import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

print("--- FILE 4: HUẤN LUYỆN VÀ ĐÁNH GIÁ NAIVE BAYES ---")

# 1. Đọc dữ liệu sạch
df = pd.read_csv("web_behavior_clean.csv")
X = df.drop(columns=['Voucher_Used'])
y = df['Voucher_Used']

# 2. CHIA TẬP DỮ LIỆU (80% Học - 20% Thi)
# Bắt buộc phải có bước này để đo độ chính xác thực tế
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"✅ Đã chia tập: {len(X_train)} dòng để Học, {len(X_test)} dòng để Thi.")

# 3. Huấn luyện Mô hình
nb_model = GaussianNB()
nb_model.fit(X_train, y_train)

# 4. Làm bài thi trên tập Test
y_pred = nb_model.predict(X_test)

# 5. HIỆN CHỈ SỐ CHUẨN XÁC RA CONSOLE
acc = accuracy_score(y_test, y_pred) * 100
print("\n" + "="*40)
print(f"📊 ĐỘ CHÍNH XÁC (ACCURACY): {acc:.2f}%")
print("="*40)
print("\n📈 BÁO CÁO CHI TIẾT (Precision, Recall, F1-Score):")
print(classification_report(y_test, y_pred, target_names=['Không xài Mã (0)', 'Có xài Mã (1)']))

# 6. VẼ BIỂU ĐỒ (Ma trận nhầm lẫn) CHO ĐỠ KHÔ KHAN
cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(7, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Đoán: KHÔNG', 'Đoán: CÓ'], 
            yticklabels=['Thực: KHÔNG', 'Thực: CÓ'],
            annot_kws={"size": 14, "weight": "bold"})

plt.title(f"MA TRẬN NHẦM LẪN NAIVE BAYES\nĐộ chính xác: {acc:.2f}%", fontsize=14, fontweight='bold', pad=15)
plt.ylabel('Thực tế (Actual)')
plt.xlabel('AI Dự đoán (Predicted)')
plt.show()

# 7. Lưu Model
joblib.dump(nb_model, "naive_bayes_model.pkl")
print("\n✅ Đã lưu file model Naive Bayes sẵn sàng đưa lên C#!")