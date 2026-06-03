import pandas as pd
from sklearn.cluster import KMeans
import joblib

print("--- HUẤN LUYỆN GOM CỤM K-MEANS ---")

try:
    df = pd.read_csv("voucher_processed_data.csv")
except FileNotFoundError:
    print("Lỗi: Không tìm thấy voucher_processed_data.csv")
    exit()

# Chỉ lấy những người được nhận voucher để chia cụm
df_voucher = df[df['Nhan_Voucher'] == 1].copy()
X = df_voucher[['So_Lan_Xem', 'Thoi_Gian_Giay', 'Cuon_Trang', 'Ngan_Sach']]

# Train K-Means
kmeans_model = KMeans(n_clusters=3, random_state=99, n_init=10)
kmeans_model.fit(X)

# Lưu bộ não
joblib.dump(kmeans_model, "voucher_kmeans.pkl")
print("=> Đã lưu xong não bộ: voucher_kmeans.pkl")