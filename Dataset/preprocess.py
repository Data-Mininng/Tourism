import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os

# ================= 1. ĐỌC DỮ LIỆU CỦA FILE CSV THUẦN TÚY =================
print("Đang đọc dữ liệu gốc từ file CSV...")
# Định vị chính xác thư mục dataset nơi chứa file preprocess.py hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn đến file CSV được sinh ra từ file tạo dữ liệu 
csv_path = os.path.join(current_dir, "tourism_dataset_5k.csv")

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"❌ Không tìm thấy file dữ liệu gốc tại: {csv_path}. Vui lòng chạy file tạo dữ liệu trước!")

df = pd.read_csv(csv_path)

# ================= 2. LÀM SẠCH DỮ LIỆU (CLEANING) =================
print("Bước 1: Làm sạch dữ liệu...")


columns_to_drop = ['id', 'services_list', 'activities_list']
df = df.drop(columns=columns_to_drop, errors='ignore')

# Xóa các dòng có giá trị rỗng (Missing Values) để an toàn
df = df.dropna()

# ================= 3. RỜI RẠC HÓA DỮ LIỆU (DISCRETIZATION) =================
print("Bước 2: Rời rạc hóa ngân sách (Tạo Bin)...")
# Đóng gói ngân sách thành 3 rổ để tiện chạy FPgrowth 
# Cắt theo các mốc: < 8 triệu (Thấp), 8-15 triệu (Trung bình), > 15 triệu (Cao)
bins = [0, 8.0, 15.0, float('inf')]
labels = ['Thap', 'Trung_Binh', 'Cao']
df['ngan_sach_phan_loai'] = pd.cut(df['ngan_sach_trieu'], bins=bins, labels=labels)

# ================= 4. MÃ HÓA DỮ LIỆU CHỮ (ENCODING) =================
print("Bước 3: Mã hóa One-Hot Encoding...")
# Gom các cột chứa chữ (Categorical)
categorical_cols = [
    'gioi_tinh', 'nhom_tuoi', 'muc_dich', 'mua', 
    'dia_diem', 'kenh_dat', 'ngan_sach_phan_loai'
]

# Dùng get_dummies để bung chữ thành các cột nhị phân (0 và 1)
df_encoded = pd.get_dummies(df, columns=categorical_cols, dtype=int)

# ================= 5. CHUẨN HÓA THANG ĐO (SCALING) =================
print("Bước 4: Chuẩn hóa thang đo (Min-Max Scaling)...")
# Cột số cần chuẩn hóa về chung dải [0, 1] để chạy K-Means không bị lệch trọng số
numeric_cols = ['so_nguoi', 'so_ngay', 'ngan_sach_trieu', 'danh_gia']

scaler = MinMaxScaler()
# Chuẩn hóa và đè lại vào các cột cũ
df_encoded[numeric_cols] = scaler.fit_transform(df_encoded[numeric_cols])


# ================= 6. XUẤT DỮ LIỆU ĐÃ TIỀN XỬ LÝ RA THƯ MỤC DATASET =================
print("Bước 5: Lưu dữ liệu ra file...")
output_csv = os.path.join(current_dir, "tourism_dataset_preprocessed.csv")
output_xlsx = os.path.join(current_dir, "tourism_dataset_preprocessed.xlsx")

# Xuất file CSV cho mô hình AI đọc
df_encoded.to_csv(output_csv, index=False, encoding='utf-8')

# Xuất thêm file Excel trực quan
df_encoded.to_excel(output_xlsx, index=False)

print("==================================================")
print(f"TIỀN XỬ LÝ THÀNH CÔNG!")
print(f"Số cột lúc đầu: {df.shape[1]}")
print(f"Số cột sau khi One-Hot Encoding: {df_encoded.shape[1]}")
print(f"Đã lưu file CSV tại: {output_csv}")
print(f"Đã lưu file Excel tại: {output_xlsx}")
print("Dữ liệu giờ đã toàn số là số (0-1), sẵn sàng cho Data Mining!")