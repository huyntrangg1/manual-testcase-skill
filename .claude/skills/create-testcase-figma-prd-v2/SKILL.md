---
name: create-testcase-figma-prd-v2
description: Tạo test case XLSX kèm RTM cho 1 feature mobile từ PRD/spec và Figma nếu có — coverage đủ theo requirement/risk với số case tối thiểu hợp lý, không trùng lặp, Pre-condition tối ưu cho chạy liên tục / automation, tự kiểm coverage trước khi giao. Dùng khi user yêu cầu viết / tạo / sinh test case cho 1 feature hoặc 1 spec.
---

# Mục tiêu

Senior QA tạo **bộ test case nhỏ nhất nhưng đủ chứng minh mọi requirement, branch, risk và outcome quan trọng**.

Nguyên tắc cốt lõi:

1. Đọc đủ nguồn; không bỏ requirement để giảm token.
2. **Requirement phải được trace, nhưng không bắt buộc mỗi requirement 1 case riêng.**
3. 1 case được cover nhiều rule nếu cùng hành vi và Expected chứng minh được tất cả.
4. 1 rule được có nhiều case khi điều kiện / kết quả khác nhau.
5. P/N/E là **chiều coverage, không phải quota** — không tạo case chỉ để lấp ô.
6. Case độc lập về mục tiêu, nhưng tối ưu setup để chạy liên tục.
7. Chỉ hỏi user điểm làm đổi tập case hoặc Expected.
8. Script kiểm cấu trúc / RTM / Pre-condition; LLM tập trung vào requirement, risk, coverage và tính đúng của case.

Thứ tự ưu tiên:

**Coverage đúng > Expected đúng > Traceability > Automation readiness > Số case thấp**

Output:
- XLSX theo template `assets/templates/testcase-template-v2.csv`.
- Mỗi sheet test case kèm 1 sheet RTM.
- Không ghi đè file test case đã có kết quả chạy.

---

# 1. Nguồn và phạm vi

- Chỉ đọc/ghi trong đúng thư mục `<ten-du-an>`:
  - `specs/design|q&a/<ten-du-an>/`
  - `testcase/<ten-du-an>/`
- Tên dự án khác trong ví dụ chỉ là ví dụ.
- Đọc spec **nguyên văn**, không qua tóm tắt.
- PRD begamob: đọc qua MCP `project_doc_get_by_url` (markdown); tài liệu dài thì theo `section` / `offset` tới hết.
- Không lưu spec về local; ghi version + ngày cập nhật vào `Link SRS`.
- Ảnh nhúng cần xem → tải tạm vào scratchpad.
- Spec `.md` có ảnh base64 lớn → lọc dòng `[imageN]: <data:image…>` để đọc chữ, trích ảnh ra xem.
- Không đặt giả định trái câu `Đã chốt` trong Q&A.
- Tiếng Việt, trừ nhãn cố định của template.
- Platform:
  - App 2 nền tảng → `Both`, bước khác nhau ghi `Android: … / iOS: …`; chỉ tách case khi hành vi khác thật.
  - App 1 nền tảng → ghi đúng nền tảng theo PRD.

## Quy tắc tiết kiệm token

Đọc nguồn **1 lần**, ghi lại đủ:
- Requirement / rule.
- Flow / entry point.
- State / condition.
- Data / boundary.
- Nguồn.
- Risk.
- Điểm chưa rõ.

Các bước sau dùng lại; chỉ quay lại nguồn khi cần xác minh chi tiết.

---

# 2. Design / Figma

Nếu có Figma:

`python3 assets/scripts/fetch_figma.py "<link>" <ten-du-an>`

- Tự dùng cache; `--force` khi design đã đổi.
- Lỗi token / 403 / 404 → chuyển nguyên văn hướng dẫn script cho user.
- Hết quota mã 4 → không chạy lại trong phiên; làm theo phương án dự phòng script in ra (cache cũ / nhờ user export ảnh tay vào thư mục cache).
- Vẫn không lấy được → dừng phần design, báo user, tiếp tục theo PRD.
- Không dùng Figma MCP.
- **Mở từng ảnh bằng Read, không bỏ ảnh** (ràng buộc CLAUDE.md).
- `figma-index.md` dùng để đối chiếu copy và prototype.
- Không suy ra UI từ tên layer.

