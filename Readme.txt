Thao tác để web hoạt động
1. chạy file run_all.py
( file sẽ tự nạp các thư viện, tạo cũng như chạy các file tương ứng để triển khai API luật kết hợp và cây quyết định )
2. import file tourism_dataset_preprocessed vừa được tạo trong thư mục Dataset vào SQL Server đặt với tên database mới là Tourism_DB
3. chạy web bình thường
===============================
Thao tác trên web:
web sẽ dựa trên thao tác người dùng như truy cập một dv bất kỳ, web sẽ gửi các dv đó thông qua phương thức post để nhận kết quả luật từ bảng luật có tên là Luat_FPGrowth. Trang "dành riêng cho bạn" sẽ hiện các luật đó bằng cách đề xuất các dv tương ứng
Đối với cấp voucher, bản chất model là dự đoán xem có đặt hàng thay không Khách hàng sẽ được cấp voucher 15% nếu thỏa mãn ít nhất một trong hai điều kiện sau:

Chỉ số giá trị trang (page_values) lớn hơn 0.5.

HOẶC Thời gian xem sản phẩm (productrelated_duration) lớn hơn 0.03