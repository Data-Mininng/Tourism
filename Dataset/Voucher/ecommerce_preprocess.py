import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

print("--- BƯỚC 1: TIỀN XỬ LÝ DỮ LIỆU (PREPROCESSING) ---")

# 1. Đọc dữ liệu thô
df = pd.read_csv("E-commerce Customer Behavior - Sheet1.csv")

# 2. XỬ LÝ DỮ LIỆU THIẾU
mode_satisfaction = df['Satisfaction Level'].mode()[0]
df['Satisfaction Level'] = df['Satisfaction Level'].fillna(mode_satisfaction)

# 3. LỌC BỎ CỘT VÔ DỤNG & CỘT BỊ ĐA CỘNG TUYẾN
# Chém Customer ID (vô nghĩa) và Items Purchased, Average Rating (do dính chặt với Total Spend)
cols_to_drop = ['Customer ID', 'Items Purchased', 'Average Rating']

for col in cols_to_drop:
    if col in df.columns:
        df = df.drop(columns=[col])

# 4. XỬ LÝ NGOẠI LAI (OUTLIERS) BẰNG IQR CHO CỘT TIỀN
Q1 = df['Total Spend'].quantile(0.25)
Q3 = df['Total Spend'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
df = df[(df['Total Spend'] >= lower_bound) & (df['Total Spend'] <= upper_bound)]

# 5. MÃ HÓA CHỮ THÀNH SỐ (LABEL ENCODING)
label_encoders = {}
categorical_cols = ['Gender', 'City', 'Membership Type', 'Satisfaction Level']

for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

# Cột Target (True/False -> 1/0)
df['Discount Applied'] = df['Discount Applied'].astype(int)

# Lưu bộ từ điển để API C# xài sau này
joblib.dump(label_encoders, "label_encoders.pkl")

# 6. CHUẨN HÓA THANG ĐO (SCALING)
# Chỉ còn lại các biến số học độc lập
scaler = StandardScaler()
numeric_cols = ['Age', 'Total Spend', 'Days Since Last Purchase']
df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

# Lưu khuôn ép chuẩn hóa
joblib.dump(scaler, "data_scaler.pkl")

# 7. XUẤT FILE DATA SẠCH
df.to_csv("ecommerce_processed_data.csv", index=False)
print("✅ Đã xử lý xong! Dữ liệu sạch được lưu tại: ecommerce_processed_data.csv")
print("✅ Đã lưu label_encoders.pkl và data_scaler.pkl để phục vụ API.")