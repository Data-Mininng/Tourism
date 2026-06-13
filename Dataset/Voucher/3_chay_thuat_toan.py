import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier # ĐÂY MỚI LÀ CÂY QUYẾT ĐỊNH CHUẨN
from sklearn.metrics import accuracy_score

# 1. Đọc dữ liệu CSV đã qua tiền xử lý
df = pd.read_csv('Dataset/Voucher/du_lieu_da_xu_ly.csv')
X = df.drop('Need_Voucher', axis=1)
y = df['Need_Voucher']

# 2. Chia 3 tập biệt lập: 60% Train - 20% Val - 20% Test
X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.25, random_state=42)

print(f"Đã chia 3 tập chuẩn Cây quyết định: Train ({len(X_train)}) - Val ({len(X_val)}) - Test ({len(X_test)})")

# 3. Dò tìm điểm Overfitting của đúng 1 Cây quyết định
max_depths = range(1, 16)
train_scores = []
val_scores = []

for depth in max_depths:
    # Khởi tạo chuẩn DecisionTreeClassifier
    model = DecisionTreeClassifier(max_depth=depth, random_state=42)
    model.fit(X_train, y_train)
    
    # Chấm điểm trên tập Huấn luyện và tập Kiểm định (Val)
    train_scores.append(accuracy_score(y_train, model.predict(X_train)))
    val_scores.append(accuracy_score(y_val, model.predict(X_val)))

# 4. Vẽ biểu đồ tìm Max Depth tối ưu cho Cây quyết định
plt.figure(figsize=(10, 6))
plt.plot(max_depths, train_scores, label='Điểm trên tập Huấn luyện (Train)', marker='o', color='blue')
plt.plot(max_depths, val_scores, label='Điểm trên tập Kiểm định (Val)', marker='s', color='orange')

plt.title('Dò tìm Max Depth tối ưu cho Cây Quyết Định trên tập Validation')
plt.xlabel('Độ sâu của cây (Max Depth)')
plt.ylabel('Độ chính xác')
plt.xticks(max_depths)
plt.legend()
plt.grid(True)
plt.show()