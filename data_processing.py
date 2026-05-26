"""
=============================================================
FILE: data_processing.py
MỤC ĐÍCH: Đọc, làm sạch và tích hợp 9 file dữ liệu thành 1 bảng duy nhất
=============================================================
"""

import pandas as pd
import os

# Thư mục chứa 9 file CSV gốc
DATA_DIR = "Tourism_Dataset"


def load_and_merge_data():
    """
    BƯỚC 1: ĐỌC & TÍCH HỢP DỮ LIỆU (Data Integration)
    ====================================================
    Vấn đề: Dữ liệu bị phân tán trong 9 file riêng lẻ.
    Giải pháp: Dùng kỹ thuật MERGE (như SQL JOIN) để gộp lại
    theo sơ đồ quan hệ:
    
    Transaction → User → City → Country → Region
         ↓
       Item → Type
         ↓
        Mode
    """
    try:
        # --- ĐỌC DỮ LIỆU ---
        # sep=None + engine='python': tự động nhận diện dấu phân cách (,  hay ;  hay tab)
        # encoding='latin-1': đọc được ký tự đặc biệt trong tên địa danh
        transaction = pd.read_csv(os.path.join(DATA_DIR, "Transaction.csv"), sep=None, engine='python', encoding='latin-1')
        user        = pd.read_csv(os.path.join(DATA_DIR, "User.csv"),        sep=None, engine='python', encoding='latin-1')
        item        = pd.read_csv(os.path.join(DATA_DIR, "Item.csv"),        sep=None, engine='python', encoding='latin-1')
        city        = pd.read_csv(os.path.join(DATA_DIR, "City.csv"),        sep=None, engine='python', encoding='latin-1')
        country     = pd.read_csv(os.path.join(DATA_DIR, "Country.csv"),     sep=None, engine='python', encoding='latin-1')
        region      = pd.read_csv(os.path.join(DATA_DIR, "Region.csv"),      sep=None, engine='python', encoding='latin-1')
        mode        = pd.read_csv(os.path.join(DATA_DIR, "Mode.csv"),        sep=None, engine='python', encoding='latin-1')
        attr_type   = pd.read_csv(os.path.join(DATA_DIR, "Type.csv"),        sep=None, engine='python', encoding='latin-1')

        # --- CHUẨN HÓA ---
        # Xóa khoảng trắng thừa trong tên cột và giá trị chuỗi
        # Ví dụ: "UserId  " → "UserId", "  Beaches" → "Beaches"
        all_dfs = [transaction, user, item, city, country, region, mode, attr_type]
        for d in all_dfs:
            d.columns = d.columns.str.strip()
            for col in d.select_dtypes(include='object').columns:
                d[col] = d[col].astype(str).str.strip()

        # --- ÉP KIỂU KHÓA NGOẠI VỀ STRING ---
        # Lý do: "001" (string) ≠ 1 (integer) → merge sẽ bị mất dữ liệu nếu không thống nhất
        transaction['UserId']      = transaction['UserId'].astype(str)
        transaction['AttractionId']= transaction['AttractionId'].astype(str)
        transaction['VisitMode']   = transaction['VisitMode'].astype(str)
        user['UserId']             = user['UserId'].astype(str)
        user['CityId']             = user['CityId'].astype(str)
        city['CityId']             = city['CityId'].astype(str)
        city['CountryId']          = city['CountryId'].astype(str)
        country['CountryId']       = country['CountryId'].astype(str)
        country['RegionId']        = country['RegionId'].astype(str)
        region['RegionId']         = region['RegionId'].astype(str)
        item['AttractionId']       = item['AttractionId'].astype(str)
        item['AttractionTypeId']   = item['AttractionTypeId'].astype(str)
        attr_type['AttractionTypeId'] = attr_type['AttractionTypeId'].astype(str)
        mode['VisitModeId']        = mode['VisitModeId'].astype(str)

        # --- LÀM SẠCH BẢNG TRANSACTION ---
        transaction.dropna(subset=['UserId', 'AttractionId'], inplace=True)   # Xóa dòng thiếu khóa
        transaction.drop_duplicates(inplace=True)                              # Xóa dòng trùng lặp
        transaction['Rating'] = pd.to_numeric(transaction['Rating'], errors='coerce')  # Ép về số

        # --- RỜI RẠC HÓA RATING (Discretization) ---
        # Chuyển số thực (1-5) → nhãn phân loại để FP-Growth có thể xử lý
        # Kỹ thuật này gọi là "Binning" (phân khoảng)
        def binning_rating(r):
            if r >= 4.5: return 'Xuất sắc'   # 4.5 → 5.0
            if r >= 3.5: return 'Tốt'         # 3.5 → 4.4
            return 'Trung bình'               # 1.0 → 3.4
        transaction['Rating_Level'] = transaction['Rating'].apply(binning_rating)

        # --- TÍCH HỢP ĐA TẦNG (Multi-level Merge) ---
        # Mỗi bước là 1 LEFT JOIN: giữ toàn bộ Transaction, bổ sung thêm thông tin
        df = transaction.merge(user[['UserId', 'CityId']], on='UserId', how='left')
        df = df.merge(city[['CityId', 'CityName', 'CountryId']], on='CityId', how='left')
        df = df.merge(country[['CountryId', 'Country', 'RegionId']], on='CountryId', how='left')
        df = df.merge(region[['RegionId', 'Region']], on='RegionId', how='left')
        df = df.merge(item[['AttractionId', 'Attraction', 'AttractionTypeId']], on='AttractionId', how='left')
        df = df.merge(attr_type[['AttractionTypeId', 'AttractionType']], on='AttractionTypeId', how='left')
        df = df.merge(mode[['VisitModeId', 'VisitMode']], left_on='VisitMode', right_on='VisitModeId', how='left')

        # Đặt lại tên cột cho rõ nghĩa
        df.rename(columns={
            'CityName': 'City',
            'AttractionType': 'Type',
            'VisitMode_y': 'TravelMode'
        }, inplace=True)

        return df

    except Exception as e:
        print(f"[LỖI] load_and_merge_data: {e}")
        return None


def get_cleaned_features(df):
    """
    BƯỚC 2: TRÍCH XUẤT ĐẶC TRƯNG (Feature Selection)
    ==================================================
    Chỉ giữ lại các cột CÓ Ý NGHĨA cho khai phá dữ liệu.
    Loại bỏ các cột nhiễu như ID, tọa độ, địa chỉ chi tiết...
    """
    if df is None:
        return None

    keep_cols = ['UserId', 'TravelMode', 'Attraction', 'Type', 'Rating_Level', 'Rating']
    actual_cols = [c for c in keep_cols if c in df.columns]

    df_clean = df[actual_cols].copy()
    df_clean.dropna(inplace=True)  # Xóa dòng có giá trị NULL

    print(f"[INFO] Sau làm sạch: {df_clean.shape[0]} dòng hợp lệ")
    return df_clean