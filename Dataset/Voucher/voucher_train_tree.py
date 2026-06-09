import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

print("="*65)
print("🚀 BƯỚC 3: HUẤN LUYỆN & KIỂM ĐỊNH CÂY QUYẾT ĐỊNH 🚀")
print("="*65)

# 1. Đọc dữ liệu
df = pd.read_csv("voucher_processed_data.csv")
X = df[['So_Lan_Xem', 'Thoi_Gian_Giay', 'Cuon_Trang', 'Ngan_Sach']]
y = df['Nhan_Voucher']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 2. Huấn luyện bằng Decision Tree 
# VŨ KHÍ BÍ MẬT: class_weight='balanced' ép AI phải chú ý đến nhóm Khách Săn Sale
model = DecisionTreeClassifier(max_depth=5, class_weight='balanced', random_state=42)
model.fit(X_train, y_train)

# 3. Làm bài thi
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

train_acc = accuracy_score(y_train, y_train_pred) * 100
test_acc = accuracy_score(y_test, y_test_pred) * 100

print(f"\n📊 [1] TỔNG QUAN ĐỘ CHÍNH XÁC (ACCURACY):")
print(f"    👉 Điểm thi Đề cương (Train) : {train_acc:.2f}%")
print(f"    👉 Điểm thi Thực tế (Test)   : {test_acc:.2f}%")

print(f"\n🔍 [2] MA TRẬN NHẦM LẪN (CONFUSION MATRIX):")
cm = confusion_matrix(y_test, y_test_pred)
print("                       [Máy đoán: KHÔNG]    [Máy đoán: CÓ]")
print(f"  [Thực tế: KHÔNG]          {cm[0][0]:<15} {cm[0][1]}")
print(f"  [Thực tế: CÓ]             {cm[1][0]:<15} {cm[1][1]}")

print(f"\n📈 [3] BÁO CÁO CHI TIẾT CÁC CHỈ SỐ:")
print(classification_report(y_test, y_test_pred, target_names=["Khách thường (0)", "Khách Săn Sale (1)"]))

# 4. Lưu Model đổi tên cho khỏi nhầm
joblib.dump(model, "gatekeeper_tree.pkl")
print("="*65)
print("✅ ĐÃ LƯU NÃO BỘ THÀNH CÔNG: gatekeeper_tree.pkl")
print("="*65)