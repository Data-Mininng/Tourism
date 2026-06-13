import pandas as pd
from sqlalchemy import create_engine, text

SERVER   = '.'
DATABASE = 'Tourism_DB'
DB_URL   = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
engine   = create_engine(DB_URL)


# =====================================================================
# KHỞI TẠO BẢNG LOG (chỉ chạy 1 lần khi server start)
# =====================================================================

def init_log_tables():
    """Tạo bảng VoucherInputLog và VoucherPredictLog nếu chưa tồn tại."""
    with engine.begin() as conn:
        # Bảng 1: Lưu 7 feature đầu vào từ web gửi sang
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherInputLog' AND xtype='U')
            CREATE TABLE VoucherInputLog (
                Id                       INT IDENTITY(1,1) PRIMARY KEY,
                AdministrativeDuration   FLOAT         NOT NULL DEFAULT 0,
                InformationalDuration    FLOAT         NOT NULL DEFAULT 0,
                ProductRelatedDuration   FLOAT         NOT NULL DEFAULT 0,
                BounceRates              FLOAT         NOT NULL DEFAULT 0,
                ExitRates                FLOAT         NOT NULL DEFAULT 0,
                PageValues               FLOAT         NOT NULL DEFAULT 0,
                Weekend                  INT           NOT NULL DEFAULT 0,
                ReceivedAt               DATETIME2     NOT NULL DEFAULT GETDATE()
            )
        """))

        # Bảng 2: Lưu kết quả cây quyết định trả ra
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherPredictLog' AND xtype='U')
            CREATE TABLE VoucherPredictLog (
                Id                      INT IDENTITY(1,1) PRIMARY KEY,
                InputLogId              INT           NULL,           -- FK -> VoucherInputLog.Id
                PredictedRevenueIntent  INT           NOT NULL DEFAULT -1,  -- 0=không mua, 1=sẽ mua
                NeedVoucher             BIT           NOT NULL DEFAULT 0,
                DiscountPercent         INT           NOT NULL DEFAULT 0,
                DecisionReason          NVARCHAR(500) NOT NULL DEFAULT '',
                PredictedAt             DATETIME2     NOT NULL DEFAULT GETDATE(),
                CONSTRAINT FK_VoucherPredictLog_Input
                    FOREIGN KEY (InputLogId) REFERENCES VoucherInputLog(Id)
            )
        """))
    print("✅ Bảng VoucherInputLog và VoucherPredictLog đã sẵn sàng.")


# =====================================================================
# HÀM LƯU LOG DỮ LIỆU VOUCHER
# =====================================================================