Nếu không có design:
- Ghi rõ `chưa đối chiếu design` trong báo cáo.

---

# 3. Requirement Map trước khi viết case

Bảng phẳng trong scratchpad:

`ID | Cấp | Thuộc | Requirement/Rule | Condition/State | Expected | Nguồn | Risk`

## 3.1. Cấp requirement

- **Feature**: nhóm chức năng lớn / mỗi file spec (nhiều file → mỗi file 1 sheet + 1 RTM).
- **Flow**: đường đi nghiệp vụ độc lập — Happy Case, mỗi entry point, nhánh rẽ trong Edge Case / AC, nút điều hướng prototype, chuyển trạng thái (Free/Pro, bộ đếm, reset ngày…).
- **Rule**: hành vi / điều kiện / validation / state / data cụ thể.
- **Design rule**: chỉ có trên design → nguồn `Design (Figma)`.

## 3.2. Atomic nhưng không over-split

Tách rule đủ để biết coverage, nhưng **không tách 1 hành vi liên tục thành nhiều rule chỉ vì PRD viết nhiều câu**.

## 3.3. Design ↔ PRD

- 2 nguồn khác nhau → Q&A, không tự chọn.
- Không tính text tĩnh / icon trang trí.

## 3.4. Decision table

Dùng khi:
- Kết quả phụ thuộc ≥ 2 điều kiện.
- Các tổ hợp cho Expected khác nhau.

Tổ hợp cùng kết quả, không có risk riêng → gộp.

---

# 4. Coverage model — ít case nhưng đủ

Phân loại từng rule trước khi viết:

### A. Đã cover
Case khác đã cover đầy đủ → không tạo case mới, chỉ trace.

### B. Gộp được
- Cùng flow hoặc cùng state.
- Cùng mục tiêu kiểm thử.
- Expected của các rule xác minh được trong 1 lần chạy.

→ Ưu tiên gộp.

### C. Case riêng
Khi có ít nhất 1 lý do:
- Expected khác.
- Branch / điều kiện khác.
- Risk khác đáng kể.
- Cần state / data riêng.
- Lỗi rule này không suy ra được từ case kia.
- Gộp làm Steps / Expected quá phức tạp hoặc khó automation.

### D. Không áp dụng
`N/A — <lý do>` trong RTM, không tạo case.

## 4.1. Chọn data

Ưu tiên:
1. Giá trị hợp lệ đại diện.
2. Mỗi loại lỗi validation 1 giá trị.
3. Biên dưới / biên trên.
4. Ngay dưới / ngay trên biên khi behavior khác.
5. Rỗng / null khi hệ thống phân biệt.
6. Chuyển trạng thái quan trọng.

Nhiều data cùng Expected, cùng risk → 1 case đại diện. Tách khi biên làm đổi Expected.

## 4.2. Negative / Edge suy diễn

Inventory phần tử tương tác từng màn, đi qua `references/checklist-negative-edge.md` (lọc lớp 3 theo PRD / Q&A đã chốt).

Checklist là **nguồn phát hiện rủi ro**, không phải danh sách bắt buộc. Mỗi gợi ý chỉ thành case khi đạt cả 3:

1. PRD / Q&A / design cho phép tình huống xảy ra.
2. Có hành vi / risk cần xác minh.
3. Chưa case nào cover đúng mục tiêu.

- Gợi ý trùng nhau trong cùng flow → gộp.
- Áp dụng → Rule nguồn `Checklist: <nhóm> / <mục>`.

---

# 5. Q&A

File:

`specs/q&a/<ten-du-an>/<ten-spec>-qna.md` (nhiều spec cùng feature → 1 file theo tên feature)

Cột:

`STT | Feature/Màn | Câu hỏi | Mức độ (High/Medium/Low) | Giả định tạm | Trạng thái`

