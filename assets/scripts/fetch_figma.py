"""
fetch_figma.py — Lấy design từ Figma REST API về cache local `specs/design/<ten-du-an>/<thu-muc>/`.

Dùng chung cho các skill cần đọc Figma (vd: create-testcase-figma-prd-v2). Không cần Figma MCP hay gói Pro,
chỉ cần personal access token (scope File content: Read) trong biến môi trường FIGMA_TOKEN hoặc file .figma-token ở gốc dự án.

Cách dùng (chạy từ thư mục gốc dự án):
    python3 assets/scripts/fetch_figma.py "<link-figma-co-node-id>" <ten-du-an> [--dir <ten-thu-muc>] [--scale 2] [--force]

Script làm gì:
    1. Kiểm tra cache: link (file_key + node-id) đã lấy trước đó → in lại kết quả, KHÔNG gọi API (trừ khi --force).
    2. Request 1 — GET /v1/files/<key>/nodes (full depth): lấy cây layer, tìm TẤT CẢ frame (kể cả trong section/group lồng nhau),
       trích text content + điều hướng prototype của từng frame.
    3. Request 2 — GET /v1/images/<key>: render PNG cho tất cả frame trong 1 request (chia lô nếu > 100 frame).
    4. Tải PNG về ngay (URL S3 hết hạn nhanh), bỏ ảnh trùng byte-for-byte, đặt tên kebab-case theo tên frame.
    5. Ghi `figma-index.md` (danh sách frame, text, điều hướng) — file tự sinh, được ghi đè mỗi lần chạy.
       `README.md` trong cùng thư mục dành cho ghi chú viết tay sau khi xem ảnh → script KHÔNG đụng vào.

Khi hết quota (429):
    - Giới hạn theo phút (seat Dev/Full): tự chờ theo Retry-After rồi gọi lại, tối đa 2 lần.
    - Hết lượt tháng (seat View/Collab, ~20 request/tháng): dừng ngay, KHÔNG gọi thêm. Nếu request lấy cấu trúc đã
      thành công thì vẫn lưu `figma-index.md` (danh sách frame + text) và JSON gốc — lần chạy sau chỉ gọi phần render ảnh
      (1 request thay vì 2). In ra phương án dự phòng (cache cũ / export ảnh tay từ Figma / xin seat Dev).

Mã thoát: 0 = OK, 2 = thiếu token/sai link, 3 = lỗi API (403/404/...), 4 = hết quota (429).
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

API = "https://api.figma.com/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # thư mục gốc dự án
DESIGN_ROOT = PROJECT_ROOT / "specs" / "design"
SCREEN_TYPES = {"FRAME", "COMPONENT", "COMPONENT_SET"}
CONTAINER_TYPES = {"CANVAS", "SECTION", "GROUP", "DOCUMENT"}
TALL_FRAME_PX = 2500
IMAGE_BATCH = 100
SHORT_WAIT_MAX = 120   # Retry-After <= 2 phút → coi là giới hạn theo phút, tự chờ rồi gọi lại
SHORT_RETRIES = 2
NODES_SNAPSHOT = ".figma-nodes.json"  # JSON gốc của request lấy cấu trúc, để không phải gọi lại khi render ảnh bị 429
_sleep = time.sleep


class FigmaError(Exception):
    pass


class QuotaError(FigmaError):
    """429. monthly=True: hết lượt tháng (seat View/Collab) → không chờ được, phải dùng phương án dự phòng."""

    def __init__(self, retry_after, limit_type, plan_tier, monthly):
        self.retry_after, self.limit_type, self.plan_tier, self.monthly = retry_after, limit_type, plan_tier, monthly
        self.partial_dir, self.pending_frames = None, []
        super().__init__("429 — hết quota Figma API")


# ---------- tiện ích ----------

def kebab(name):
    """'Step 01 Height — Default (Cm)' → 'step-01-height-default-cm' (bỏ dấu tiếng Việt)."""
    s = (name or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "frame"


def parse_figma_url(url):
    """Trả về (file_key, node_id dạng '241:1832'). Hỗ trợ /design/, /file/, /proto/ và link branch."""
    m = re.search(r"figma\.com/(?:design|file|proto|board)/([A-Za-z0-9]+)(?:/[^/?]*)?(?:/branch/([A-Za-z0-9]+))?", url)
    if not m:
        raise ValueError("Link không phải link file Figma (cần dạng figma.com/design/<FILE_KEY>/...)")
    file_key = m.group(2) or m.group(1)
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    node = (qs.get("node-id") or qs.get("node_id") or [None])[0]
    if not node:
        raise ValueError("Link thiếu node-id — trên Figma chọn section/frame cần test → Copy link to selection")
    return file_key, node.replace("-", ":")


# ---------- gọi API ----------

def _get(url, token, counter, _attempt=0):
    counter["requests"] += 1
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            try:
                retry = int(e.headers.get("Retry-After", ""))
            except ValueError:
                retry = None
            limit_type = (e.headers.get("X-Figma-Rate-Limit-Type") or "").lower()  # low = View/Collab, high = Dev/Full
            plan_tier = e.headers.get("X-Figma-Plan-Tier") or "?"
            monthly = limit_type == "low" or retry is None or retry > SHORT_WAIT_MAX
            if not monthly and _attempt < SHORT_RETRIES:
                print(f"429 giới hạn theo phút — chờ {retry}s rồi gọi lại ({_attempt + 1}/{SHORT_RETRIES})...",
                      file=sys.stderr)
                _sleep(retry + 1)
                return _get(url, token, counter, _attempt + 1)
            raise QuotaError(retry, limit_type or "?", plan_tier, monthly)
        body = e.read().decode("utf-8", "ignore")[:300]
        if e.code == 403:
            raise FigmaError("403 — token sai/hết hạn/thiếu scope. Tạo token mới, bật File content → Read.")
        if e.code == 404:
            raise FigmaError("404 — token không có quyền xem file. Kiểm tra tài khoản Figma có mở được file trên web không.")
        raise FigmaError(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        raise FigmaError(f"Không kết nối được Figma API: {e.reason}")


def _download(url, dest):
    with urllib.request.urlopen(url, timeout=120) as r:  # URL S3 đã ký sẵn, không cần token, không tính quota
        data = r.read()
    dest.write_bytes(data)
    return data


# ---------- phân tích cây layer ----------

def collect_frames(node):
    """Lấy các 'màn' cấp cao nhất: FRAME/COMPONENT nằm trực tiếp hoặc lồng trong CANVAS/SECTION/GROUP.
    Không đi vào bên trong 1 frame (frame con bên trong là layout, không phải màn riêng)."""
    if node.get("visible") is False:
        return []
    t = node.get("type")
    if t in SCREEN_TYPES:
        return [node]
    if t in CONTAINER_TYPES:
        out = []
        for child in node.get("children", []):
            out.extend(collect_frames(child))
        return out
    return []


def extract_texts(node):
    """Text content hiển thị trong frame, theo thứ tự layer, bỏ trùng liên tiếp."""
    texts = []

    def walk(n):
        if n.get("visible") is False:
            return
        if n.get("type") == "TEXT":
            s = " ".join((n.get("characters") or "").split())
            if s and (not texts or texts[-1] != s):
                texts.append(s)
        for c in n.get("children", []):
            walk(c)

    walk(node)
    return texts


def extract_links(node):
    """Điều hướng prototype: [(tên layer bấm, id frame đích)]."""
    links = []

    def walk(n):
        dests = []
        if n.get("transitionNodeID"):
            dests.append(n["transitionNodeID"])
        for it in n.get("interactions") or []:
            for a in it.get("actions") or []:
                if a and a.get("destinationId"):
                    dests.append(a["destinationId"])
        for d in dict.fromkeys(dests):
            links.append((n.get("name", ""), d))
        for c in n.get("children", []):
            walk(c)

    walk(node)
    return links


def assign_filenames(frames):
    used, names = set(), {}
    for f in frames:
        base = kebab(f["name"])
        name, i = base, 2
        while name in used:
            name, i = f"{base}-{i}", i + 1
        used.add(name)
        names[f["id"]] = f"{name}.png"
    return names


# ---------- cache ----------

def _cache_path(project):
    return DESIGN_ROOT / project / ".figma-cache.json"


def load_cache(project):
    p = _cache_path(project)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(project, cache):
    p = _cache_path(project)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- ghi index ----------

def write_index(out_dir, url, file_key, node_id, root_name, frames, filenames, texts, links, dupes, failed, tall,
                pending=False):
    id_to_name = {f["id"]: f["name"] for f in frames}
    lines = [
        f"# Figma index — {root_name}",
        "",
        f"> Nguồn: {url}",
        f"> File `{file_key}`, node `{node_id}`. Lấy qua Figma REST API ngày {date.today()} bằng `assets/scripts/fetch_figma.py`.",
        "> File này TỰ SINH, bị ghi đè mỗi lần chạy lại. Ghi chú sau khi xem ảnh → viết vào `README.md` cùng thư mục.",
        "",
        *(["> ⏳ **CHƯA CÓ ẢNH** — request render ảnh bị 429 (hết quota). Text bên dưới là chính xác, nhưng phải có ảnh "
            "mới làm được Bước 0.6. Chạy lại script khi có quota (chỉ tốn 1 request), hoặc export ảnh tay vào thư mục này.", ""]
          if pending else []),
        f"## Danh sách frame ({len(frames)})",
        "",
        "| # | File | Node ID | Tên frame gốc | Kích thước |",
        "| - | ---- | ------- | ------------- | ---------- |",
    ]
    for i, f in enumerate(frames, 1):
        box = f.get("absoluteBoundingBox") or {}
        size = f"{round(box.get('width', 0))}×{round(box.get('height', 0))}" if box else "?"
        fid = f["id"]
        if pending:
            file_cell = f"⏳ chưa có ảnh (hết quota) — tên gợi ý `{filenames[fid]}`"
        elif fid in failed:
            file_cell = "⚠️ render lỗi"
        elif fid in dupes:
            file_cell = f"(trùng ảnh `{dupes[fid]}`)"
        else:
            file_cell = f"`{filenames[fid]}`"
        lines.append(f"| {i} | {file_cell} | {fid} | {f['name']} | {size} |")

    if tall:
        lines += ["", f"⚠️ Frame cao > {TALL_FRAME_PX}px (chữ nhỏ dễ bị nén, đọc sai): "
                  + ", ".join(f"`{filenames[i]}`" for i in tall)
                  + " — chạy lại với `--scale 3 --force` hoặc nhờ designer cắt frame ngắn lại."]

    lines += ["", "## Text content theo frame", "",
              "Trích từ layer TEXT đang hiển thị — chỉ để đối chiếu copy/label, KHÔNG thay cho việc xem ảnh."]
    for f in frames:
        lines += ["", f"### {f['name']} (`{f['id']}`)", ""]
        lines += [f"- {t}" for t in texts[f["id"]]] or ["- (không có text)"]

    nav = [(f, src, dst) for f in frames for src, dst in links[f["id"]]]
    if nav:
        lines += ["", "## Điều hướng prototype", "", "| Từ frame | Layer bấm | Tới frame |", "| --- | --- | --- |"]
        for f, src, dst in nav:
            lines.append(f"| {f['name']} | {src} | {id_to_name.get(dst, f'`{dst}` (ngoài phạm vi link)')} |")

    (out_dir / "figma-index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- luồng chính ----------

def fetch(url, project, token, subdir=None, scale=2, force=False):
    file_key, node_id = parse_figma_url(url)
    cache_key = f"{file_key}:{node_id}"
    cache = load_cache(project)

    counter = {"requests": 0}
    data = None
    if not force and cache_key in cache:
        entry = cache[cache_key]
        out_dir = DESIGN_ROOT / project / entry["dir"]
        if entry.get("status") == "partial" and (out_dir / NODES_SNAPSHOT).exists():
            # lần trước đã lấy được cấu trúc nhưng render ảnh bị 429 → dùng lại JSON, chỉ gọi phần render
            data = json.loads((out_dir / NODES_SNAPSHOT).read_text(encoding="utf-8"))
        elif (out_dir / "figma-index.md").exists():
            return {**entry, "cached": True, "dir": out_dir, "requests": 0}

    if data is None:
        data = _get(f"{API}/files/{file_key}/nodes?ids={urllib.parse.quote(node_id)}", token, counter)
    node_entry = (data.get("nodes") or {}).get(node_id)
    if not node_entry or not node_entry.get("document"):
        raise FigmaError(f"Không tìm thấy node {node_id} trong file {file_key} (node đã bị xoá hoặc link sai).")
    root = node_entry["document"]
    frames = collect_frames(root)
    if not frames:
        raise FigmaError(f"Node `{root.get('name')}` (type {root.get('type')}) không chứa frame nào để render.")

    out_dir = DESIGN_ROOT / project / (subdir or kebab(root.get("name")))
    out_dir.resolve().relative_to(PROJECT_ROOT)  # chặn ghi ra ngoài thư mục dự án
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / NODES_SNAPSHOT).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    filenames = assign_filenames(frames)
    texts = {f["id"]: extract_texts(f) for f in frames}
    links = {f["id"]: extract_links(f) for f in frames}
    tall = [f["id"] for f in frames if (f.get("absoluteBoundingBox") or {}).get("height", 0) > TALL_FRAME_PX]

    ids = [f["id"] for f in frames]
    image_urls = {}
    try:
        for i in range(0, len(ids), IMAGE_BATCH):
            batch = ",".join(ids[i:i + IMAGE_BATCH])
            res = _get(f"{API}/images/{file_key}?ids={urllib.parse.quote(batch)}&format=png&scale={scale}",
                       token, counter)
            if res.get("err"):
                raise FigmaError(f"Render ảnh lỗi: {res['err']}")
            image_urls.update(res.get("images") or {})
    except QuotaError as e:
        # request lấy cấu trúc đã tốn quota → giữ lại kết quả, lần sau chỉ gọi render
        write_index(out_dir, url, file_key, node_id, root.get("name", ""), frames, filenames, texts, links,
                    {}, [], [], pending=True)
        cache[cache_key] = {"dir": out_dir.name, "root_name": root.get("name", ""), "fetched": str(date.today()),
                            "frames": len(frames), "pngs": [], "status": "partial"}
        save_cache(project, cache)
        e.partial_dir = out_dir
        e.pending_frames = [(f["name"], filenames[f["id"]]) for f in frames]
        raise

    seen_hash, dupes, failed, saved = {}, {}, [], []
    for fid in ids:
        img_url = image_urls.get(fid)
        if not img_url:
            failed.append(fid)
            continue
        dest = out_dir / filenames[fid]
        digest = hashlib.sha256(_download(img_url, dest)).hexdigest()
        if digest in seen_hash:
            dest.unlink()
            dupes[fid] = seen_hash[digest]
        else:
            seen_hash[digest] = filenames[fid]
            saved.append(filenames[fid])

    write_index(out_dir, url, file_key, node_id, root.get("name", ""), frames, filenames, texts, links,
                dupes, failed, [t for t in tall if t not in failed and t not in dupes])

    entry = {"dir": out_dir.name, "root_name": root.get("name", ""), "fetched": str(date.today()),
             "frames": len(frames), "pngs": saved, "status": "complete"}
    cache[cache_key] = entry
    save_cache(project, cache)
    return {**entry, "cached": False, "dir": out_dir, "requests": counter["requests"],
            "dupes": len(dupes), "failed": len(failed), "tall": len(tall)}


def print_quota_help(e, project):
    err = lambda m="": print(m, file=sys.stderr)
    seat = {"low": "View/Collab", "high": "Dev/Full"}.get(e.limit_type, "không rõ")
    if e.monthly:
        when = ""
        if e.retry_after:
            until = datetime.now() + timedelta(seconds=e.retry_after)
            when = f" Có lượt lại sau ~{e.retry_after / 86400:.1f} ngày (khoảng {until:%d/%m/%Y %H:%M})."
        err(f"HẾT LƯỢT FIGMA API THEO THÁNG — seat {seat}, gói workspace chứa file: {e.plan_tier}.{when}")
        err("Đã DỪNG, không gọi thêm request nào (gọi lại liên tục không giúp gì, chỉ kéo dài thời gian chờ).")
    else:
        err(f"429 GIỚI HẠN THEO PHÚT — seat {seat}, gói {e.plan_tier}. Đã tự chờ & thử lại {SHORT_RETRIES} lần không được.")
        err(f"Chờ {e.retry_after or 60}s rồi chạy lại đúng lệnh này.")
        return

    if e.partial_dir:
        rel = e.partial_dir.relative_to(PROJECT_ROOT)
        err(f"\nĐã lưu được cấu trúc + text: {rel}/figma-index.md (chưa có ảnh).")
        err("Chạy lại lệnh này khi có lượt → chỉ tốn 1 request (render ảnh), không lấy lại cấu trúc.")

    err("\nPhương án dự phòng:")
    old = sorted(p.name for p in (DESIGN_ROOT / project).iterdir() if p.is_dir()) if (DESIGN_ROOT / project).is_dir() else []
    err("  1. Dùng cache cũ trong specs/design/" + project + "/: " + (", ".join(old) if old else "(chưa có)")
        + " — chỉ hợp lệ nếu design màn đó chưa đổi.")
    target = f"specs/design/{project}/{e.partial_dir.name}/" if e.partial_dir else f"specs/design/{project}/<ten-section>/"
    err(f"  2. Export ảnh TAY từ Figma (không tốn lượt API): chọn các frame → panel Export → PNG 2x → Export → "
        f"bỏ file vào {target}")
    if e.pending_frames:
        err("     Danh sách frame cần export (tên file gợi ý):")
        for name, fn in e.pending_frames:
            err(f"       - {name}  →  {fn}")
    err("  3. Xin seat Dev hoặc Full trong workspace chứa file (giới hạn chuyển sang theo phút, không lo hết tháng), "
        "hoặc nhờ designer chuyển/duplicate file sang workspace trả phí mà bạn có seat Dev/Full.")
    err("  4. Chờ tới khi có lượt lại.")


def load_token():
    """FIGMA_TOKEN từ biến môi trường; không có thì đọc file .figma-token ở gốc dự án
    (dòng không bắt đầu bằng '#'; dòng '# expires: YYYY-MM-DD' dùng để cảnh báo hết hạn)."""
    token = os.environ.get("FIGMA_TOKEN", "").strip()
    if token:
        return token
    f = PROJECT_ROOT / ".figma-token"
    if not f.is_file():
        return ""
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        m = re.match(r"#\s*expires:\s*(\d{4}-\d{2}-\d{2})", line)
        if m and date.fromisoformat(m.group(1)) < date.today():
            print(f"⚠️  Token trong .figma-token đã hết hạn từ {m.group(1)} — tạo token mới và cập nhật file.",
                  file=sys.stderr)
        elif line and not line.startswith("#"):
            token = line
    return token


def main():
    ap = argparse.ArgumentParser(description="Lấy design Figma về specs/design/<ten-du-an>/ (cache local).")
    ap.add_argument("url", help="Link Figma có node-id (Copy link to selection)")
    ap.add_argument("project", help="<ten-du-an> kebab-case, trùng tên thư mục dự án")
    ap.add_argument("--dir", help="Tên thư mục con (mặc định: kebab-case tên section/frame gốc)")
    ap.add_argument("--scale", type=float, default=2, help="Tỉ lệ render PNG (mặc định 2; frame cao dùng 3)")
    ap.add_argument("--force", action="store_true", help="Bỏ qua cache, gọi lại API (tốn quota)")
    args = ap.parse_args()

    # dự án đã có thư mục (vd GLP-1) thì giữ đúng tên cũ; dự án mới bắt buộc kebab-case
    if args.project != kebab(args.project) and not (DESIGN_ROOT / args.project).is_dir():
        print(f"<ten-du-an> phải là kebab-case, vd: {kebab(args.project)}", file=sys.stderr)
        sys.exit(2)
    if "/" in args.project or args.project.startswith("."):
        print("<ten-du-an> không được chứa '/' hoặc bắt đầu bằng '.'", file=sys.stderr)
        sys.exit(2)
    token = load_token()
    if not token:
        print("THIẾU FIGMA_TOKEN. Figma → avatar → Settings → Security → Personal access tokens → Generate new token "
              "(scope File content: Read), rồi lưu vào file .figma-token ở gốc dự án (1 dòng token, tuỳ chọn thêm dòng "
              "'# expires: YYYY-MM-DD'), hoặc đặt biến môi trường FIGMA_TOKEN.",
              file=sys.stderr)
        sys.exit(2)

    try:
        r = fetch(args.url, args.project, token, subdir=args.dir, scale=args.scale, force=args.force)
    except ValueError as e:
        print(f"Link không hợp lệ: {e}", file=sys.stderr)
        sys.exit(2)
    except QuotaError as e:
        print_quota_help(e, args.project)
        sys.exit(4)
    except FigmaError as e:
        print(f"Lỗi Figma API: {e}", file=sys.stderr)
        sys.exit(3)

    rel = r["dir"].relative_to(PROJECT_ROOT)
    if r["cached"]:
        print(f"Dùng CACHE (lấy ngày {r['fetched']}, 0 request API). Thêm --force nếu design đã đổi.")
    else:
        print(f"Đã gọi {r['requests']} request API. {r['frames']} frame → {len(r['pngs'])} ảnh "
              f"(bỏ {r['dupes']} ảnh trùng, {r['failed']} render lỗi, {r['tall']} frame quá cao).")
    print(f"Thư mục: {rel}/")
    print(f"Index:   {rel}/figma-index.md")
    print("Ảnh cần mở bằng Read (từng ảnh một):")
    for p in r["pngs"]:
        print(f"  {rel}/{p}")


if __name__ == "__main__":
    main()
