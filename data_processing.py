import pandas as pd
import os

# Tự động lấy đường dẫn cùng thư mục chứa file code
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Tourism_Dataset")

def load_and_merge_data():
    try:
        # TỐI ƯU: Chỉ định thẳng engine='c' (mặc định) và sep=',' sẽ nhanh hơn rất nhiều so với engine='python' & sep=None
        # Thêm on_bad_lines='skip' để bỏ qua các dòng lỗi (nếu có) thay vì crash chương trình
        read_kwargs = {'encoding': 'latin-1', 'on_bad_lines': 'skip'}
        
        transaction = pd.read_csv(os.path.join(DATA_DIR, "Transaction.csv"), **read_kwargs)
        user        = pd.read_csv(os.path.join(DATA_DIR, "User.csv"), **read_kwargs)
        item        = pd.read_csv(os.path.join(DATA_DIR, "Item.csv"), **read_kwargs)
        city        = pd.read_csv(os.path.join(DATA_DIR, "City.csv"), **read_kwargs)
        country     = pd.read_csv(os.path.join(DATA_DIR, "Country.csv"), **read_kwargs)
        region      = pd.read_csv(os.path.join(DATA_DIR, "Region.csv"), **read_kwargs)
        mode        = pd.read_csv(os.path.join(DATA_DIR, "Mode.csv"), **read_kwargs)
        attr_type   = pd.read_csv(os.path.join(DATA_DIR, "Type.csv"), **read_kwargs)

        # CHUẨN HÓA KHOẢNG TRẮNG
        all_dfs = [transaction, user, item, city, country, region, mode, attr_type]
        for d in all_dfs:
            d.columns = d.columns.str.strip()
            # TỐI ƯU: Chỉ strip các cột có kiểu object để tránh lỗi ép kiểu
            obj_cols = d.select_dtypes(include=['object']).columns
            for col in obj_cols:
                d[col] = d[col].astype(str).str.strip()

        # ÉP KIỂU STRING CHO CÁC KHÓA
        transaction['UserId']       = transaction['UserId'].astype(str)
        transaction['AttractionId'] = transaction['AttractionId'].astype(str)
        transaction['VisitMode']    = transaction['VisitMode'].astype(str)
        user['UserId']              = user['UserId'].astype(str)
        user['CityId']              = user['CityId'].astype(str)
        city['CityId']              = city['CityId'].astype(str)
        city['CountryId']           = city['CountryId'].astype(str)
        country['CountryId']        = country['CountryId'].astype(str)
        country['RegionId']         = country['RegionId'].astype(str)
        region['RegionId']          = region['RegionId'].astype(str)
        item['AttractionId']        = item['AttractionId'].astype(str)
        item['AttractionTypeId']    = item['AttractionTypeId'].astype(str)
        attr_type['AttractionTypeId'] = attr_type['AttractionTypeId'].astype(str)
        mode['VisitModeId']         = mode['VisitModeId'].astype(str)

        # LÀM SẠCH GIAO DỊCH
        transaction.dropna(subset=['UserId', 'AttractionId'], inplace=True)
        transaction.drop_duplicates(inplace=True)
        transaction['Rating'] = pd.to_numeric(transaction['Rating'], errors='coerce')

        # BINNING RATING
        def binning_rating(r):
            if pd.isna(r): return 'Không xác định' # TỐI ƯU: Xử lý rỗng
            if r >= 4.5: return 'Xuất sắc'
            if r >= 3.5: return 'Tốt'
            return 'Trung bình'
        transaction['Rating_Level'] = transaction['Rating'].apply(binning_rating)

        # MERGE DỮ LIỆU
        df = transaction.merge(user[['UserId', 'CityId']], on='UserId', how='left')
        df = df.merge(city[['CityId', 'CityName', 'CountryId']], on='CityId', how='left')
        df = df.merge(country[['CountryId', 'Country', 'RegionId']], on='CountryId', how='left')
        df = df.merge(region[['RegionId', 'Region']], on='RegionId', how='left')
        df = df.merge(item[['AttractionId', 'Attraction', 'AttractionTypeId']], on='AttractionId', how='left')
        df = df.merge(attr_type[['AttractionTypeId', 'AttractionType']], on='AttractionTypeId', how='left')
        df = df.merge(mode[['VisitModeId', 'VisitMode']], left_on='VisitMode', right_on='VisitModeId', how='left')

        df.rename(columns={
            'CityName': 'City',
            'AttractionType': 'Type',
            'VisitMode_y': 'TravelMode'
        }, inplace=True)

        return df

    except Exception as e:
        print(f"[LỖI CRITICAL] load_and_merge_data: {e}")
        return None

def get_cleaned_features(df):
    if df is None or df.empty:
        return None

    keep_cols = ['UserId', 'TravelMode', 'Attraction', 'Type', 'Rating_Level', 'Rating']
    actual_cols = [c for c in keep_cols if c in df.columns]

    df_clean = df[actual_cols].copy()
    df_clean.dropna(inplace=True)
    
    # Lọc bỏ các dòng lỗi Rating
    df_clean = df_clean[df_clean['Rating_Level'] != 'Không xác định']

    print(f"[INFO] Sau làm sạch: {df_clean.shape[0]} dòng hợp lệ")
    return df_clean