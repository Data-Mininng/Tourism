import pandas as pd
import numpy as np
import random

print("--- MODULE 1: HỆ THỐNG THU THẬP DỮ LIỆU WEB ---")

np.random.seed(42)
random.seed(42)
n_samples = 1000

# (Giữ nguyên đoạn sinh dữ liệu ở trên...)
time_on_site = np.random.normal(loc=120, scale=40, size=n_samples).clip(10, 600)
pages_viewed = np.random.poisson(lam=4, size=n_samples).clip(1, 20)
exit_rate = np.random.uniform(low=0.01, high=0.99, size=n_samples)

visitor_type = np.random.choice(['New_Visitor', 'Returning_Visitor'], size=n_samples, p=[0.3, 0.7])
device = np.random.choice(['Mobile', 'Desktop'], size=n_samples, p=[0.6, 0.4])
ages = np.random.randint(18, 60, size=n_samples)

voucher_used = []
for i in range(n_samples):
    prob = 0.2
    if visitor_type[i] == 'New_Visitor': prob += 0.3
    if time_on_site[i] > 150: prob += 0.2
    if exit_rate[i] > 0.7: prob -= 0.1
    prob = max(0, min(1, prob))
    voucher_used.append(1 if random.random() < prob else 0)

df_raw = pd.DataFrame({
    'Time_On_Site': np.round(time_on_site, 1),
    'Pages_Viewed': pages_viewed,
    'Exit_Rate': np.round(exit_rate, 3),
    'Visitor_Type': visitor_type,
    'Device': device,
    'Age': ages,
    'Voucher_Used': voucher_used
})

# ĐÃ SỬA THÀNH CSV CHUẨN XỊN
df_raw.to_csv("web_behavior_raw.csv", index=False)
print("✅ Hoàn tất! Đã lưu dữ liệu thô vào: web_behavior_raw.csv")