Chỉ ghi:
- Mâu thuẫn trong PRD / giữa các PRD.
- Mâu thuẫn PRD ↔ design.
- Lỗ hổng PRD làm Expected có thể khác nhau.
- Quyết định đã chốt.

Không ghi:
- Thiếu design.
- Môi trường test.
- Typo không ảnh hưởng behavior.

Đọc Q&A cũ trước:
- Câu `Đã chốt` theo đúng, không hỏi lại.
- Giữ số cũ, chỉ cập nhật trạng thái + thêm câu mới cuối file.

**Chỉ hỏi user khi câu trả lời đổi:** flow · Expected · platform · data/state · scope · số / loại case — gồm cả đặc điểm app PRD không nói (nền tảng, tài khoản, gói, thiết bị đi kèm) và Project Name / Written By khi chưa có file test case cũ.

- Tối đa 1 lượt, AskUserQuestion ≤ 4 câu, phương án đề xuất đặt đầu.
- Ghi kết quả thành câu Q&A: `Đã chốt (user, <ngày>): …`.
- **Không hỏi được user** → giả định tạm, ghi Q&A, nêu trong báo cáo.
- Case theo câu chốt / giả định ghi `(Q&A #n)` trong Expected.
- Câu chưa trả lời và không đặt được giả định hợp lý → **vẫn viết case** (Pre-condition, Steps đầy đủ), bước phụ thuộc câu đó ghi Expected `Chờ confirm (Q&A #n)`. Cột Giả định tạm trong Q&A ghi `Case TC_xxx — Expected chờ confirm`, không ghi "chưa viết case".

---

# 6. Viết case

## 6.1. E2E

Mỗi **business flow độc lập** ≥ 1 case, module `Luồng E2E`. Kiểm:
- Entry point.
- Các màn chính.
- Data truyền giữa màn.
- Chuyển trạng thái quan trọng.
- Kết quả cuối.

Không tạo E2E riêng cho từng rule. E2E của nhánh lỗi → Test Type `Negative`.

## 6.2. Focused case

Dùng cho: validation · biên · quyền / trạng thái · xử lý lỗi · tính toán · UI có requirement · chuyển tiếp đặc biệt.

## 6.3. UI

- **Mỗi màn / modal / dialog trong design có 1 case `Hiển thị UI màn <tên>`** (module = màn đó, Test Type `Positive`, Priority `Low`; màn trên luồng chính → `Medium`), kiểm bố cục ở trạng thái mặc định. Để riêng, không gộp vào case luồng — lỗi UI không chặn luồng.
- **UI của từng trạng thái** (trống, có data, bị khoá, lỗi, đang chạy…) kiểm ngay trong Expected của case tạo ra điều kiện đó, không tách case riêng.
- Expected UI theo design, ghi đủ: phần tử + vị trí (góc trên-trái, dưới-phải…) · icon, ảnh minh hoạ, mascot + chuyển động · copy nguyên văn đầy đủ (không "…") · nút + trạng thái nút. Copy design khác PRD → theo Q&A.
- **Màu và font**: case UI kiểm thêm font (họ, độ đậm, cỡ) + mã màu của phần tử chính — title, số liệu lớn, nút (nền + chữ), tab / dòng picker đang chọn, nền card / khung, màu ring / chart / icon trạng thái. Không ghi khoảng cách, padding, kích thước, bo góc.
- Chưa có design chính xác (chỉ có ảnh, chưa vẽ) → bố cục theo ảnh nhúng trong PRD, **không đoán mã màu / font từ ảnh**; ghi nguồn trong RTM, nêu trong báo cáo phần màu / font chờ design.
- RTM: mỗi màn 1 dòng Rule `UI: <màn>`, Nguồn = tên frame design / mục PRD; ô Positive = case UI, Negative/Edge `N/A — UI tĩnh` trừ khi có trạng thái lỗi.

## 6.4. Chống trùng

Trước khi thêm case, so: mục tiêu · điều kiện · thao tác · Expected · loại data · state.

Chỉ khác câu chữ, không thêm coverage → gộp.

## 6.5. Cột test case

