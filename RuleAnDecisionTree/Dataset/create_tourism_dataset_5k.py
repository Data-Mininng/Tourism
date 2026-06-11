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

SERVICES = [
    'DV_Khach_San_Homestay',   # Gọi API Booking.com
    'DV_Ve_May_Bay',           # Gọi API Google Flights
    'DV_Dua_Don_San_Bay',      # Tự build DB nội bộ
    'DV_Tour_Va_Khu_Vui_Choi', # Gọi API Tripadvisor/Viator
    'DV_Thue_Xe_Tu_Lai'        # Gọi API Booking Car Rental
]

ACTIVITIES = [
    'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
    'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh'
]

# Thêm các mảng hỗ trợ cho Log Frontend tương ứng bảng GiaoDich
DEPARTURES = ['Ha_Noi', 'HCMC', 'Da_Nang', 'Hai_Phong', 'Can_Tho']
AIRLINES = ['Vietnam_Airlines', 'VietJet_Air', 'Bamboo_Airways', 'Vietravel_Airlines', 'None']
HOTEL_TYPES = ['Homestay', 'Hotel_3_Star', 'Hotel_4_Star', 'Resort_5_Star']

def generate_record(record_id):
    # 1. Sinh các thuộc tính ngữ cảnh (Categorical) cơ bản
    destination = random.choice(DESTINATIONS)
    season = random.choice(['Mua_Xuan', 'Mua_Ha', 'Mua_Thu', 'Mua_Dong'])
    purpose = random.choice(['Nghi_Duong', 'Kham_Pha', 'Cong_Tac', 'Trang_Mat'])
    age_group = random.choice(['18_24', '25_34', '35_44', '45_54', 'Tren_55'])
    gender = random.choice(['Nam', 'Nu'])
    booking_channel = random.choice(['Website', 'Mobile_App', 'Zalo_OA', 'Truc_Tiep'])
    
    # 2. Sinh các thuộc tính ngữ cảnh bổ sung khớp với Log Frontend gửi sang
    departure = random.choice(DEPARTURES)
    # Nếu điểm đi trùng điểm đến thì ép đi bằng xe/hình thức khác (Không có hãng hàng không)
    airline = random.choice(AIRLINES[:-1]) if departure != destination else 'None'
    hotel_type = random.choice(HOTEL_TYPES)
    has_pool = 1 if hotel_type in ['Hotel_4_Star', 'Resort_5_Star'] and random.random() < 0.85 else 0

    # 3. Sinh các biến số học logic dựa trên Ngữ cảnh
    if purpose == 'Nghi_Duong' or hotel_type == 'Resort_5_Star':
        budget = round(random.uniform(15.0, 45.0), 1)
        days = random.randint(3, 7)
    else:
        budget = round(random.uniform(3.0, 14.9), 1)
        days = random.randint(1, 4)

    people = random.choice([1, 2, 2, 2, 3, 4, 5]) # Xu hướng đi 2 người hoặc gia đình
    rating = random.choice([3, 4, 4, 5, 5])       # Xu hướng đánh giá tốt

    # =====================================================================
    # CÂN BẰNG LẠI XÁC SUẤT HÀNH VI (Đã hạ nhiệt HD_Am_Thuc và phân phối theo địa điểm)
    # =====================================================================
    services = {s: 0 for s in SERVICES}
    activities = {a: 0 for a in ACTIVITIES}

    # --- KHỐI LOGIC CHO HOẠT ĐỘNG (ACTIVITIES) ---
    activities['HD_Am_Thuc'] = 1 if random.random() < 0.40 else 0

    if destination in ['Da_Nang', 'Nha_Trang', 'Phu_Quoc', 'Mui_Ne']:
        activities['HD_Tam_Bien'] = 1 if random.random() < 0.85 else 0
        activities['HD_Check_In'] = 1 if random.random() < 0.60 else 0
        if purpose == 'Nghi_Duong':
            activities['HD_Nghi_Duong_Chua_Lanh'] = 1 if random.random() < 0.75 else 0
            
    elif destination in ['Sapa', 'Da_Lat']:
        activities['HD_Leo_Nui_Trekking'] = 1 if random.random() < 0.80 else 0
        activities['HD_Check_In'] = 1 if random.random() < 0.75 else 0
        if season in ['Mua_Thu', 'Mua_Dong']:
            activities['HD_Nghi_Duong_Chua_Lanh'] = 1 if random.random() < 0.60 else 0
            
    elif destination in ['Ha_Long', 'Hoi_An', 'Hue', 'Ha_Noi', 'HCMC']:
        activities['HD_Tham_Quan_Di_Tich'] = 1 if random.random() < 0.85 else 0
        activities['HD_Am_Thuc'] = 1 if random.random() < 0.65 else 0 

    # --- KHỐI LOGIC CHO DỊCH VỤ (SERVICES) ---
    if hotel_type in ['Hotel_4_Star', 'Resort_5_Star'] or purpose == 'Nghi_Duong':
        services['DV_Khach_San_Homestay'] = 1 if random.random() < 0.90 else 0
    else:
        services['DV_Khach_San_Homestay'] = 1 if random.random() < 0.50 else 0

    if (departure == 'Ha_Noi' and destination in ['Phu_Quoc', 'HCMC', 'Nha_Trang', 'Da_Nang', 'Mui_Ne']) or \
       (departure == 'HCMC' and destination in ['Ha_Noi', 'Ha_Long', 'Sapa', 'Hue', 'Da_Nang']):
        services['DV_Ve_May_Bay'] = 1 if random.random() < 0.85 else 0
    else:
        services['DV_Ve_May_Bay'] = 1 if random.random() < 0.20 else 0

    if services['DV_Ve_May_Bay'] == 1:
        services['DV_Dua_Don_San_Bay'] = 1 if random.random() < 0.75 else 0

    if age_group in ['25_34', '35_44'] and budget >= 10.0:
        services['DV_Thue_Xe_Tu_Lai'] = 1 if random.random() < 0.60 else 0

    if purpose == 'Kham_Pha' or destination in ['Phu_Quoc', 'Nha_Trang', 'Ha_Long']:
        services['DV_Tour_Va_Khu_Vui_Choi'] = 1 if random.random() < 0.70 else 0

    # =====================================================================

    # 4. Gom dữ liệu khớp thuộc tính cấu trúc cũ
    record = {
        'id': record_id,
        'ngan_sach_trieu': budget,
        'so_ngay': days,
        'so_nguoi': people,
        'muc_dich': purpose,
        'nhom_tuoi': age_group,
        'gioi_tinh': gender,
        'mua': season,
        'dia_diem': destination,
        'kenh_dat': booking_channel,
        'danh_gia': rating,
        'khach_quay_lai': random.choice([0, 1]),
        
        'tu_den': departure,
        'hang_hang_khong': airline,
        'loai_khach_san': hotel_type,
        'ho_boi': has_pool
    }

    record.update(services)
    record.update(activities)

    services_list = [s for s in SERVICES if services[s] == 1]
    activities_list = [a for a in ACTIVITIES if activities[a] == 1]
    record['services_list'] = ",".join(services_list)
    record['activities_list'] = ",".join(activities_list)

    return record

# ================== THỰC THI CHƯƠNG TRÌNH ==================
if __name__ == "__main__":
    print("--- [BẮT ĐẦU] Khởi tạo 5000 dòng dữ liệu du lịch đã cân bằng hành vi ---")
    
    NUM_RECORDS = 5000
    records = [generate_record(i) for i in range(1, NUM_RECORDS + 1)]
        
    df = pd.DataFrame(records)

    # Định vị chính xác thư mục dataset/ để lưu file ra đúng chỗ
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_filename = os.path.join(current_dir, "tourism_dataset_5k.csv")
    
    # CHỈ XUẤT FILE CSV THUẦN TÚY, BỎ HẾT PHẦN TO_SQL ĐẨY VÀO DATABASE
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    
    print("==================================================")
    print(f"[XUẤT FILE THÀNH CÔNG]")
    print(f"Đã tạo xong file CSV tại: {csv_filename}")
    print("Không thực hiện ghi tự động vào CSDL. Sẵn sàng cho file preprocess.py xử lý!")