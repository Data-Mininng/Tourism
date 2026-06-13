-- ============================================================
-- MIGRATION: Thêm cột ImageUrl vào 5 bảng dịch vụ
--            + Tạo 2 bảng log voucher mới
-- Chạy script này MỘT LẦN trên DB hiện có
-- ============================================================

-- ── 1. THÊM CỘT ImageUrl ────────────────────────────────────

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Hotels') AND name = 'ImageUrl')
    ALTER TABLE Hotels ADD ImageUrl NVARCHAR(300) NOT NULL DEFAULT 'img/hotel/default.jpg';

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Tours') AND name = 'ImageUrl')
    ALTER TABLE Tours ADD ImageUrl NVARCHAR(300) NOT NULL DEFAULT 'img/tour/default.jpg';

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Flights') AND name = 'ImageUrl')
    ALTER TABLE Flights ADD ImageUrl NVARCHAR(300) NOT NULL DEFAULT 'img/flight/default.jpg';

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Cars') AND name = 'ImageUrl')
    ALTER TABLE Cars ADD ImageUrl NVARCHAR(300) NOT NULL DEFAULT 'img/car/default.jpg';

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('Transfers') AND name = 'ImageUrl')
    ALTER TABLE Transfers ADD ImageUrl NVARCHAR(300) NOT NULL DEFAULT 'img/transfer/default.jpg';

GO

-- ── 2. CẬP NHẬT ImageUrl CHO DỮ LIỆU ĐÃ SEED ───────────────
-- Hotels (8 bản ghi, Id 1-8)
UPDATE Hotels SET ImageUrl = 'img/hotel/1.jpg' WHERE Id = 1;  -- Hanoi Pearl Hotel
UPDATE Hotels SET ImageUrl = 'img/hotel/2.jpg' WHERE Id = 2;  -- Saigon Star Hotel
UPDATE Hotels SET ImageUrl = 'img/hotel/3.jpg' WHERE Id = 3;  -- Danang Beach Resort
UPDATE Hotels SET ImageUrl = 'img/hotel/4.jpg' WHERE Id = 4;  -- Nha Trang Palace Hotel
UPDATE Hotels SET ImageUrl = 'img/hotel/5.jpg' WHERE Id = 5;  -- Phu Quoc Island Resort
UPDATE Hotels SET ImageUrl = 'img/hotel/6.jpg' WHERE Id = 6;  -- Hoi An Ancient House Hotel
UPDATE Hotels SET ImageUrl = 'img/hotel/7.jpg' WHERE Id = 7;  -- Dalat Flower Hotel
UPDATE Hotels SET ImageUrl = 'img/hotel/8.jpg' WHERE Id = 8;  -- Ha Long Bay Cruise Hotel

-- Tours (8 bản ghi, Id 1-8)
UPDATE Tours SET ImageUrl = 'img/tour/1.jpg' WHERE Id = 1;  -- Du thuyền Hạ Long Bay
UPDATE Tours SET ImageUrl = 'img/tour/2.jpg' WHERE Id = 2;  -- Khám phá Phố Cổ Hội An
UPDATE Tours SET ImageUrl = 'img/tour/3.jpg' WHERE Id = 3;  -- Trekking Sapa – Fansipan
UPDATE Tours SET ImageUrl = 'img/tour/4.jpg' WHERE Id = 4;  -- Khám phá Phú Quốc
UPDATE Tours SET ImageUrl = 'img/tour/5.jpg' WHERE Id = 5;  -- Tour Đà Nẵng – Bà Nà Hills
UPDATE Tours SET ImageUrl = 'img/tour/6.jpg' WHERE Id = 6;  -- Khám phá Tây Nguyên
UPDATE Tours SET ImageUrl = 'img/tour/7.jpg' WHERE Id = 7;  -- Hành trình Cố đô Huế
UPDATE Tours SET ImageUrl = 'img/tour/8.jpg' WHERE Id = 8;  -- Tour Mũi Né – Bình Thuận

