import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib

print("--- BƯỚC 2: TIỀN XỬ LÝ (SCALING) ---")

# 1. Đọc dữ liệu thô
try:
    df = pd.read_csv("voucher_raw_data.csv")
except FileNotFoundError:
    print("Lỗi: Không tìm thấy voucher_raw_data.csv")
    exit()

features = ['So_Lan_Xem', 'Thoi_Gian_Giay', 'Cuon_Trang', 'Ngan_Sach']
X = df[features]
y = df['Nhan_Voucher']

# 2. Chuẩn hóa dải số liệu về [0, 1]
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# 3. LƯU LẠI CÁI KHUÔN (Để mốt API dùng)
joblib.dump(scaler, "voucher_data_scaler.pkl")

# 4. Lưu lại dữ liệu đã sạch ra một file CSV mới
df_processed = pd.DataFrame(X_scaled, columns=features)
df_processed['Nhan_Voucher'] = y.values
df_processed.to_csv("voucher_processed_data.csv", index=False)

print("=> Đã đúc xong Khuôn: voucher_data_scaler.pkl")
print("=> Đã lưu dữ liệu sạch: voucher_processed_data.csv")