| Cột | Quy tắc |
| --- | --- |
| Test Case # | `TC_<PREFIX>_<STT>`: mỗi sheet 1 prefix viết tắt feature (vd `TC_LOGIN`), STT liên tục toàn sheet theo **thứ tự chạy** |
| Module/Group test | Theo màn / khối chức năng + `Luồng E2E` |
| Test Type | `Positive` / `Negative` / `Edge`, đúng ô RTM case cover |
| Test Scenario | *Động từ + đối tượng + điều kiện*; không trùng trong module; cấm tên chung chung. Case cùng mục tiêu chỉ khác data dùng chung 1 Scenario, xếp liền nhau |
| Test Cases Description | `Verify [đối tượng] [hành vi] khi [điều kiện / data]`; mã AC trong ngoặc cuối câu |
| Pre-condition | Theo mục 7 |
| Steps | Đánh số, ngắn gọn: thao tác nối bằng `→` (vd `Card "Balance" → "2 min" → [Start on Watch]`), không giải thích lý do; gọi phần tử đúng chữ/nhãn UI; thao tác trên thiết bị khác ghi tiền tố `Watch:` / `iPhone:` |
| Expected Result | **Mỗi step đúng 1 dòng, cùng số với step** (step chỉ thao tác vẫn ghi kết quả thấy được, vd "Modal đóng", "Let's Begin mở"); quan sát và đo được (copy, số liệu, trạng thái nút, màn chuyển tới) |
| Priority | Theo risk — High: luồng chính / blocker · Medium: rule phụ, validation · Low: UI tĩnh, hiếm gặp |

Trạng thái mất thời gian (chờ giờ, sang ngày) → dựng nhanh bằng chức năng app / chỉnh giờ máy.

---

# 7. Pre-condition — giảm setup khi chạy / automation

Chỉ 3 dạng:

### Dựng mới
`1. Reset nếu cần … 2. Data … 3. Màn bắt đầu …`

### Tiếp tục
`Tiếp tục từ TC_xxx: <màn, data hiện tại>. Trước khi chạy: <thao tác>.`

Chỉ dùng khi case ngay trước để lại state ổn định; không reset.

### Navigate
`Navigate tới màn <tên> với data: <giá trị>.`

Dùng cho focused case độc lập; chỉ ghi màn đích + data.

## Quy tắc reset và reuse

- `Reinstall app` khi cần hành vi "lần đầu" / data trống.
- `Delete account` chỉ khi app có tài khoản (theo PRD / Q&A; chưa rõ → hỏi).
- Tạo được bằng thao tác trong app → không reset.
- Gom case theo state: chỉ xem → đổi data → phá trạng thái cuối nhóm.
- Không reuse nếu case trước đổi data mà case sau cần baseline khác.
- Cấm câu mơ hồ ("trạng thái mặc định", "đã có data", "như case trước").

---

# 8. RTM

`ID | Cấp | Thuộc | Nội dung | Nguồn | Flow / E2E | Positive | Negative | Edge | Ghi chú`

- Mọi requirement có trạng thái coverage.
- 1 case được xuất hiện ở nhiều dòng RTM.
- Ô không áp dụng → `N/A — <lý do cụ thể>`.
- Ô Positive chỉ N/A khi rule **không có hành vi positive** hoặc dòng `Checklist:`. Ô N/A phải chứa nguyên cụm `không có hành vi positive` (check_rtm.py dò đúng cụm này), vd `N/A — không có hành vi positive: rule chỉ quy định chặn thao tác`.
- Không tạo case chỉ để tránh N/A.
- Không orphan case, không orphan requirement.
- N/A lớp 3 checklist ghi ở cột Ghi chú dòng Feature.

---

# 9. Build và kiểm tự động

## 9.1. Build

```python
import sys; sys.path.insert(0, ".claude/skills/create-testcase-figma-prd-v2/assets/scripts")
from build_testcase import build_testcase_xlsx

# testcases: (Test Case #, Module, Test Type, Platform, Scenario, Description, Pre-condition, Steps, Expected, Priority)
# nhiều spec → sheets=[{"sheet_name", "function_name", "srs_link", "testcases", "rtm"}, ...]
build_testcase_xlsx(
    project_name=..., function_name=..., written_by=..., written_date=...,
    reviewed_by="", reviewed_date="", execute_by="", execute_date="",
    srs_link=..., testcases=..., rtm=...,
    output_path="testcase/<ten-du-an>/<file>.xlsx",
)
```