-- Flights (6 bản ghi, Id 1-6)
UPDATE Flights SET ImageUrl = 'img/flight/1.jpg' WHERE Id = 1;  -- Vietnam Airlines VN123
UPDATE Flights SET ImageUrl = 'img/flight/2.jpg' WHERE Id = 2;  -- VietJet Air VJ456
UPDATE Flights SET ImageUrl = 'img/flight/3.jpg' WHERE Id = 3;  -- Bamboo Airways QH789
UPDATE Flights SET ImageUrl = 'img/flight/4.jpg' WHERE Id = 4;  -- Vietnam Airlines VN321
UPDATE Flights SET ImageUrl = 'img/flight/5.jpg' WHERE Id = 5;  -- VietJet Air VJ654
UPDATE Flights SET ImageUrl = 'img/flight/6.jpg' WHERE Id = 6;  -- Pacific Airlines BL100

-- Cars (8 bản ghi, Id 1-8)
UPDATE Cars SET ImageUrl = 'img/car/1.jpg' WHERE Id = 1;  -- Toyota Camry
UPDATE Cars SET ImageUrl = 'img/car/2.jpg' WHERE Id = 2;  -- Honda Civic
UPDATE Cars SET ImageUrl = 'img/car/3.jpg' WHERE Id = 3;  -- Hyundai Tucson
UPDATE Cars SET ImageUrl = 'img/car/4.jpg' WHERE Id = 4;  -- Ford Ranger
UPDATE Cars SET ImageUrl = 'img/car/5.jpg' WHERE Id = 5;  -- Mazda CX-5
UPDATE Cars SET ImageUrl = 'img/car/6.jpg' WHERE Id = 6;  -- Kia Morning
UPDATE Cars SET ImageUrl = 'img/car/7.jpg' WHERE Id = 7;  -- VinFast VF 8
UPDATE Cars SET ImageUrl = 'img/car/8.jpg' WHERE Id = 8;  -- Mercedes C200

-- Transfers (8 bản ghi, Id 1-8)
UPDATE Transfers SET ImageUrl = 'img/transfer/1.jpg' WHERE Id = 1;  -- Taxi Nội Bài → HN
UPDATE Transfers SET ImageUrl = 'img/transfer/2.jpg' WHERE Id = 2;  -- Taxi TSN → HCM
UPDATE Transfers SET ImageUrl = 'img/transfer/3.jpg' WHERE Id = 3;  -- Limousine HN → Hạ Long
UPDATE Transfers SET ImageUrl = 'img/transfer/4.jpg' WHERE Id = 4;  -- Bus HCM → Mũi Né
UPDATE Transfers SET ImageUrl = 'img/transfer/5.jpg' WHERE Id = 5;  -- Bus ĐN → Hội An
UPDATE Transfers SET ImageUrl = 'img/transfer/6.jpg' WHERE Id = 6;  -- Train HN → HCM
UPDATE Transfers SET ImageUrl = 'img/transfer/7.jpg' WHERE Id = 7;  -- Limousine ĐN → Hội An
UPDATE Transfers SET ImageUrl = 'img/transfer/8.jpg' WHERE Id = 8;  -- Taxi Phú Quốc

GO

-- ── 3. TẠO BẢNG VoucherFeatureLog ───────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherFeatureLog' AND xtype='U')
CREATE TABLE VoucherFeatureLog (
    Id                    INT IDENTITY(1,1) PRIMARY KEY,
    SessionId             NVARCHAR(64)      NOT NULL DEFAULT '',
    UserId                INT               NULL,
    TotalLogCount         INT               NOT NULL DEFAULT 0,

    -- 7 Feature gửi lên model dự đoán voucher
    AdminDuration         DECIMAL(12,4)     NOT NULL DEFAULT 0,
    InformationalDuration DECIMAL(12,4)     NOT NULL DEFAULT 0,
    ProductDuration       DECIMAL(12,4)     NOT NULL DEFAULT 0,
    BounceRate            DECIMAL(8,6)      NOT NULL DEFAULT 0,
    ExitRate              DECIMAL(8,6)      NOT NULL DEFAULT 0,
    AvgPageValues         DECIMAL(10,4)     NOT NULL DEFAULT 0,
    WeekendVal            INT               NOT NULL DEFAULT 0,

    -- Các trang đã xem
    PagesVisited          NVARCHAR(200)     NOT NULL DEFAULT '',
    UniquePageCount       INT               NOT NULL DEFAULT 0,

    ComputedAt            DATETIME          NOT NULL DEFAULT GETDATE()
);

