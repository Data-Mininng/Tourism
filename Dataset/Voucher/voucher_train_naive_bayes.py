import pandas as pd
from sklearn.naive_bayes import GaussianNB
import joblib

print("--- BƯỚC 3: HUẤN LUYỆN NAIVE BAYES ---")

# Đọc file dữ liệu ĐÃ QUA TIỀN XỬ LÝ
try:
    df = pd.read_csv("voucher_processed_data.csv")
except FileNotFoundError:
    print("Lỗi: Không tìm thấy voucher_processed_data.csv")
    exit()

X = df[['So_Lan_Xem', 'Thoi_Gian_Giay', 'Cuon_Trang', 'Ngan_Sach']]
y = df['Nhan_Voucher']

# Train bằng Naive Bayes (Phân phối Gaussian cho dữ liệu liên tục)
model = GaussianNB()
model.fit(X, y)

# Lưu bộ não
joblib.dump(model, "classification_model_bayes.pkl")
print("=> Đã lưu xong não bộ: classification_model_bayes.pkl")