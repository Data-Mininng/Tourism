import pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

print("="*65)
print("BƯỚC 3: HUẤN LUYỆN & KIỂM ĐỊNH MÔ HÌNH NAIVE BAYES ")
print("="*65)

# 1. Đọc dữ liệu đã qua tiền xử lý
try:
    df = pd.read_csv("voucher_processed_data.csv")
except FileNotFoundError:
    print("Lỗi: Không tìm thấy 'voucher_processed_data.csv'. Hãy chạy file tiền xử lý trước!")
    exit()

# Gọi 5 cột đặc trưng
features = ['Age', 'Total Spend', 'Items Purchased', 'Average Rating', 'Days Since Last Purchase']
X = df[features]
y = df['Nhan_Voucher']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 2. Huấn luyện AI
nb_model = GaussianNB()
nb_model.fit(X_train, y_train)

# 3. Đánh giá mô hình
y_train_pred = nb_model.predict(X_train)
y_test_pred = nb_model.predict(X_test)

train_acc = accuracy_score(y_train, y_train_pred) * 100
test_acc = accuracy_score(y_test, y_test_pred) * 100

# ================= HIỂN THỊ LOG CHUYÊN NGHIỆP =================

print(f"\n [1] TỔNG QUAN ĐỘ CHÍNH XÁC (ACCURACY):")
print(f"     Train-Acc : {train_acc:.2f}%")
print(f"     Test  : {test_acc:.2f}%")
print(f"    => Độ lệch (Kiểm tra Overfit): {abs(train_acc - test_acc):.2f}%")

print(f"\n[2] MA TRẬN NHẦM LẪN (CONFUSION MATRIX - TRÊN TẬP TEST):")
cm = confusion_matrix(y_test, y_test_pred)
print("                       [Máy đoán: KHÔNG]    [Máy đoán: CÓ]")
print(f"  [Thực tế: KHÔNG]          {cm[0][0]:<15} {cm[0][1]}")
print(f"  [Thực tế: CÓ]             {cm[1][0]:<15} {cm[1][1]}")


print(f"\n[3] BÁO CÁO CHI TIẾT CÁC CHỈ SỐ (CLASSIFICATION REPORT):")
print(classification_report(y_test, y_test_pred, target_names=["Khách thường (0)", "Khách Săn Sale (1)"]))

# 4. Lưu Model
joblib.dump(nb_model, "classification_model_bayes.pkl")
print("="*65)
print("ĐÃ LƯU NÃO BỘ THÀNH CÔNG: classification_model_bayes.pkl")
print("="*65)