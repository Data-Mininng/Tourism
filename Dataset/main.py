import pandas as pd
import numpy as np
import random
import os

np.random.seed(42)
random.seed(42)

# ================== DATA ==================

DESTINATIONS = [
    'Ha_Long', 'Da_Nang', 'Hoi_An', 'Sapa', 'Nha_Trang',
    'Phu_Quoc', 'Da_Lat', 'Hue', 'HCMC', 'Ha_Noi', 'Mui_Ne'
]

# ĐÃ TINH CHỈNH: Gộp nhóm Khách sạn, thêm các dịch vụ OTA cốt lõi (Vé máy bay, Đưa đón, Khu vui chơi, Tour)
SERVICES = [
    'DV_Khach_San_Resort',  # Gộp 5 sao, 3 sao, Resort
    'DV_Homestay_Glamping', # Cập nhật xu hướng Glamping
    'DV_Ve_May_Bay',        # Thêm mới
    'DV_Dua_Don_San_Bay',   # Thêm mới
    'DV_Ve_Khu_Vui_Choi',   # Thêm mới
    'DV_Tour_Trong_Ngay',   # Thay thế Tour_Tau_Thuyen để bao quát hơn
    'DV_Thue_Xe_Oto',
    'DV_Thue_Xe_Dien',      # Thay thế xe máy xăng
]

ACTIVITIES = [
    'HD_Tam_Bien',
    'HD_Leo_Nui_Trekking',
    'HD_Tham_Quan_Di_Tich',
    'HD_Mua_Sam',
    'HD_Am_Thuc',
    'HD_Chup_Anh_Check_In',
    'HD_The_Thao_Nuoc',
    'HD_Nghi_Duong_Chua_Lanh', # Cập nhật xu hướng "Chữa lành"
]

TRIP_PURPOSES = ['Gia_Dinh', 'Tuan_Trang_Mat', 'Di_Mot_Minh', 'Ban_Be', 'Cong_Tac', 'Kham_Pha']
SEASONS = ['Xuan', 'Ha', 'Thu', 'Dong']
AGE_GROUPS = ['18-25', '26-35', '36-45', '46-55', '55+']
BOOKING_CHANNELS = ['Website_OTA', 'Truc_Tiep', 'App_Di_Dong', 'Super_App_Vi_Dien_Tu'] # Thêm Super App

# Phân loại địa lý có Sân Bay (QUAN TRỌNG cho logic Vé máy bay)
HAS_AIRPORT = ['Da_Nang', 'Nha_Trang', 'Phu_Quoc', 'Da_Lat', 'Hue', 'HCMC', 'Ha_Noi', 'Ha_Long']

BEACH = ['Nha_Trang', 'Phu_Quoc', 'Da_Nang', 'Mui_Ne', 'Ha_Long']
MOUNTAIN = ['Sapa', 'Da_Lat']
CULTURE = ['Hoi_An', 'Hue', 'Ha_Noi', 'HCMC']

# ================== LOGIC ==================

def choose_accommodation(budget_level):
    # Đơn giản hóa thành 2 lựa chọn lưu trú chính
    if budget_level in ['high', 'medium']:
        return 'DV_Khach_San_Resort'
    else:
        return 'DV_Homestay_Glamping'

def calculate_budget(destination, days, group_size, budget_level):
    if destination in ['Phu_Quoc', 'Ha_Long']:
        base = random.uniform(1.2, 2.5)
    elif destination in ['Da_Nang', 'Nha_Trang', 'Mui_Ne']:
        base = random.uniform(0.9, 2.0)
    elif destination in ['Sapa', 'Da_Lat']:
        base = random.uniform(0.7, 1.5)
    else:
        base = random.uniform(0.6, 1.3)

    if budget_level == 'high':
        mul = random.uniform(1.5, 2.5)
    elif budget_level == 'medium':
        mul = random.uniform(1.0, 1.5)
    else:
        mul = random.uniform(0.7, 1.0)

    total = base * days * group_size * mul
    total *= random.uniform(0.85, 1.2)

    return round(total, 1)

