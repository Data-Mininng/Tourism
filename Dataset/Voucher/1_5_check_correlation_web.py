import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

print("--- ĐANG CHỤP X-QUANG BỘ DỮ LIỆU WEB ---")

# Đọc dữ liệu vừa sinh ra ở Bước 1
df = pd.read_csv("web_behavior_raw.csv")

# K-Means chỉ chạy trên 3 biến hành vi này, nên ta chỉ soi 3 biến này
cols_to_check = ['Time_On_Site', 'Pages_Viewed', 'Exit_Rate']
data_for_kmeans = df[cols_to_check]

# Tính ma trận tương quan Pearson
corr_matrix = data_for_kmeans.corr()

# Vẽ biểu đồ Bản đồ nhiệt (Heatmap)
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, linewidths=0.5, fmt=".3f")
plt.title("MA TRẬN TƯƠNG QUAN HÀNH VI WEB (KIỂM TRA CHO K-MEANS)")
plt.show()