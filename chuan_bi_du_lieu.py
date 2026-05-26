import pandas as pd
from data_processing import load_and_merge_data, get_cleaned_features

print("Bắt đầu đọc và gộp 9 file dữ liệu gốc...")
# 1. Lấy dữ liệu đã gộp từ code cũ của bạn
raw_df = load_and_merge_data()

if raw_df is not None:
    # 2. Lấy các cột quan trọng
    clean_df = get_cleaned_features(raw_df)
    
    print(f"Đã gộp xong! Tổng số dòng: {clean_df.shape[0]}")
    
    # 3. TIẾN HÀNH VIỆT HÓA (Dịch các nhãn trong cột)
    print("Đang tiến hành Việt hóa dữ liệu...")
    
    # Dịch cột Hình thức đi (TravelMode)
    travel_mode_dict = {
        'Solo': 'Đi một mình',
        'Family': 'Gia đình',
        'Couples': 'Cặp đôi',
        'Friends': 'Bạn bè',
        'Business': 'Công tác'
    }
    clean_df['TravelMode'] = clean_df['TravelMode'].map(travel_mode_dict).fillna(clean_df['TravelMode'])
    
    # Dịch cột Đánh giá (Rating_Level) - dựa theo hàm binning_rating của bạn
    rating_dict = {
        'Excellent': 'Xuất sắc',
        'Good': 'Tốt',
        'Average': 'Trung bình'
    }
    clean_df['Rating_Level'] = clean_df['Rating_Level'].map(rating_dict).fillna(clean_df['Rating_Level'])
    
    # Dịch loại hình tham quan (Type) (Bạn có thể bổ sung thêm từ điển này tùy theo dữ liệu thực tế)
    type_dict = {
        'Historical': 'Lịch sử',
        'Nature': 'Thiên nhiên',
        'Entertainment': 'Giải trí',
        'Shopping': 'Mua sắm',
        'Cultural': 'Văn hóa',
        'Religious': 'Tôn giáo'
        # Thêm các loại hình khác có trong file Type.csv của bạn
    }
    clean_df['Type'] = clean_df['Type'].map(type_dict).fillna(clean_df['Type'])
    
    # 4. LƯU THÀNH FILE MỚI ĐỂ SỬ DỤNG CHO WEB
    output_file = "DuLieu_DaLamSach_TiengViet.csv"
    clean_df.to_csv(output_file, index=False, encoding='utf-8-sig') # Dùng utf-8-sig để Excel đọc tiếng Việt không bị lỗi font
    print(f"🎉 Đã lưu thành công file: {output_file}")
    
else:
    print("Có lỗi xảy ra khi gộp dữ liệu.")