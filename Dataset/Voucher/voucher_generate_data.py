import pandas as pd
import numpy as np
import random

print("--- BƯỚC 1: TẠO DỮ LIỆU THÔ THỰC TẾ ---")

np.random.seed(42)
random.seed(42)

data = []

for _ in range(5000):

    # --------------------------
    # HÀNH VI KHÁCH HÀNG
    # --------------------------

    so_lan_xem = random.randint(1, 15)

    thoi_gian_giay = int(
        np.clip(
            np.random.normal(180, 120),
            5,
            600
        )
    )

    cuon_trang = int(
        np.clip(
            np.random.normal(60, 25),
            0,
            100
        )
    )

    ngan_sach = round(
        np.clip(
            np.random.normal(15, 6),
            2,
            30
        ),
        1
    )

    # Đã từng mua hàng chưa
    da_mua_hang = random.choice([0, 1])

    # Thành viên VIP
    vip = random.choice([0, 1])

    # --------------------------
    # TÍNH ĐIỂM QUAN TÂM
    # --------------------------

    score = 0

    # Xem nhiều lần
    score += so_lan_xem * 0.15

    # Thời gian ở lại trang
    score += thoi_gian_giay / 100

    # Cuộn sâu
    score += cuon_trang / 25

    # Ngân sách thấp => dễ cấp voucher
    score += (30 - ngan_sach) / 5

    # Khách cũ
    score += da_mua_hang * 1.5

    # VIP
    score += vip * 1.0

    # Nhiễu tự nhiên
    score += np.random.normal(0, 0.8)

    # --------------------------
    # CHUYỂN THÀNH XÁC SUẤT
    # --------------------------

    probability = 1 / (1 + np.exp(-(score - 8)))

    # --------------------------
    # QUYẾT ĐỊNH CẤP VOUCHER
    # --------------------------

    nhan_voucher = 1 if random.random() < probability else 0

    data.append([
        so_lan_xem,
        thoi_gian_giay,
        cuon_trang,
        ngan_sach,
        da_mua_hang,
        vip,
        nhan_voucher
    ])

df = pd.DataFrame(
    data,
    columns=[
        "So_Lan_Xem",
        "Thoi_Gian_Giay",
        "Cuon_Trang",
        "Ngan_Sach",
        "Da_Mua_Hang",
        "VIP",
        "Nhan_Voucher"
    ]
)

print("\nPHÂN BỐ NHÃN:")
print(df["Nhan_Voucher"].value_counts())

print("\nTỶ LỆ:")
print(df["Nhan_Voucher"].value_counts(normalize=True) * 100)

df.to_csv(
    "voucher_raw_data.csv",
    index=False
)

print("\n=> Đã lưu voucher_raw_data.csv")