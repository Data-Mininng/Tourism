import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
import os

def _discretize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Biến đổi dữ liệu thô từ CSV/Database thành ma trận nhị phân True/False.
    Tự động chuẩn hóa nhãn theo đúng định dạng chuỗi ngữ cảnh.
    """
    result = pd.DataFrame(index=df.index)

    # 1. Các cột nhị phân dịch vụ & hoạt động có sẵn
    binary_cols = [
        'DV_Khach_San_Homestay', 'DV_Ve_May_Bay', 'DV_Dua_Don_San_Bay',
        'DV_Tour_Va_Khu_Vui_Choi', 'DV_Thue_Xe_Tu_Lai',
        'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
        'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh',
    ]
    for col in binary_cols:
        if col in df.columns:
            result[col] = df[col].astype(bool)

    # 2. Xử lý tự động biến chữ (Categorical) - Áp map tiền tố chuẩn
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
                # Xử lý trường hợp giá trị dạng số 0/1 của cột ho_boi hoặc chứa tiền tố sẵn
                if val_str in ['1', '1.0', 'True']:
                    result[f"Co_{prefix}"] = (df[col].astype(str).str.startswith(('1', 'True')))
                elif val_str in ['0', '0.0', 'False']:
                    result[f"Khong_{prefix}"] = (df[col].astype(str).str.startswith(('0', 'False')))
                elif val_str.startswith(("Co_", "Khong_")):
                    result[val_str] = (df[col] == val)
                else:
                    result[f"{prefix}_{val_str}"] = (df[col] == val)

    # 3. Rời rạc hóa các biến số học (Numerical) dựa trên giá trị thô gốc
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

def run_fpgrowth(df: pd.DataFrame, min_support: float = 0.02, min_confidence: float = 0.4) -> pd.DataFrame:
    """
    Hàm thực thi sinh luật kết hợp FP-Growth từ tập dữ liệu thô.
    """
    if df.empty:
        print("[⚠️ CẢNH BÁO] DataFrame rỗng, không thể chạy FP-Growth.")
        return pd.DataFrame()

    # Bước 1: Rời rạc hóa dữ liệu
    df_cleaned = _discretize(df)
    
    # Bước 2: Tìm tập phổ biến
    frequent_itemsets = fpgrowth(df_cleaned, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        print(f"[⚠️ KHÔNG CÓ LUẬT] Không tìm thấy tập phổ biến nào đạt ngưỡng support >= {min_support}")
        return pd.DataFrame()
        
    # Bước 3: Sinh luật liên kết
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    if rules.empty:
        print(f"[⚠️ KHÔNG CÓ LUẬT] Không sinh được luật nào đạt ngưỡng confidence >= {min_confidence}")
        return pd.DataFrame()

    # Bộ lọc vế phải chỉ giữ lại dịch vụ hoặc hoạt động gợi ý
    SERVICE_ITEMS = {
        'DV_Khach_San_Homestay', 'DV_Ve_May_Bay', 'DV_Dua_Don_San_Bay',
        'DV_Tour_Va_Khu_Vui_Choi', 'DV_Thue_Xe_Tu_Lai',
        'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
        'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh',
    }

    rules = rules[rules['consequents'].apply(lambda x: all(item in SERVICE_ITEMS for item in x))]
    
    if rules.empty:
        print("[⚠️ KHÔNG CÓ LUẬT] Không có luật nào có vế phải thuộc danh mục dịch vụ/hoạt động hợp lệ.")
        return pd.DataFrame()

    # Định dạng chuỗi frozenset thành chuỗi văn bản thuần
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ','.join(sorted(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ','.join(sorted(x)))

    # Định hình cấu trúc xuất ra khớp bảng Luat_FPGrowth trong hệ thống
    rules_db = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    rules_db.columns = ['DichVu_Goc', 'DichVu_GoiY', 'Do_Ho_Tro_Support', 'Do_Tin_Cay_Confidence', 'Do_Nang_Lift']

    print(f"[FPGrowth] Đã tạo thành công {len(rules_db)} luật ngữ cảnh chất lượng cao!")
    return rules_db

# Khối thực thi kiểm thử độc lập
# Khối thực thi kiểm thử độc lập (Sửa lại cơ chế quét file an toàn)
if __name__ == "__main__":
    print("\n--- [KIỂM THỬ ĐỘC LẬP] Đang chạy sinh luật mẫu từ file CSV gốc ---")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Thử nghiệm các đường dẫn có thể có của file dữ liệu 5k
    possible_paths = [
        os.path.abspath(os.path.join(current_dir, os.path.pardir, 'dataset', 'tourism_dataset_5k.csv')),
        os.path.abspath(os.path.join(current_dir, '..', 'dataset', 'tourism_dataset_5k.csv')),
        os.path.abspath(os.path.join(current_dir, 'tourism_dataset_5k.csv'))
    ]
    
    csv_raw_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_raw_path = path
            break

    if csv_raw_path:
        print(f"✅ Đã tìm thấy file dữ liệu gốc tại: {csv_raw_path}")
        df_raw = pd.read_csv(csv_raw_path)
        
        # BẮT BUỘC: Hạ min_support xuống 0.02 (2%) để bốc được địa điểm và mùa
        # Tăng min_confidence lên 0.4 (40%) để giữ luật chất lượng
        result_rules = run_fpgrowth(df_raw, min_support=0.02, min_confidence=0.4)
        
        if not result_rules.empty:
            print("\n🔥 TOP 20 LUẬT CÓ NGỮ CẢNH (ĐỊA ĐIỂM, MÙA, NGÂN SÁCH...) SINH RA:")
            print("==========================================================================")
            # Lọc xem các luật nào có chứa chữ 'Den_' hoặc 'Mua_' ở vế trái để hiển thị kiểm tra
            context_rules = result_rules[result_rules['DichVu_Goc'].str.contains('Den_|Mua_|NganSach_|MucDich_')]
            if not context_rules.empty:
                print(context_rules.head(20).to_string())
            else:
                print(result_rules.head(20).to_string())
            print("==========================================================================")
    else:
        print("❌ LỖI KHÔNG TÌM THẤY DATA: Bạn chưa chạy file 'create_tourism_dataset_5k.py' để tạo file csv gốc!")
        print("Vui lòng chạy lệnh: python dataset/create_tourism_dataset_5k.py trước nhé.")