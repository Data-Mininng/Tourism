import pandas as pd
from data_processing import load_and_merge_data, get_cleaned_features

print("Bắt đầu đọc và gộp 9 file dữ liệu gốc...")
raw_df = load_and_merge_data()

if raw_df is not None and not raw_df.empty:
    clean_df = get_cleaned_features(raw_df)
    
    print(f"Đã gộp xong! Tổng số dòng: {clean_df.shape[0]}")
    print("Đang tiến hành Việt hóa dữ liệu...")
    
    # TỐI ƯU: Sử dụng .replace() thay vì .map().fillna()
    travel_mode_dict = {
        'Solo': 'Đi một mình',
        'Family': 'Gia đình',
        'Couples': 'Cặp đôi',
        'Friends': 'Bạn bè',
        'Business': 'Công tác'
    }
    clean_df['TravelMode'] = clean_df['TravelMode'].replace(travel_mode_dict)
    
    rating_dict = {
        'Excellent': 'Xuất sắc',
        'Good': 'Tốt',
        'Average': 'Trung bình'
    }
    clean_df['Rating_Level'] = clean_df['Rating_Level'].replace(rating_dict)
    
    type_dict = {
        'Historical': 'Lịch sử',
        'Nature': 'Thiên nhiên',
        'Entertainment': 'Giải trí',
        'Shopping': 'Mua sắm',
        'Cultural': 'Văn hóa',
        'Religious': 'Tôn giáo'
    }
    clean_df['Type'] = clean_df['Type'].replace(type_dict)
    
    # Lưu file
    output_file = "DuLieu_DaLamSach_TiengViet.csv"
    clean_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"🎉 Đã lưu thành công file: {output_file}")
else:
    print("Có lỗi xảy ra khi gộp dữ liệu hoặc dữ liệu rỗng.")