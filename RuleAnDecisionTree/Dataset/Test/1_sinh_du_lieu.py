import pandas as pd
import numpy as np
import random

# Hàm sinh dữ liệu có chủ đích
def sinh_data_web_dulich(so_luong=5000):
    data = []
    for _ in range(so_luong):
        session_duration = random.randint(10, 600)
        viewed_pricing_page = random.randint(0, 10)
        scroll_depth = random.choice([0, 1])
        device = random.choice(['Mobile', 'PC'])
        
        # Logic giả lập
        if viewed_pricing_page > 3 and session_duration > 120:
            need_voucher = np.random.choice([1, 0], p=[0.85, 0.15])
        elif viewed_pricing_page <= 1:
            need_voucher = np.random.choice([1, 0], p=[0.1, 0.9])
        else:
            need_voucher = np.random.choice([1, 0], p=[0.4, 0.6])
            
        data.append([session_duration, viewed_pricing_page, scroll_depth, device, need_voucher])
        
    return pd.DataFrame(data, columns=['Session_Duration', 'Viewed_Pricing_Page', 'Scroll_Depth', 'Device', 'Need_Voucher'])

# Chạy và lưu ra chuẩn file CSV
df = sinh_data_web_dulich(5000)
df.to_csv('du_lieu_goc.csv', index=False)
print("Đã sinh xong 5000 dòng dữ liệu và lưu chuẩn định dạng vào 'du_lieu_goc.csv'")