def save_voucher_input_log(params: dict) -> int:
    """
    Lưu 7 feature web gửi sang vào VoucherInputLog.
    Trả về Id của bản ghi vừa insert.
    """
    sql = text("""
        INSERT INTO VoucherInputLog
            (AdministrativeDuration, InformationalDuration, ProductRelatedDuration,
             BounceRates, ExitRates, PageValues, Weekend)
        OUTPUT INSERTED.Id
        VALUES
            (:admin, :info, :product, :bounce, :exit_, :page, :weekend)
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {
            "admin"  : params["administrative_duration"],
            "info"   : params["informational_duration"],
            "product": params["productrelated_duration"],
            "bounce" : params["bounce_rates"],
            "exit_"  : params["exit_rates"],
            "page"   : params["page_values"],
            "weekend": int(params["weekend"]),
        }).fetchone()
    return int(row[0])


def save_voucher_predict_log(input_id: int, predicted_revenue: int,
                              need_voucher: int, discount: int, reason: str):
    """Lưu kết quả dự đoán của cây quyết định vào VoucherPredictLog."""
    sql = text("""
        INSERT INTO VoucherPredictLog
            (InputLogId, PredictedRevenueIntent, NeedVoucher, DiscountPercent, DecisionReason)
        VALUES
            (:input_id, :revenue, :need, :discount, :reason)
    """)
    with engine.begin() as conn:
        conn.execute(sql, {
            "input_id": input_id,
            "revenue" : predicted_revenue,
            "need"    : need_voucher,
            "discount": discount,
            "reason"  : (reason or "")[:500],
        })


# =====================================================================
# TRUY XUẤT VÀ LƯU TRỮ MÔ HÌNH LUẬT KẾT HỢP
# =====================================================================

def get_transactions() -> pd.DataFrame:
    """
    Lấy dữ liệu từ GiaoDich — chỉ SELECT các cột thực sự tồn tại.
    Tự động phát hiện cột nào có trong bảng trước khi query để tránh lỗi 42S22.
    """
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = 'GiaoDich'"
        ))
        existing_cols = {row[0] for row in result}

    desired_cols = [
        "DV_Khach_San_Homestay", "DV_Ve_May_Bay", "DV_Dua_Don_San_Bay",
        "DV_Tour_Va_Khu_Vui_Choi", "DV_Thue_Xe_Tu_Lai",
        "HD_Tam_Bien", "HD_Leo_Nui_Trekking", "HD_Tham_Quan_Di_Tich",
        "HD_Am_Thuc", "HD_Check_In", "HD_Nghi_Duong_Chua_Lanh",
        "dia_diem", "muc_dich", "mua", "nhom_tuoi", "gioi_tinh", "kenh_dat",
        "ngan_sach_trieu", "so_ngay", "so_nguoi", "danh_gia", "khach_quay_lai",
        "tu_den", "hang_hang_khong", "loai_khach_san", "ho_boi",
    ]

    valid_cols   = [c for c in desired_cols if c in existing_cols]
    missing_cols = [c for c in desired_cols if c not in existing_cols]

    if missing_cols:
        print(f"[DB] ⚠️  Bỏ qua {len(missing_cols)} cột chưa tồn tại trong GiaoDich: {missing_cols}")

    col_list = ", ".join(valid_cols)
    query    = f"SELECT {col_list} FROM GiaoDich"
    df = pd.read_sql(query, engine)
    print(f"[DB] Lấy {len(df)} giao dịch với {df.shape[1]} cột để luyện AI.")
    return df


def save_rules(rules_df: pd.DataFrame):
    """
    Làm sạch và đổi tên cột khớp 100% với cấu trúc bảng thực tế trong SQL Server.
    Đảm bảo giữ lại và ghi nhận đúng cột Chi_So_Lift và Do_Ho_Tro.
    """
    if rules_df.empty:
        print("[DB ⚠️] Tập luật rỗng, hủy bỏ tiến trình lưu.")
        return

    # 1. Tạo bản sao để xử lý đổi tên cột
    df_to_save = rules_df.copy()

    # 2. Khớp trực tiếp tên cột từ rule_generator sang cột thực tế trong SSMS của bạn
    # Vế trái: Tên cột do module rule_generator sinh ra
    # Vế phải: Tên cột thực tế lấy chính xác từ ảnh chụp bảng của bạn
    mapping_cols = {
        "DichVu_Goc": "DichVu_Goc",
        "DichVu_GoiY": "DichVu_GoiY",
        "Do_Ho_Tro_Support": "Do_Ho_Tro",            # Khớp với 'Do_Ho_Tro' trong ảnh
        "Do_Tin_Cay_Confidence": "Do_Tin_Cay_Confidence", # Giữ nguyên viết hoa thường
        "Do_Nang_Lift": "Chi_So_Lift"                # Khớp chuẩn xác với 'Chi_So_Lift' trong ảnh
    }

    # Thực hiện đổi tên cột
    df_to_save = df_to_save.rename(columns=mapping_cols)

    # 3. Lọc bỏ các cột thừa (nếu có) không nằm trong 5 cột chính của bảng
    db_expected_columns = ["DichVu_Goc", "DichVu_GoiY", "Do_Ho_Tro", "Do_Tin_Cay_Confidence", "Chi_So_Lift"]
    final_cols = [c for c in df_to_save.columns if c in db_expected_columns]
    df_to_save = df_to_save[final_cols]

    # 4. Truncate (Xóa sạch) dữ liệu luật cũ và ghi đè tập luật mới
    try:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE Luat_FPGrowth"))
            print("[DB] Đã dọn dẹp (TRUNCATE) các luật cũ để chuẩn bị ghi mới.")
    except Exception as ex:
        print(f"[DB ⚠️] Cảnh báo khi làm sạch dữ liệu cũ: {ex}")

    # Đẩy dữ liệu trực tiếp xuống bảng Luat_FPGrowth trong SQL Server
    try:
        df_to_save.to_sql('Luat_FPGrowth', engine, if_exists='append', index=False)
        print(f"🌲 [DB] Thành công! Đã đồng bộ {len(df_to_save)} luật vào DB (Có đủ Do_Ho_Tro và Chi_So_Lift).")
    except Exception as e:
        print(f"❌ [DB LỖI LƯU LUẬT]: {str(e)}")