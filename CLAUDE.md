# Về dự án

Sinh test case chức năng (integration / system test) có RTM truy vết cho app mobile (iOS + Android) từ PRD/spec + design Figma — skill `create-testcase-figma-prd-v2`. Điểm mờ / lệch giữa PRD và design ghi vào file Q&A.

Dùng cho nhiều dự án con song song — mỗi loại tài liệu có thư mục con theo tên dự án `<ten-du-an>/`.

# Cấu trúc thư mục

```
<thu-muc-du-an>/
├── CLAUDE.md
├── .mcp.json                  # Playwright + begamob (đọc PRD)
├── .figma-token               # Figma personal access token — tự tạo, KHÔNG commit
├── .claude/skills/            # create-testcase-figma-prd-v2
├── assets/
│   ├── scripts/fetch_figma.py
│   └── templates/testcase-template-v2.csv
├── specs/                     # (git ignore) design/<ten-du-an>/ cache Figma · q&a/<ten-du-an>/ file Q&A
└── testcase/<ten-du-an>/      # (git ignore) test case XLSX (sheet test case + sheet RTM)
```

Quy ước:

- `<ten-du-an>` kebab-case, dùng THỐNG NHẤT 1 tên trên mọi thư mục của cùng 1 dự án. Tên file kebab-case.
- Test case: XLSX theo `assets/templates/testcase-template-v2.csv`, sinh bằng script của skill — không dựng file bằng tay.
- PRD/spec trên begamob đọc trực tiếp qua MCP (`project_doc_get_by_url`, markdown), không lưu về local; doc dài đọc lần lượt theo `section` / `offset` tới hết. Ghi version + ngày cập nhật của doc vào header test case (`Link SRS`) và file Q&A.
- Design Figma lấy qua `assets/scripts/fetch_figma.py`, cache trong `specs/design/<ten-du-an>/` — lần sau đọc cache. Hết quota → làm theo phương án dự phòng script in ra (cache cũ / export ảnh tay).
- Q&A: `specs/q&a/<ten-du-an>/<ten-spec>-qna.md` — chỉ ghi mâu thuẫn trong PRD, mâu thuẫn design ↔ PRD, lỗ hổng PRD và quyết định đã chốt (Trạng thái `Đã chốt`, mọi lần chạy sau phải theo). Không ghi đè câu đã có — chỉ cập nhật trạng thái / thêm câu mới.

# Ràng buộc

1. Chỉ đọc/ghi file trong thư mục dự án; file tạm để trong scratchpad của phiên.
2. Không trộn dữ liệu giữa các dự án con.
3. Không viết chung chung: Pre-condition / Steps / Expected Result cụ thể, đánh số, đo được.
4. Lấy hết frame trong link Figma user gửi và mở xem từng ảnh — không tự giới hạn số frame.
5. Điểm mờ / mâu thuẫn → ghi Q&A và nêu giả định tạm, không tự đoán rồi viết như yêu cầu đã chốt.
6. Trước khi xoá / ghi đè file đã có, giải thích và chờ xác nhận. Không ghi đè file test case / Q&A đã có kết quả — tạo file mới hoặc hỏi trước.
7. Bí mật (`.figma-token`) không được đọc ra màn hình, copy hay gửi đi.