-- ── 4. TẠO BẢNG VoucherDecisionLog ──────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherDecisionLog' AND xtype='U')
CREATE TABLE VoucherDecisionLog (
    Id                    INT IDENTITY(1,1) PRIMARY KEY,
    SessionId             NVARCHAR(64)      NOT NULL DEFAULT '',
    UserId                INT               NULL,
    FeatureLogId          INT               NULL,   -- FK -> VoucherFeatureLog.Id
    VoucherCode           NVARCHAR(50)      NULL,

    -- Đầu ra model
    ModelPredictedRevenue INT               NOT NULL DEFAULT 0,  -- 0=không mua, 1=sẽ mua
    ModelDecidedGrant     BIT               NOT NULL DEFAULT 0,
    DiscountPercent       INT               NOT NULL DEFAULT 0,
    DecisionReason        NVARCHAR(500)     NOT NULL DEFAULT '',

    -- Kết quả thực tế (cập nhật sau)
    ActuallyUsed          BIT               NULL,       -- NULL = chưa biết
    ActuallyPurchased     BIT               NULL,
    IsModelCorrect        BIT               NULL,       -- NULL = chưa đủ dữ liệu

    DecidedAt             DATETIME          NOT NULL DEFAULT GETDATE(),
    EvaluatedAt           DATETIME          NULL
);

-- FK optional (không bắt buộc để tránh lỗi khi chạy lần đầu)
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE name = 'FK_VoucherDecisionLog_FeatureLog'
)
ALTER TABLE VoucherDecisionLog
    ADD CONSTRAINT FK_VoucherDecisionLog_FeatureLog
    FOREIGN KEY (FeatureLogId) REFERENCES VoucherFeatureLog(Id)
    ON DELETE SET NULL;

GO

-- ── 5. VIEW KIỂM TRA ĐỘ CHÍNH XÁC MODEL VOUCHER ────────────
-- Dùng để xem dashboard: model đúng bao nhiêu %
IF EXISTS (SELECT * FROM sysobjects WHERE name='vw_VoucherModelAccuracy' AND xtype='V')
    DROP VIEW vw_VoucherModelAccuracy;
GO

CREATE VIEW vw_VoucherModelAccuracy AS
SELECT
    COUNT(*)                                             AS TongQuyetDinh,
    SUM(CASE WHEN ModelDecidedGrant = 1 THEN 1 ELSE 0 END) AS SoLanCap,
    SUM(CASE WHEN ModelDecidedGrant = 0 THEN 1 ELSE 0 END) AS SoLanKhongCap,
    SUM(CASE WHEN IsModelCorrect = 1   THEN 1 ELSE 0 END) AS SoDung,
    SUM(CASE WHEN IsModelCorrect = 0   THEN 1 ELSE 0 END) AS SoSai,
    SUM(CASE WHEN IsModelCorrect IS NULL THEN 1 ELSE 0 END) AS ChuaDanhGia,
    -- Accuracy tính trên các quyết định đã đánh giá
    CASE WHEN SUM(CASE WHEN IsModelCorrect IS NOT NULL THEN 1 ELSE 0 END) > 0
         THEN CAST(
              SUM(CASE WHEN IsModelCorrect = 1 THEN 1 ELSE 0 END) * 100.0
              / SUM(CASE WHEN IsModelCorrect IS NOT NULL THEN 1 ELSE 0 END)
              AS DECIMAL(5,2))
         ELSE NULL
    END AS AccuracyPhanTram,
    -- Tỉ lệ voucher được dùng thực tế / tổng được cấp
    CASE WHEN SUM(CASE WHEN ModelDecidedGrant = 1 AND ActuallyUsed IS NOT NULL THEN 1 ELSE 0 END) > 0
         THEN CAST(
              SUM(CASE WHEN ModelDecidedGrant = 1 AND ActuallyUsed = 1 THEN 1 ELSE 0 END) * 100.0
              / SUM(CASE WHEN ModelDecidedGrant = 1 AND ActuallyUsed IS NOT NULL THEN 1 ELSE 0 END)
              AS DECIMAL(5,2))
         ELSE NULL
    END AS TiLeDungVoucher
FROM VoucherDecisionLog;
GO

PRINT N'✅ Migration hoàn tất: ImageUrl thêm vào 5 bảng, VoucherFeatureLog + VoucherDecisionLog tạo thành công.';
