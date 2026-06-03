import pandas as pd
from sqlalchemy import create_engine, text

# CẤU HÌNH DB (Thằng anh nhớ check lại SERVER và DATABASE cho chuẩn nhé)
SERVER = '.'
DATABASE = 'Tourism_DB'
DB_URL = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
engine = create_engine(DB_URL)

def get_transactions() -> pd.DataFrame:
    """Hàm lấy dữ liệu từ DB ném lên RAM"""
    
    # Đã sửa lại danh sách cột chuẩn xịn theo ma trận 5 DV và 6 HD
    query = """
        SELECT 
            DV_Khach_San_Homestay, 
            DV_Ve_May_Bay, 
            DV_Dua_Don_San_Bay, 
            DV_Tour_Va_Khu_Vui_Choi, 
            DV_Thue_Xe_Tu_Lai,
            HD_Tam_Bien, 
            HD_Leo_Nui_Trekking, 
            HD_Tham_Quan_Di_Tich, 
            HD_Am_Thuc, 
            HD_Check_In, 
            HD_Nghi_Duong_Chua_Lanh
        FROM GiaoDich
    """
    return pd.read_sql(query, engine)

def save_rules(rules_df: pd.DataFrame):
    """Hàm nhận DataFrame và đập thẳng vào DB an toàn"""
    
    # Bước 1: Dọn dẹp nhà cửa. 
    # Dùng TRUNCATE để xóa sạch data cũ nhưng VẪN GIỮ NGUYÊN cấu trúc bảng, khóa chính, khóa ngoại.
    try:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE Luat_FPGrowth"))
            print("Đã dọn sạch dữ liệu cũ trong bảng Luat_FPGrowth.")
    except Exception as e:
        # Nếu bảng chưa tồn tại (lần đầu chạy), nó sẽ báo lỗi và bỏ qua TRUNCATE
        print("Bảng Luat_FPGrowth chưa tồn tại, SQLAlchemy sẽ tự động tạo mới.")

    # Bước 2: Bơm data mới vào. 
    # Dùng if_exists='append' để nối dữ liệu vào bảng đã có, tránh bị đổi kiểu dữ liệu cột.
    rules_df.to_sql('Luat_FPGrowth', engine, if_exists='append', index=False)
    print("Đã lưu luật mới vào Database thành công!")