- Không dựng file bằng tay.
- Project Name / Written By lấy từ file test case cũ cùng dự án (chưa có → hỏi ở mục 5).
- Script tự gộp ô Scenario liền nhau cùng tên và ẩn cột Platform khi mọi case cùng 1 nền tảng.
- Script tự đánh lại số case liên tục theo thứ tự truyền vào và đổi theo mọi chỗ nhắc mã (RTM, `Tiếp tục từ`) → xoá / chèn case không cần sửa số tay.

## 9.2. Kiểm

```bash
python3 .claude/skills/create-testcase-figma-prd-v2/assets/scripts/check_rtm.py testcase/<ten-du-an>/<file>.xlsx "specs/q&a/<ten-du-an>/<ten-spec>-qna.md"
```

Phải đạt `✅ 0 lỗi`. Script kiểm:
- RTM 3 cấp.
- Test Type khớp ô.
- Orphan case.
- Pre-condition.
- Expected trống; số dòng Expected khớp số step.
- `(Q&A #n)` có thật trong file Q&A; Expected `Chờ confirm` mà câu đó đã chốt → viết lại Expected.

**Không kiểm lại bằng tay những gì script đã kiểm.**

---

# 10. Review độc lập — chỉ khi cần

Chạy 1 subagent khi feature có một trong:
- Nhiều branch / state.
- Decision table phức tạp.
- Tính toán / business rule quan trọng.
- Nhiều nguồn PRD / design.
- Risk High.
- Feature lớn, dễ sót flow.

Feature đơn giản → RTM + `check_rtm.py` là đủ.

## Cách chạy

- Đưa subagent: nguồn spec, thư mục design, checklist, file Q&A.
- **Không đưa RTM / case** cho tới khi subagent tự liệt kê xong luồng + tình huống; sau đó mới cho đối chiếu file XLSX.

## Phạm vi review

Chỉ tìm:
1. Thiếu flow / branch có căn cứ.
2. Requirement chưa cover.
3. Negative / Edge có risk chưa cover.
4. E2E không đi đủ flow.
5. Expected không chứng minh được requirement.
6. Tính toán / data sai.

Không review: format, cú pháp Pre-condition, biến thể không tăng coverage.

## Output

Tối đa 20 gap: `Gap | Nguồn | Risk | Case liên quan | Hành động`

- Chỉ thêm case khi gap có căn cứ → build lại + `check_rtm.py`.
- Không chạy lại reviewer trừ khi sửa ảnh hưởng nhiều flow.

---

# 11. Coverage gate trước khi giao

1. Requirement nào chưa trace?
2. Flow / entry point nào chưa cover?
3. Branch làm Expected khác chưa test?
4. Biên / state quan trọng chưa test?
5. Màn / modal nào trong design chưa có case UI; trạng thái nào có UI riêng mà Expected chưa tả?
6. Case nào trùng mục tiêu?
7. Case nào chỉ để lấp P/N/E?
8. Setup / Reinstall / Delete account nào bỏ được mà không giảm tính độc lập?

- Câu 1–5 còn gap → bổ sung.
- Câu 6–8 có vấn đề → gộp / tối ưu.

---

# 12. Giao file

Tóm tắt ngắn:
- `check_rtm.py`: 0 lỗi.
- Tổng case; theo Module / Test Type / Priority.
- Số Reinstall / Delete account.
- Q&A mới (nêu câu High).
- Giả định quan trọng.
- Ngoài phạm vi.
- Nếu có review: gap thật, case đã sửa / thêm.

Không giải thích dài quá trình suy luận.

> **Minimal sufficient test set**: bộ test case nhỏ nhất nhưng vẫn chứng minh được các requirement, branch, risk và outcome quan trọng.
