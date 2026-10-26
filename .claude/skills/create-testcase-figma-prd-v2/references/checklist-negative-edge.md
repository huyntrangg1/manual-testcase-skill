# Checklist suy diễn Negative / Edge

Cách dùng: lớp 3 lọc theo PRD / Q&A đã chốt trước (app không có → `N/A — <lý do>` 1 lần cho cả spec; có thì không được N/A). Lớp 1 áp cho mỗi rule; lớp 2 cho mỗi phần tử trong inventory màn; nhóm "Theo luồng" chỉ 1–2 điểm đại diện mỗi Flow. Mỗi mục áp dụng → 1 dòng Rule nguồn `Checklist: <lớp/nhóm> / <mục>`; PRD không nói hệ thống xử lý thế nào → Q&A, không bịa Expected. Mục không áp dụng → `N/A — <lý do>`. Gặp loại phần tử chưa có → tự áp cùng tinh thần (biên, rỗng, sai định dạng, gián đoạn, lặp thao tác, đồng thời). Review phát hiện sót do thiếu mục → bổ sung mục tổng quát vào đúng lớp.

## 1. Lõi — mỗi rule
- **Phân vùng**: mỗi lớp hợp lệ cho kết quả khác nhau ≥ 1 case Positive; mỗi lớp không hợp lệ ≥ 1 case Negative.
- **Biên**: min−1 / min / max / max+1 (số, độ dài, số lượng); thời gian: đúng mốc, trước/sau 1 đơn vị; biên điều kiện hoàn thành / hết hạn.
- **Bảng quyết định**: rule ≥ 2 điều kiện → mọi tổ hợp khác kết quả; tổ hợp không thể xảy ra ghi lý do.
- **Chuyển trạng thái**: mọi chuyển hợp lệ; thử chuyển không hợp lệ; sau kết thúc / huỷ / hết hạn về đúng trạng thái gốc.
- **Vòng đời dữ liệu**: tạo / sửa / xoá phản ánh ở mọi nơi dùng tới; còn sau khi thoát và mở lại.
- **Thời điểm & đồng thời**: sự kiện tự động xảy ra khi user đang thao tác (popup / form đang mở); bấm lặp / 2 thao tác gần đồng thời; giá trị đã lưu quá hạn trước khi dùng; huỷ việc đã lên lịch khi luồng huỷ; chờ lâu ở 1 bước.
- **Thời gian & locale**: qua 0h / ngày / tuần / tháng mới; đổi múi giờ; chỉnh giờ máy tiến / lùi; format ngày, số, tiền theo locale.
- **Phân quyền / vai trò**: mỗi vai trò đúng phần được phép; vai trò không có quyền bị chặn; quyền đổi khi đang dùng.
- **Lỗi & phục hồi**: mất kết nối / server lỗi giữa thao tác ghi → không mất, không ghi trùng; thao tác lại sau lỗi; trạng thái nhất quán sau phục hồi.

## 2. Theo loại phần tử
- **Ô nhập**: trống · chỉ khoảng trắng · khoảng trắng đầu/cuối · min, min−1, max, max+1 · ký tự đặc biệt, emoji, có dấu · số âm, 0, thập phân, dấu phẩy/chấm · paste chuỗi dài · sai định dạng · đổi đơn vị rồi kiểm quy đổi + làm tròn.
- **Nút / CTA**: bấm 2 lần nhanh · disabled khi chưa đủ điều kiện, enable lại khi đủ · bấm khi loading · bấm khi offline.
- **Picker / toggle / chọn**: giá trị mặc định · giá trị biên đầu/cuối dải · cuộn tới đầu/cuối · bỏ chọn hết · vượt số lượng tối đa · đổi rồi Back có giữ không.
- **List / dữ liệu động**: 0 · 1 · nhiều / cuộn hết · phân trang · text dài bị cắt · ảnh lỗi · cập nhật khi quay lại màn · giữ lọc / sắp xếp khi vào màn con rồi quay lại.
- **Popup / dialog / sheet**: tap ngoài · Back / vuốt đóng · X không lưu · mở lại có giữ trạng thái · popup chồng popup · sự kiện tự động khi popup đang mở.
- **Luồng nhiều bước**: Back từng bước có giữ dữ liệu · xuống nền / thoát giữa chừng rồi mở lại · deep link / notification vào giữa luồng · xong luồng rồi Back · vào lại khi đang có phiên dở.
- **Tính toán / đếm**: biên công thức · làm tròn · chia 0 / dữ liệu rỗng · mỗi khoảng kết quả ≥ 1 case · reset theo ngày/tuần · format khi qua ngưỡng (59:59 → 01:00:00, 999 → 1,000).
- **Timer / hẹn giờ**: chạy đúng khi app ở nền / bị đóng / máy khởi động lại · không vượt mục tiêu · đạt mục tiêu khi app không mở · bắt đầu ở quá khứ / tương lai · huỷ thì huỷ luôn nhắc nhở.
- **Animation / tự chuyển màn**: thao tác khi animation chạy · auto-chuyển đúng thời gian · xuống nền giữa animation.

