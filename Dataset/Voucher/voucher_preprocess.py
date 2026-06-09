import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

print("--- BƯỚC 2: TIỀN XỬ LÝ (SCALING & ENCODING) ---")

# 1. Đọc dữ liệu từ file thực tế của anh
try:
    df = pd.read_csv("E-commerce Customer Behavior - Sheet1.csv")
except FileNotFoundError:
    print("Lỗi: Không tìm thấy file 'E-commerce Customer Behavior - Sheet1.csv'")
    exit()

# 2. Xóa các dòng trống (NaN) nếu có để tránh lỗi khi train
df = df.dropna()

# 3. Chọn 5 thuộc tính dạng số phù hợp hoàn hảo với thuật toán GaussianNB
features = ['Age', 'Total Spend', 'Items Purchased', 'Average Rating', 'Days Since Last Purchase']
X = df[features]

# 4. Ép cột nhãn 'Discount Applied' từ định dạng Booleans/Text (TRUE/FALSE) sang số (1/0)
# Đồng thời gán tên 'Nhan_Voucher' để đồng bộ với File Train của anh
df['Nhan_Voucher'] = df['Discount Applied'].astype(int)
y = df['Nhan_Voucher']

# 5. Chuẩn hóa dải số liệu đưa về Phân Phối Chuẩn (Tối ưu cho toán xác xuất của Bayes)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 6. LƯU LẠI CÁI KHUÔN SCALE
joblib.dump(scaler, "voucher_data_scaler.pkl")

# 7. Xuất file dữ liệu sạch trung gian
df_processed = pd.DataFrame(X_scaled, columns=features)
df_processed['Nhan_Voucher'] = y.values
df_processed.to_csv("voucher_processed_data.csv", index=False)

print("=> Đã đúc xong Khuôn: voucher_data_scaler.pkl")
print("=> Đã lưu dữ liệu sạch: voucher_processed_data.csv")