import pandas as pd
import numpy as np
import random

print("--- BƯỚC 1: TẠO DỮ LIỆU THÔ ---")
np.random.seed(42)
random.seed(42)

data = []
for _ in range(3000):
    so_lan_xem = random.randint(1, 15)
    thoi_gian_giay = random.randint(2, 600)
    cuon_trang = random.randint(0, 100)
    ngan_sach = round(random.uniform(2.0, 30.0), 1)
    
    nhan_voucher = 0
    if 3 <= so_lan_xem <= 8 and thoi_gian_giay > 60 and cuon_trang > 50 and ngan_sach < 15.0:
        nhan_voucher = 1
        
    if random.random() < 0.1: # Bơm nhiễu
        nhan_voucher = 1 if nhan_voucher == 0 else 0
        
    data.append([so_lan_xem, thoi_gian_giay, cuon_trang, ngan_sach, nhan_voucher])

df = pd.DataFrame(data, columns=['So_Lan_Xem', 'Thoi_Gian_Giay', 'Cuon_Trang', 'Ngan_Sach', 'Nhan_Voucher'])
df.to_csv("voucher_raw_data.csv", index=False)
print("=> Đã lưu xong dữ liệu thô: voucher_raw_data.csv")