## 3. Theo app — lọc theo PRD / Q&A đã chốt
- **Tài khoản** (bắt buộc nếu có đăng nhập): đổi tài khoản → dữ liệu / quyền lợi tách đúng · đăng nhập lại thấy lại dữ liệu · gỡ cài lại · 1 tài khoản 2 máy · giới hạn tính theo tài khoản hay thiết bị.
- **Gói Free / Trial / Premium**: mỗi gói đúng tính năng · Free → Trial → Premium → hết hạn → gia hạn · mua xong mở ngay · khôi phục trên máy mới · huỷ giữa kỳ · trạng thái gói đồng bộ giữa các thiết bị.
- **Quảng cáo**: rewarded load fail / đóng giữa chừng / không fill / không thưởng khi chưa xem hết · vị trí, thời điểm, tần suất · không hiện với Premium · không che nút chính.
- **IAP**: huỷ · lỗi · mất mạng giữa thanh toán · bấm mua 2 lần · giá đúng store / region.
- **Quyền hệ thống**: lần đầu xin · từ chối rồi vào lại · từ chối vĩnh viễn → hướng dẫn Settings · cấp từ Settings rồi quay lại · thu hồi khi đang chạy · khác biệt theo OS.
- **Notification**: nhận khi nền / đóng / khoá màn hình · bấm mở đúng màn · tắt trong app và Settings · đổi giờ / múi giờ · huỷ khi tiến trình huỷ.
- **Dữ liệu server**: 4xx/5xx có báo lỗi + retry · rỗng / null / thiếu trường · text rất dài, số rất lớn · dữ liệu đổi khi đang mở màn · offline rồi đồng bộ.
- **Cập nhật phiên bản**: dữ liệu, cài đặt, tiến trình, gói còn sau nâng cấp · màn mới hiện đúng với user cũ · force / optional update.
- **Remote config**: bật/tắt, giá trị biên, sai kiểu / thiếu key → mặc định · đổi khi app đang mở.
- **Thiết bị đi kèm** (đồng hồ, thiết bị BLE…): chưa pair · mất kết nối giữa thao tác · thiết bị khoá màn hình / hết pin · dữ liệu đồng bộ 2 chiều không mất, không trùng.

## 4. Nền tảng iOS & Android
Case dùng chung, bước khác nhau ghi `Android: … / iOS: …`; hành vi chỉ 1 OS → case riêng.
- Back: Android nút/cử chỉ hệ thống (cùng kết quả nút ← của app) · iOS vuốt mép trái.
- Đóng hẳn app: Android Recent apps vuốt bỏ · iOS App Switcher vuốt lên.
- Chạy nền: Android có thể bị hệ thống đóng · iOS tạm dừng gần như ngay → định giờ dựa mốc thời gian + notification lên lịch.
- Quyền notification: Android 13+ có popup, ≤ 12 mặc định có quyền (case riêng) · iOS từ chối rồi chỉ bật lại trong Settings.
- Quyền khác: Android "Don't ask again" · iOS chọn 1 lần / khi dùng app / ảnh giới hạn.
- Cỡ chữ lớn, vùng an toàn (tai thỏ, Dynamic Island, thanh điều hướng), bàn phím che ô nhập, widget / Live Activity nếu spec có, phiên bản OS tối thiểu theo PRD.

## Theo luồng (1–2 điểm mỗi Flow)
Offline khi vào màn · mất mạng giữa thao tác · mạng chậm / timeout · xuống nền rồi mở lại · đóng hẳn app rồi mở lại · user mới (first-run) vs user cũ.
