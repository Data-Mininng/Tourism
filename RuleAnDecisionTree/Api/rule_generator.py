import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules

def _discretize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Biến đổi dữ liệu thô từ Database thành ma trận nhị phân True/False.
    Tự động chuẩn hóa nhãn theo đúng định dạng chuỗi của Frontend gửi sang API.
    """
    result = pd.DataFrame(index=df.index)

    # 1. Các cột nhị phân có sẵn (Dịch vụ & Hoạt động)
    binary_cols = [
        'DV_Khach_San_Homestay', 'DV_Ve_May_Bay', 'DV_Dua_Don_San_Bay',
        'DV_Tour_Va_Khu_Vui_Choi', 'DV_Thue_Xe_Tu_Lai',
        'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
        'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh',
    ]
    for col in binary_cols:
        if col in df.columns:
            result[col] = df[col].astype(bool)

    # 2. Xử lý tự động biến chữ (Categorical) - Áp map tiền tố chuẩn khớp cấu trúc log
    mapping_prefixes = {
        'dia_diem': 'Den',
        'mua': 'Mua',
        'muc_dich': 'MucDich',
        'nhom_tuoi': 'NhomTuoi',
        'gioi_tinh': 'GioiTinh',
        'kenh_dat': 'KenhDat',
        'tu_den': 'TuDen',
        'hang_hang_khong': 'Hang',
        'loai_khach_san': 'KhachSan',
        'ho_boi': 'HoBoi'
    }

    for col, prefix in mapping_prefixes.items():
        if col in df.columns:
            for val in df[col].dropna().unique():
                val_str = str(val).strip()
                # Nếu giá trị trong DB đã chứa sẵn chữ "Co_" hoặc "Khong_" (như Co_Ho_Boi) thì giữ nguyên nhãn nguyên bản
                if val_str.startswith(("Co_", "Khong_")):
                    result[val_str] = (df[col] == val)
                else:
                    result[f"{prefix}_{val_str}"] = (df[col] == val)

    # 3. Rời rạc hóa các biến số học (Numerical)
    if 'ngan_sach_trieu' in df.columns:
        result['NganSach_Thap'] = df['ngan_sach_trieu'] < 5
        result['NganSach_Trung_Binh'] = (df['ngan_sach_trieu'] >= 5) & (df['ngan_sach_trieu'] <= 15)
        result['NganSach_Cao'] = df['ngan_sach_trieu'] > 15

    if 'so_ngay' in df.columns:
        result['SoNgay_Ngan'] = df['so_ngay'] <= 3
        result['SoNgay_TrungBinh'] = (df['so_ngay'] > 3) & (df['so_ngay'] <= 7)
        result['SoNgay_Dai'] = df['so_ngay'] > 7

    if 'so_nguoi' in df.columns:
        result['SoNguoi_Solo'] = df['so_nguoi'] == 1
        result['SoNguoi_CapDoi'] = df['so_nguoi'] == 2
        result['SoNguoi_DoanGroup'] = df['so_nguoi'] > 2

    if 'danh_gia' in df.columns:
        result['DanhGia_Cao'] = df['danh_gia'] >= 4

    if 'khach_quay_lai' in df.columns:
        result['Khach_QuayLai'] = df['khach_quay_lai'].astype(bool)

    return result

def run_fpgrowth(df: pd.DataFrame, min_support: float, min_confidence: float) -> pd.DataFrame:
    # Bước 1: Rời rạc hóa toàn bộ dữ liệu ngữ cảnh + dịch vụ
    df_cleaned = _discretize(df)
    
    # Bước 2: Chạy thuật toán tìm tập phổ biến
    frequent_itemsets = fpgrowth(df_cleaned, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        return pd.DataFrame()
        
    # Bước 3: Sinh luật liên kết từ tập phổ biến
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    if rules.empty:
        return pd.DataFrame()

    # Tập hợp các dịch vụ/hoạt động hợp lệ để hiển thị đề xuất ở vế phải
    SERVICE_ITEMS = {
        'DV_Khach_San_Homestay', 'DV_Ve_May_Bay', 'DV_Dua_Don_San_Bay',
        'DV_Tour_Va_Khu_Vui_Choi', 'DV_Thue_Xe_Tu_Lai',
        'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
        'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh',
    }

    # SỬA LỖI LOGIC: Chỉ lọc vế phải (consequents) bắt buộc nằm trong tập SERVICE_ITEMS.
    # Vế trái (antecedents) giữ nguyên toàn bộ để cho phép gom luật từ địa điểm, ngân sách, mùa...
    rules = rules[rules['consequents'].apply(lambda x: all(item in SERVICE_ITEMS for item in x))]
    
    if rules.empty:
        return pd.DataFrame()

    # Chuyển đổi dữ liệu từ tập hợp (frozenset) sang chuỗi ngăn cách bằng dấu phẩy thuần (KHÔNG khoảng trắng)
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ','.join(sorted(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ','.join(sorted(x)))

    # Định hình cấu trúc xuất ra khớp bảng Luat_FPGrowth trong SQL Server
    rules_db = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    rules_db.columns = ['DichVu_Goc', 'DichVu_GoiY', 'Do_Ho_Tro_Support', 'Do_Tin_Cay_Confidence', 'Do_Nang_Lift']

    print(f"[FPGrowth] Đã tạo thành công {len(rules_db)} luật ngữ cảnh chất lượng cao!")
    return rules_db