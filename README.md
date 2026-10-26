# manual-testcase-skill

Skill Claude Code sinh **test case chức năng (XLSX) kèm RTM** cho 1 feature app mobile từ PRD + design Figma.

- Steps ngắn gọn, mỗi step có 1 dòng Expected cùng số — dễ chuyển sang automation.
- Pre-condition nối chuỗi (`Tiếp tục từ TC_xxx`) để giảm reinstall khi chạy.
- Mỗi màn có case "Hiển thị UI" (bố cục, copy, màu, font theo design).
- Script tự kiểm RTM, Pre-condition, khớp Steps / Expected, tham chiếu Q&A.

## Cài đặt

1. Mở thư mục này bằng Claude Code (lần đầu chấp nhận MCP server `playwright` và `begamob` trong `.mcp.json`).
2. Python 3 + `pip install openpyxl`.
3. Figma: tạo personal access token (scope *File content: Read*), lưu 1 dòng vào file `.figma-token` ở gốc thư mục (đã git ignore).

## Dùng

Trong Claude Code:

```
viết test case cho <feature> dự án <ten-du-an>, PRD <link begamob>, Figma <link>
```

Kết quả:

| Thư mục | Nội dung |
| --- | --- |
| `testcase/<ten-du-an>/` | File XLSX: sheet test case + sheet RTM |
| `specs/q&a/<ten-du-an>/` | File Q&A (mâu thuẫn PRD / design, quyết định đã chốt) |
| `specs/design/<ten-du-an>/` | Cache ảnh + dữ liệu Figma |

Các thư mục trên là tài liệu riêng của từng dự án, đã nằm trong `.gitignore`.

Kiểm lại file bất kỳ lúc nào:

```bash
python3 .claude/skills/create-testcase-figma-prd-v2/assets/scripts/check_rtm.py testcase/<ten-du-an>/<file>.xlsx "specs/q&a/<ten-du-an>/<ten-spec>-qna.md"
```
