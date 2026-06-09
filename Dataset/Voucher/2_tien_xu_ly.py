import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

print("--- MODULE 2: PIPELINE TIỀN XỬ LÝ (PREPROCESSING) ---")

# Đọc định dạng CSV
df = pd.read_csv("web_behavior_raw.csv")

df = df.dropna()

encoders = {}
categorical_cols = ['Visitor_Type', 'Device']
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

joblib.dump(encoders, "label_encoders.pkl")

scaler = StandardScaler()
numeric_cols = ['Time_On_Site', 'Pages_Viewed', 'Exit_Rate', 'Age']
df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
joblib.dump(scaler, "data_scaler.pkl")

# Xuất ra định dạng CSV
df.to_csv("web_behavior_clean.csv", index=False)
print("✅ Hoàn tất! Dữ liệu sạch lưu tại: web_behavior_clean.csv")