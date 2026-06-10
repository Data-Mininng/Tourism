import pandas as pd
import numpy as np
import random
import os

# Set seed để ra kết quả cố định mỗi lần chạy (dễ debug)
np.random.seed(42)
random.seed(42)

# ================== CẤU HÌNH DATA ==================

DESTINATIONS = [
    'Ha_Long', 'Da_Nang', 'Hoi_An', 'Sapa', 'Nha_Trang',
    'Phu_Quoc', 'Da_Lat', 'Hue', 'HCMC', 'Ha_Noi', 'Mui_Ne'
]

# CHỈ GIỮ LẠI CÁC DỊCH VỤ CÓ API HOẶC DỄ TỰ QUẢN LÝ DB
SERVICES = [
    'DV_Khach_San_Homestay',   # Gọi API Booking.com
    'DV_Ve_May_Bay',           # Gọi API Google Flights
    'DV_Dua_Don_San_Bay',      # Tự build DB nội bộ (Giá cố định)
    'DV_Tour_Va_Khu_Vui_Choi', # Gọi API Tripadvisor/Viator
    'DV_Thue_Xe_Tu_Lai'        # Gọi API Booking Car Rental
]

# HOẠT ĐỘNG GIÚP PHÂN TÍCH HÀNH VI (TỰ BUILD DB NỘI BỘ)
ACTIVITIES = [
    'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
    'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh'
]

TRIP_PURPOSES = ['Gia_Dinh', 'Tuan_Trang_Mat', 'Di_Mot_Minh', 'Ban_Be', 'Cong_Tac', 'Kham_Pha']
SEASONS = ['Xuan', 'Ha', 'Thu', 'Dong']
AGE_GROUPS = ['18-25', '26-35', '36-45', '46-55', '55+']
BOOKING_CHANNELS = ['Website_OTA', 'Truc_Tiep', 'App_Di_Dong', 'Super_App_Vi_Dien_Tu']

HAS_AIRPORT = ['Da_Nang', 'Nha_Trang', 'Phu_Quoc', 'Da_Lat', 'Hue', 'HCMC', 'Ha_Noi', 'Ha_Long']
BEACH = ['Nha_Trang', 'Phu_Quoc', 'Da_Nang', 'Mui_Ne', 'Ha_Long']
MOUNTAIN = ['Sapa', 'Da_Lat']
CULTURE = ['Hoi_An', 'Hue', 'Ha_Noi', 'HCMC']

# ================== LOGIC VÀ TẠO DATA ==================

def calculate_budget(destination, days, group_size, budget_level):
    base = 1.0
    if destination in ['Phu_Quoc', 'Ha_Long']:
        base = random.uniform(1.2, 2.5)
    elif destination in ['Da_Nang', 'Nha_Trang', 'Mui_Ne']:
        base = random.uniform(0.9, 2.0)
    elif destination in ['Sapa', 'Da_Lat']:
        base = random.uniform(0.7, 1.5)
    else:
        base = random.uniform(0.6, 1.3)

    mul = 1.0
    if budget_level == 'high':
        mul = random.uniform(1.5, 2.5)
    elif budget_level == 'medium':
        mul = random.uniform(1.0, 1.5)
    else:
        mul = random.uniform(0.7, 1.0)

    total = base * days * group_size * mul
    total = total * random.uniform(0.85, 1.2)
    return round(total, 1)

