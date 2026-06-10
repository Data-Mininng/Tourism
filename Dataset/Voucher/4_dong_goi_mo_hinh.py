import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier # ĐÂY MỚI LÀ CÂY QUYẾT ĐỊNH CHUẨN
from sklearn.metrics import accuracy_score, classification_report

# 1. Đọc dữ liệu
df = pd.read_csv('du_lieu_da_xu_ly.csv')
X = df.drop('Need_Voucher', axis=1)
y = df['Need_Voucher']

# 2. Chia tập dữ liệu giống hệt file 3
X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.25, random_state=42)

print("--- Huấn luyện và đóng gói CHUẨN CÂY QUYẾT ĐỊNH (Decision Tree) ---")

# 3. Khởi tạo mô hình Cây quyết định với độ sâu anh chọn từ biểu đồ file 3
# Em tạm để cấu hình là 5, anh sửa lại theo đỉnh của biểu đồ mới nhé
best_depth = 5 
model_voucher = DecisionTreeClassifier(max_depth=best_depth, random_state=42)
model_voucher.fit(X_train, y_train)

# 4. Đánh giá khách quan trên tập TEST biệt lập
y_pred_test = model_voucher.predict(X_test)
print(f"\n[KẾT QUẢ] Độ chính xác thực tế của Cây quyết định trên tập TEST: {accuracy_score(y_test, y_pred_test) * 100:.2f}%")
print("\nBảng đo lường chất lượng chi tiết:")
print(classification_report(y_test, y_pred_test))

# 5. Đóng gói mô hình vật lý
joblib.dump(model_voucher, 'mo_hinh_quyet_dinh_voucher.pkl')
print("\nĐã xuất file 'mo_hinh_quyet_dinh_voucher.pkl' chuẩn thuật toán Cây quyết định 100%!")