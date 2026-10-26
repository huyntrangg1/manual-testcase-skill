# testcase-skills

Bộ skill Claude Code cho test case app mobile:

| Skill | Việc |
| --- | --- |
| `create-testcase-figma-prd-v2` | Sinh **test case manual (XLSX) kèm RTM** cho 1 feature từ PRD + design Figma |
| `select-automation-testcases` | Chọn case từ file manual đó, chuyển thành **test case automation** (format v2, mỗi sheet → 1 file `<sheet>-automation.xlsx`) |

## create-testcase-figma-prd-v2

- Steps ngắn gọn, mỗi step có 1 dòng Expected cùng số — dễ chuyển sang automation.
- Pre-condition nối chuỗi (`Tiếp tục từ TC_xxx`) để giảm reinstall khi chạy.
- Mỗi màn có case "Hiển thị UI" (bố cục, copy, màu, font theo design).
- Script tự kiểm RTM, Pre-condition, khớp Steps / Expected, tham chiếu Q&A.

### Cài đặt

1. Mở thư mục này bằng Claude Code (lần đầu chấp nhận MCP server `playwright` và `begamob` trong `.mcp.json`).
2. Python 3 + `pip install openpyxl`.
3. Figma: tạo personal access token (scope *File content: Read*), lưu 1 dòng vào file `.figma-token` ở gốc thư mục (đã git ignore).

### Dùng

Trong Claude Code:

```
viết test case cho <feature> dự án <ten-du-an>, PRD <link begamob>, Figma <link>
```

Kết quả:

| Thư mục | Nội dung |
| --- | --- |
| `manual-tc/<ten-du-an>/` | File XLSX: sheet test case + sheet RTM |
| `automation-tc/<ten-du-an>/` | File `<sheet>-automation.xlsx` (TestCases + TestData) do `select-automation-testcases` sinh |
| `specs/q&a/<ten-du-an>/` | File Q&A (mâu thuẫn PRD / design, quyết định đã chốt) |
| `specs/design/<ten-du-an>/` | Cache ảnh + dữ liệu Figma |

Các thư mục trên là tài liệu riêng của từng dự án, đã nằm trong `.gitignore`.

Kiểm lại file bất kỳ lúc nào:

```bash
python3 .claude/skills/create-testcase-figma-prd-v2/assets/scripts/check_rtm.py manual-tc/<ten-du-an>/<file>.xlsx "specs/q&a/<ten-du-an>/<ten-spec>-qna.md"
```

## select-automation-testcases

### Cài đặt

Node 18+. Lần đầu: `npm install --prefix .claude/skills/select-automation-testcases` (cài `exceljs`; Claude tự chạy nếu thiếu).

### Dùng

```
chọn test case automation từ manual-tc/<ten-du-an>/<file>.xlsx, ghi ra automation-tc/<ten-du-an>/
```

Claude đọc từng case, để riêng case phải test tay (kèm lý do), xếp TC chạy nối tiếp để ít cài lại app, rồi ghi file automation và dừng để bạn review.
