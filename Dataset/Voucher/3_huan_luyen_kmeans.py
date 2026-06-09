import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import joblib

print("--- FILE 3: HUẤN LUYỆN VÀ TRỰC QUAN HÓA K-MEANS ---")

# 1. Đọc dữ liệu sạch
df = pd.read_csv("web_behavior_clean.csv")
X_kmeans = df[['Time_On_Site', 'Pages_Viewed', 'Exit_Rate']]

# 2. Huấn luyện
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['Cluster'] = kmeans.fit_predict(X_kmeans)

# 3. Trực quan hóa những gì AI học được (VẼ BIỂU ĐỒ)
# Lấy tọa độ tâm cụm
centroids = pd.DataFrame(kmeans.cluster_centers_, columns=X_kmeans.columns)
centroids['Cluster'] = ['Cụm 0', 'Cụm 1', 'Cụm 2']

# Biến đổi dữ liệu để vẽ biểu đồ
centroids_melted = centroids.melt(id_vars='Cluster', var_name='Đặc trưng', value_name='Giá trị')

plt.figure(figsize=(10, 6))
sns.barplot(data=centroids_melted, x='Đặc trưng', y='Giá trị', hue='Cluster', palette='viridis')
plt.title("HÌNH ẢNH HỌC TẬP K-MEANS: SO SÁNH TỌA ĐỘ CÁC TÂM CỤM", fontsize=14, fontweight='bold')
plt.ylabel("Giá trị (Đã chuẩn hóa)")
plt.xlabel("Đặc trưng hành vi")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# 4. Lưu Model
joblib.dump(kmeans, "kmeans_model.pkl")
print("✅ Đã lưu K-Means model thành công!")