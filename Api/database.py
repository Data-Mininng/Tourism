import pandas as pd
from sqlalchemy import create_engine

# CẤU HÌNH DB
SERVER = '.'
DATABASE = 'Tourism_DB'
DB_URL = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
engine = create_engine(DB_URL)

def get_transactions() -> pd.DataFrame:
    """Hàm lấy dữ liệu từ DB ném lên RAM"""
    query = """
        SELECT 
            DV_Ve_May_Bay, DV_Khach_San_Resort, DV_Dua_Don_San_Bay, 
            DV_Ve_Khu_Vui_Choi, DV_Tour_Trong_Ngay, DV_Thue_Xe_Dien, DV_Thue_Xe_Oto 
        FROM GiaoDich
    """
    return pd.read_sql(query, engine)

def save_rules(rules_df: pd.DataFrame):
    """Hàm nhận DataFrame và đập thẳng vào DB"""
    rules_df.to_sql('Luat_FPGrowth', engine, if_exists='replace', index=False)