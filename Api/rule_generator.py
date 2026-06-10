import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules


def _discretize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuyển toàn bộ thuộc tính thành cột nhị phân True/False để Apriori xử lý.
    Mỗi giá trị của biến chữ → 1 cột riêng.
    Biến số → chia bin rồi tạo cột.
    """
    result = pd.DataFrame(index=df.index)

    # ── 1. CỘT NHỊ PHÂN SẴN CÓ (0/1) ────────────────────────────────────
    binary_cols = [
        'DV_Khach_San_Homestay', 'DV_Ve_May_Bay', 'DV_Dua_Don_San_Bay',
        'DV_Tour_Va_Khu_Vui_Choi', 'DV_Thue_Xe_Tu_Lai',
        'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
        'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh',
    ]
    for col in binary_cols:
        if col in df.columns:
            result[col] = df[col].astype(bool)

    # ── 2. CỘT CHỮ → MỖI GIÁ TRỊ LÀ 1 ITEM ─────────────────────────────
    categorical_map = {
        'dia_diem':  'Den',      # Den_Ha_Long, Den_Da_Nang...
        'muc_dich':  'Muc',      # Muc_Gia_Dinh, Muc_Du_Lich...
        'mua':       'Mua',      # Mua_Xuan, Mua_Ha...
        'nhom_tuoi': 'Tuoi',     # Tuoi_18-25, Tuoi_26-35...
        'gioi_tinh': 'GT',       # GT_Nam, GT_Nu
        'kenh_dat':  'Kenh',     # Kenh_App_Di_Dong...
    }
    for col, prefix in categorical_map.items():
        if col not in df.columns:
            continue
        for val in df[col].dropna().unique():
            item_name = f"{prefix}_{str(val).replace(' ', '_').replace('-', '_')}"
            result[item_name] = (df[col] == val)

    # ── 3. NGÂN SÁCH → 3 BIN ──────────────────────────────────────────────
    if 'ngan_sach_trieu' in df.columns:
        result['NganSach_Thap']       = df['ngan_sach_trieu'] < 8
        result['NganSach_Trung_Binh'] = (df['ngan_sach_trieu'] >= 8) & (df['ngan_sach_trieu'] < 15)
        result['NganSach_Cao']        = df['ngan_sach_trieu'] >= 15

    # ── 4. SỐ NGÀY → 3 BIN ───────────────────────────────────────────────
    if 'so_ngay' in df.columns:
        result['NgayDi_Ngan'] = df['so_ngay'] <= 3           # 2-3 ngày
        result['NgayDi_Vua']  = (df['so_ngay'] > 3) & (df['so_ngay'] <= 5)
        result['NgayDi_Dai']  = df['so_ngay'] > 5            # 6-8 ngày

    # ── 5. SỐ NGƯỜI → 3 BIN ──────────────────────────────────────────────
    if 'so_nguoi' in df.columns:
        result['NhomNguoi_1']     = df['so_nguoi'] == 1
        result['NhomNguoi_2_3']   = df['so_nguoi'].isin([2, 3])
        result['NhomNguoi_4plus'] = df['so_nguoi'] >= 4

    # ── 6. ĐÁNH GIÁ → 3 BIN ──────────────────────────────────────────────
    if 'danh_gia' in df.columns:
        result['DanhGia_Tot']   = df['danh_gia'] >= 4.0
        result['DanhGia_Trung'] = (df['danh_gia'] >= 3.0) & (df['danh_gia'] < 4.0)
        result['DanhGia_Kem']   = df['danh_gia'] < 3.0

    # ── 7. KHÁCH QUAY LẠI ────────────────────────────────────────────────
    if 'khach_quay_lai' in df.columns:
        result['Khach_Quay_Lai'] = df['khach_quay_lai'] == 1
        result['Khach_Lan_Dau']  = df['khach_quay_lai'] == 0

    return result.astype(bool)


def run_fpgrowth(df: pd.DataFrame, min_sup: float, min_conf: float) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Bảng dữ liệu trống!")

    print(f"[FPGrowth] Input: {df.shape[0]} giao dịch x {df.shape[1]} cột")

    # Rời rạc hóa toàn bộ thuộc tính
    df_bool = _discretize(df)
    print(f"[FPGrowth] Sau rời rạc hóa: {df_bool.shape[1]} item")
    print(f"[FPGrowth] Chạy FP-Growth: min_support={min_sup}, min_confidence={min_conf}")

    frequent_itemsets = fpgrowth(df_bool, min_support=min_sup, use_colnames=True)
    if frequent_itemsets.empty:
        raise ValueError(f"Không tìm thấy tập phổ biến nào với support >= {min_sup}")
    print(f"[FPGrowth] Tìm được {len(frequent_itemsets)} tập phổ biến")

    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_conf)
    print(f"[FPGrowth] Sinh được {len(rules)} luật trước khi lọc")

    # Lọc: chỉ giữ luật có ít nhất 1 dịch vụ HOẶC hoạt động ở vế phải
    # (Tránh luật vô nghĩa như Den_Da_Nang → Mua_Ha)
    SERVICE_ITEMS = {
        'DV_Khach_San_Homestay', 'DV_Ve_May_Bay', 'DV_Dua_Don_San_Bay',
        'DV_Tour_Va_Khu_Vui_Choi', 'DV_Thue_Xe_Tu_Lai',
        'HD_Tam_Bien', 'HD_Leo_Nui_Trekking', 'HD_Tham_Quan_Di_Tich',
        'HD_Am_Thuc', 'HD_Check_In', 'HD_Nghi_Duong_Chua_Lanh',
    }

    def has_service(itemset):
        return any(item in SERVICE_ITEMS for item in itemset)

    rules = rules[rules['consequents'].apply(has_service)]
    print(f"[FPGrowth] Còn {len(rules)} luật sau khi lọc (vế phải phải có dịch vụ/hoạt động)")

    # Convert frozenset → string
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(sorted(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(sorted(x)))

    rules_db = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    rules_db.columns = ['DichVu_Goc', 'DichVu_GoiY', 'Do_Ho_Tro', 'Do_Tin_Cay_Confidence', 'Chi_So_Lift']
    rules_db = rules_db.sort_values('Do_Tin_Cay_Confidence', ascending=False)

    print(f"[FPGrowth] Hoàn tất! {len(rules_db)} luật sẵn sàng lưu DB")
    print(f"\n--- TOP 10 LUẬT CÓ ĐỘ TIN CẬY CAO NHẤT ---")
    for _, row in rules_db.head(10).iterrows():
        print(f"  [{row['DichVu_Goc']}]  →  [{row['DichVu_GoiY']}]  conf={row['Do_Tin_Cay_Confidence']:.3f}  lift={row['Chi_So_Lift']:.2f}")

    return rules_db