def generate_record(i):
    tourist_type = random.choice(['beach', 'mountain', 'culture', 'random'])
    budget_level = random.choice(['low', 'medium', 'high'])

    # ===== THÔNG TIN CƠ BẢN =====
    if tourist_type == 'beach':
        destination = random.choice(BEACH)
    elif tourist_type == 'mountain':
        destination = random.choice(MOUNTAIN)
    elif tourist_type == 'culture':
        destination = random.choice(CULTURE)
    else:
        destination = random.choice(DESTINATIONS)

    gender = random.choice(['Nam', 'Nu'])
    age_group = random.choice(AGE_GROUPS)
    purpose = random.choice(TRIP_PURPOSES)
    group_size = random.randint(1, 6)
    days = random.randint(2, 8)
    season = random.choice(SEASONS)
    booking_channel = random.choice(BOOKING_CHANNELS)
    budget = calculate_budget(destination, days, group_size, budget_level)

    # ===== GÁN LOGIC DỊCH VỤ (DV) =====
    services = {s: 0 for s in SERVICES}
    
    # 95% khách sẽ đặt lưu trú (5% nhiễu là ở nhà người thân/bạn bè)
    if random.random() < 0.95:
        services['DV_Khach_San_Homestay'] = 1

    # Logic vé máy bay & Đưa đón
    if destination in HAS_AIRPORT:
        if random.random() < 0.8:
            services['DV_Ve_May_Bay'] = 1
            if random.random() < 0.6:
                services['DV_Dua_Don_San_Bay'] = 1

    # Logic Tour/Khu vui chơi
    if destination in BEACH or destination in CULTURE:
        if random.random() < 0.6:
            services['DV_Tour_Va_Khu_Vui_Choi'] = 1
            
    # Thuê xe tự lái cho nhóm đi núi hoặc đi văn hóa
    if destination in MOUNTAIN or destination in CULTURE:
        if random.random() < 0.4:
            services['DV_Thue_Xe_Tu_Lai'] = 1

    # ===== BƠM NHIỄU (NOISE) CHO DỊCH VỤ =====
    # Tránh Overfitting: Đảo ngược kết quả với tỷ lệ nhỏ (5%)
    for s in SERVICES:
        if random.random() < 0.05:
            if services[s] == 1:
                services[s] = 0
            else:
                services[s] = 1

    # ===== GÁN LOGIC HOẠT ĐỘNG (HD) =====
    activities = {a: 0 for a in ACTIVITIES}

    if destination in BEACH:
        if random.random() < 0.85:
            activities['HD_Tam_Bien'] = 1

    if destination in MOUNTAIN:
        if random.random() < 0.75:
            activities['HD_Leo_Nui_Trekking'] = 1

    if destination in CULTURE or age_group in ['46-55', '55+']:
        if random.random() < 0.7:
            activities['HD_Tham_Quan_Di_Tich'] = 1

    # Gen Z và Millennials cực thích Check-in và Chữa lành
    if age_group in ['18-25', '26-35']:
        if random.random() < 0.8:
            activities['HD_Check_In'] = 1
        if budget_level in ['medium', 'high'] and random.random() < 0.6:
            activities['HD_Nghi_Duong_Chua_Lanh'] = 1

    # 90% khách sẽ có hoạt động ẩm thực
    if random.random() < 0.9:
        activities['HD_Am_Thuc'] = 1

    # ===== BƠM NHIỄU (NOISE) CHO HOẠT ĐỘNG =====
    for a in ACTIVITIES:
        if random.random() < 0.08:  # Nhiễu 8% cho hoạt động
            if activities[a] == 1:
                activities[a] = 0
            else:
                activities[a] = 1

    # Bắt lỗi: Nếu nhiễu làm mất sạch hoạt động, gán ngẫu nhiên lại 1 cái
    total_activities = 0
    for a in ACTIVITIES:
        if activities[a] == 1:
            total_activities += 1
            
    if total_activities == 0:
        random_act = random.choice(ACTIVITIES)
        activities[random_act] = 1

    # ===== ĐÁNH GIÁ (RATING) =====
    base_rating = 3.5
    if services['DV_Khach_San_Homestay'] == 1 and budget_level == 'high':
        base_rating = base_rating + 0.5
    if services['DV_Dua_Don_San_Bay'] == 1: 
        base_rating = base_rating + 0.3

    rating = base_rating + random.uniform(-1.2, 1.2)
    if rating < 1.0:
        rating = 1.0
    if rating > 5.0:
        rating = 5.0
    rating = round(rating * 2) / 2 # Làm tròn bậc 0.5 sao

    # ===== ĐÓNG GÓI RECORD =====
    record = {
        'tourist_id': f'KH{i:04d}',
        'gioi_tinh': gender,
        'nhom_tuoi': age_group,
        'muc_dich': purpose,
        'so_nguoi': group_size,
        'ngan_sach_trieu': budget,
        'so_ngay': days,
        'mua': season,
        'dia_diem': destination,
        'kenh_dat': booking_channel,
        'danh_gia': rating,
        'khach_quay_lai': random.choice([0, 1])
    }

    record.update(services)
    record.update(activities)

    # Gom thành mảng String để dễ visualize lúc phân tích
    services_list = []
    for s in SERVICES:
        if services[s] == 1:
            services_list.append(s)
            
    activities_list = []
    for a in ACTIVITIES:
        if activities[a] == 1:
            activities_list.append(a)

    record['services_list'] = ",".join(services_list)
    record['activities_list'] = ",".join(activities_list)

    return record

# ================== MAIN EXECUTION ==================
if __name__ == "__main__":
    print("Đang khởi tạo 5000 dòng dữ liệu, thằng anh đợi xíu...")
    
    # Số lượng dữ liệu 5000 dòng theo yêu cầu
    NUM_RECORDS = 5000
    
    records = []
    for i in range(1, NUM_RECORDS + 1):
        records.append(generate_record(i))
        
    df = pd.DataFrame(records)

    current_dir = os.getcwd()
    csv_path = os.path.join(current_dir, "tourism_dataset_5k.csv")
    xlsx_path = os.path.join(current_dir, "tourism_dataset_5k.xlsx")

    df.to_csv(csv_path, index=False, encoding='utf-8')
    df.to_excel(xlsx_path, index=False)

    print("DONE! DỮ LIỆU ĐÃ LÊN LÒ!")
    print(f"Tổng số dòng: {len(df)}")
    print("CSV Path:", csv_path)
    print("XLSX Path:", xlsx_path)