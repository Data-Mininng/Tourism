import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

print("Đang chụp X-quang dữ liệu...")

# Đọc dữ liệu gốc
df = pd.read_csv("E-commerce Customer Behavior - Sheet1.csv")

# Lọc ra các cột số học mang ý nghĩa hành vi để kiểm tra chéo
cols_to_check = ['Total Spend', 'Items Purchased', 'Days Since Last Purchase', 'Average Rating']
data_for_kmeans = df[cols_to_check]

# Tính toán ma trận tương quan Pearson
corr_matrix = data_for_kmeans.corr()

# Vẽ biểu đồ Heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, linewidths=0.5, fmt=".2f")
plt.title("MA TRẬN TƯƠNG QUAN (KIỂM TRA TÍNH ĐỘC LẬP)")
plt.show()