def generate_record(i):
    tourist_type = random.choice(['beach', 'mountain', 'culture', 'random'])
    budget_level = random.choice(['low', 'medium', 'high'])

    # ===== DESTINATION =====
    if tourist_type == 'beach':
        destination = random.choice(BEACH)
    elif tourist_type == 'mountain':
        destination = random.choice(MOUNTAIN)
    elif tourist_type == 'culture':
        destination = random.choice(CULTURE)
    else:
        destination = random.choice(DESTINATIONS)

    # ===== BASIC =====
    gender = random.choice(['Nam', 'Nu'])
    age_group = random.choice(AGE_GROUPS)
    purpose = random.choice(TRIP_PURPOSES)
    group_size = random.randint(1, 6)
    days = random.randint(2, 8)
    season = random.choice(SEASONS)
    booking_channel = random.choice(BOOKING_CHANNELS)

    # ===== BUDGET =====
    budget = calculate_budget(destination, days, group_size, budget_level)

    # ===== SERVICES (LOGIC CHÍNH) =====
    services = {s: 0 for s in SERVICES}

    # 1. Lưu trú (Luôn phải có)
    main_acc = choose_accommodation(budget_level)
    services[main_acc] = 1

    # 2. Vé máy bay & Đưa đón sân bay (Logic liên kết)
    if destination in HAS_AIRPORT:
        # Nếu điểm đến có sân bay, tỷ lệ mua vé rất cao
        if random.random() < 0.75:
            services['DV_Ve_May_Bay'] = 1
            # Đã mua vé máy bay -> Tỷ lệ cao mua đưa đón sân bay
            if random.random() < 0.65:
                services['DV_Dua_Don_San_Bay'] = 1

    # 3. Vé khu vui chơi (Phụ thuộc điểm đến có Theme Park)
    if destination in ['Phu_Quoc', 'Nha_Trang', 'Da_Nang', 'Ha_Long']:
        if random.random() < 0.6:
            services['DV_Ve_Khu_Vui_Choi'] = 1
    
    # 4. Tour trong ngày
    if destination in BEACH and random.random() < 0.5:
        services['DV_Tour_Trong_Ngay'] = 1 # Tour lặn đảo
    elif destination in MOUNTAIN and random.random() < 0.4:
        services['DV_Tour_Trong_Ngay'] = 1 # Tour trekking

    # 5. Thuê xe
    if destination in CULTURE or destination in MOUNTAIN:
        if random.random() < 0.3:
            services['DV_Thue_Xe_Dien'] = 1 # Thay thế xe máy
    
    if group_size >= 4 and random.random() < 0.2:
        services['DV_Thue_Xe_Oto'] = 1 # Nhóm đông thì thuê ô tô

    # TẠO NHIỄU (NOISE) CHỐNG OVERFITTING MỚI
    # Thay vì đảo lộn ngẫu nhiên hoàn toàn như code cũ,
    # Chỉ add/remove ngẫu nhiên với tỷ lệ rất thấp (3-5%) để giữ vững luật nhưng không tuyệt đối 100%
    for s in SERVICES:
        if random.random() < 0.04:  # Tỷ lệ nhiễu thấp hơn để không phá nát logic
            services[s] = 1 - services[s]
            
    # Đảm bảo không mất dịch vụ lưu trú do nhiễu
    if services['DV_Khach_San_Resort'] == 0 and services['DV_Homestay_Glamping'] == 0:
        services[main_acc] = 1

    # ===== ACTIVITIES =====
    activities = {a: 0 for a in ACTIVITIES}

    if destination in BEACH:
        if random.random() < 0.7:
            activities['HD_Tam_Bien'] = 1
        if random.random() < 0.5:
            activities['HD_The_Thao_Nuoc'] = 1

    if destination in MOUNTAIN:
        if random.random() < 0.6:
            activities['HD_Leo_Nui_Trekking'] = 1

    if destination in CULTURE:
        if random.random() < 0.6:
            activities['HD_Tham_Quan_Di_Tich'] = 1

    if age_group in ['18-25', '26-35'] and random.random() < 0.7:
        activities['HD_Chup_Anh_Check_In'] = 1

    if age_group in ['18-25', '26-35'] and budget_level in ['medium', 'high'] and random.random() < 0.5:
        activities['HD_Nghi_Duong_Chua_Lanh'] = 1

    for a in ACTIVITIES:
        if random.random() < 0.15: # Giảm nhiễu cho activities
            activities[a] = 1

    if sum(activities.values()) == 0:
        activities[random.choice(ACTIVITIES)] = 1

    # ===== RATING =====
    base = 3.5
    if services['DV_Khach_San_Resort'] == 1 and budget_level == 'high':
        base += 0.5
    if services['DV_Dua_Don_San_Bay'] == 1: # Khách được đón tận nơi thường đánh giá cao
        base += 0.2

    rating = base + random.uniform(-1, 1)
    rating = max(1, min(5, rating))
    rating = round(rating * 2) / 2

    # ===== RECORD =====
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

    # ===== CỘT MỚI (LIST) =====
    record['services_list'] = ",".join([s for s in SERVICES if services[s] == 1])
    record['activities_list'] = ",".join([a for a in ACTIVITIES if activities[a] == 1])

    return record


# ================== MAIN ==================

if __name__ == "__main__":
    # Nâng số dòng lên 1250 theo yêu cầu
    records = [generate_record(i) for i in range(1, 1251)]
    df = pd.DataFrame(records)

    current_dir = os.getcwd()

    csv_path = os.path.join(current_dir, "tourism_dataset_v2.csv")
    xlsx_path = os.path.join(current_dir, "tourism_dataset_v2.xlsx")

    df.to_csv(csv_path, index=False, encoding='utf-8')
    df.to_excel(xlsx_path, index=False)

    print("DONE. DATASET V2 GENERATED SUCESSFULLY.")
    print("CSV:", csv_path)
    print("XLSX:", xlsx_path)