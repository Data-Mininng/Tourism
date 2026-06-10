import pandas as pd
from sqlalchemy import create_engine, text

SERVER   = '.'
DATABASE = 'Tourism_DB'
DB_URL   = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
engine   = create_engine(DB_URL)

def get_transactions() -> pd.DataFrame:
    """
    Lấy toàn bộ ma trận giao dịch đã tiền xử lý đầy đủ từ bảng GiaoDich.
    Bao gồm các thuộc tính dịch vụ, hoạt động và toàn bộ biến ngữ cảnh mở rộng.
    """
    query = """
        SELECT
            -- Dịch vụ (5 cột nhị phân)
            DV_Khach_San_Homestay,
            DV_Ve_May_Bay,
            DV_Dua_Don_San_Bay,
            DV_Tour_Va_Khu_Vui_Choi,
            DV_Thue_Xe_Tu_Lai,

            -- Hoạt động (6 cột nhị phân)
            HD_Tam_Bien,
            HD_Leo_Nui_Trekking,
            HD_Tham_Quan_Di_Tich,
            HD_Am_Thuc,
            HD_Check_In,
            HD_Nghi_Duong_Chua_Lanh,

            -- Thông tin chuyến đi (Ngữ cảnh cũ)
            dia_diem,
            muc_dich,
            mua,
            nhom_tuoi,
            gioi_tinh,
            kenh_dat,

            -- Số học
            ngan_sach_trieu,
            so_ngay,
            so_nguoi,
            danh_gia,
            khach_quay_lai,

            -- BỔ SUNG: Thêm các cột tương ứng với Log Frontend gửi sang để AI luyện luật
            tu_den,
            hang_hang_khong,
            loai_khach_san,
            ho_boi

        FROM GiaoDich
    """
    df = pd.read_sql(query, engine)
    print(f"[DB] Lấy {len(df)} giao dịch với {df.shape[1]} thuộc tính để luyện AI.")
    return df


def save_rules(rules_df: pd.DataFrame):
    try:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE Luat_FPGrowth"))
            print("Đã xóa luật cũ.")
    except:
        print("Bảng chưa tồn tại, sẽ tạo mới.")

    rules_df.to_sql('Luat_FPGrowth', engine, if_exists='append', index=False)
    print(f"Đã lưu {len(rules_df)} luật vào DB!")
