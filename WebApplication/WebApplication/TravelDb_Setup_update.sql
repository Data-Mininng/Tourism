-- ============================================================
--  VIETTRAVEL DATABASE - TravelDb  (Web C# ASP.NET)
--  Tương thích: SQL Server 2019+ / SQL Server Express / LocalDB
-- ============================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'TravelDb')
BEGIN
    CREATE DATABASE TravelDb;
END
GO

USE TravelDb;
GO

-- ============================================================
--  BẢNG NGHIỆP VỤ (GIỮ NGUYÊN)
-- ============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Cars' AND xtype='U')
CREATE TABLE Cars (
    Id          INT IDENTITY(1,1) PRIMARY KEY,
    Brand       NVARCHAR(100)  NOT NULL,
    Model       NVARCHAR(100)  NOT NULL,
    Year        INT            NOT NULL DEFAULT 2020,
    PricePerDay DECIMAL(18,2)  NOT NULL DEFAULT 0,
    IsAvailable BIT            NOT NULL DEFAULT 1,
    ImageUrl    NVARCHAR(300)  NOT NULL DEFAULT 'img/car/default.jpg',
    CreatedAt   DATETIME2      NOT NULL DEFAULT GETDATE(),
    UpdatedAt   DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Rentals' AND xtype='U')
CREATE TABLE Rentals (
    Id           INT IDENTITY(1,1) PRIMARY KEY,
    CarId        INT            NOT NULL REFERENCES Cars(Id) ON DELETE CASCADE,
    CustomerName NVARCHAR(200)  NOT NULL,
    RentDate     DATETIME2      NOT NULL,
    ReturnDate   DATETIME2      NOT NULL,
    TotalPrice   DECIMAL(18,2)  NOT NULL DEFAULT 0,
    CreatedAt    DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Flights' AND xtype='U')
CREATE TABLE Flights (
    Id             INT IDENTITY(1,1) PRIMARY KEY,
    Airline        NVARCHAR(200)  NOT NULL,
    FlightNumber   NVARCHAR(20)   NOT NULL,
    Departure      NVARCHAR(200)  NOT NULL,
    Arrival        NVARCHAR(200)  NOT NULL,
    DepartureTime  DATETIME2      NOT NULL,
    ArrivalTime    DATETIME2      NOT NULL,
    Price          DECIMAL(18,2)  NOT NULL DEFAULT 0,
    AvailableSeats INT            NOT NULL DEFAULT 0,
    ImageUrl       NVARCHAR(300)  NOT NULL DEFAULT 'img/flight/default.jpg',
    CreatedAt      DATETIME2      NOT NULL DEFAULT GETDATE(),
    UpdatedAt      DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Hotels' AND xtype='U')
CREATE TABLE Hotels (
    Id            INT IDENTITY(1,1) PRIMARY KEY,
    Name          NVARCHAR(300)  NOT NULL,
    Location      NVARCHAR(300)  NOT NULL,
    Stars         INT            NOT NULL DEFAULT 3,
    PricePerNight DECIMAL(18,2)  NOT NULL DEFAULT 0,
    HasPool       BIT            NOT NULL DEFAULT 0,
    ImageUrl      NVARCHAR(300)  NOT NULL DEFAULT 'img/hotel/default.jpg',
    CreatedAt     DATETIME2      NOT NULL DEFAULT GETDATE(),
    UpdatedAt     DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tours' AND xtype='U')
CREATE TABLE Tours (
    Id           INT IDENTITY(1,1) PRIMARY KEY,
    Name         NVARCHAR(300)  NOT NULL,
    Destination  NVARCHAR(200)  NOT NULL,
    DurationDays INT            NOT NULL DEFAULT 1,
    Price        DECIMAL(18,2)  NOT NULL DEFAULT 0,
    Description  NVARCHAR(MAX)  NULL,
    ImageUrl     NVARCHAR(300)  NOT NULL DEFAULT 'img/tour/default.jpg',
    CreatedAt    DATETIME2      NOT NULL DEFAULT GETDATE(),
    UpdatedAt    DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Transfers' AND xtype='U')
CREATE TABLE Transfers (
    Id            INT IDENTITY(1,1) PRIMARY KEY,
    Type          NVARCHAR(50)   NOT NULL,
    FromLocation  NVARCHAR(200)  NOT NULL,
    ToLocation    NVARCHAR(200)  NOT NULL,
    DepartureTime DATETIME2      NOT NULL,
    Price         DECIMAL(18,2)  NOT NULL DEFAULT 0,
    Capacity      INT            NOT NULL DEFAULT 4,
    ImageUrl      NVARCHAR(300)  NOT NULL DEFAULT 'img/transfer/default.jpg',
    CreatedAt     DATETIME2      NOT NULL DEFAULT GETDATE(),
    UpdatedAt     DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
CREATE TABLE Users (
    Id           INT IDENTITY(1,1) PRIMARY KEY,
    FullName     NVARCHAR(200)  NOT NULL,
    Email        NVARCHAR(200)  NOT NULL UNIQUE,
    PasswordHash NVARCHAR(500)  NOT NULL,
    Phone        NVARCHAR(20)   NULL,
    AvatarUrl    NVARCHAR(500)  NULL,
    DateOfBirth  DATE           NULL,
    Hometown     NVARCHAR(200)  NULL,
    CurrentCity  NVARCHAR(200)  NULL,
    Role         NVARCHAR(20)   NOT NULL DEFAULT 'User',
    MemberLevel  NVARCHAR(50)   NOT NULL DEFAULT N'Thành viên',
    IsActive     BIT            NOT NULL DEFAULT 1,
    CreatedAt    DATETIME2      NOT NULL DEFAULT GETDATE(),
    UpdatedAt    DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Bookings' AND xtype='U')
CREATE TABLE Bookings (
    Id            INT IDENTITY(1,1) PRIMARY KEY,
    UserId        INT            NULL REFERENCES Users(Id) ON DELETE SET NULL,
    BookingType   NVARCHAR(20)   NOT NULL,
    ReferenceId   INT            NOT NULL,
    BookingDate   DATETIME2      NOT NULL DEFAULT GETDATE(),
    TravelDate    DATETIME2      NULL,
    GuestCount    INT            NOT NULL DEFAULT 1,
    TotalAmount   DECIMAL(18,2)  NOT NULL DEFAULT 0,
    Status        NVARCHAR(20)   NOT NULL DEFAULT 'Pending',
    PaymentStatus NVARCHAR(20)   NOT NULL DEFAULT 'Unpaid',
    Notes         NVARCHAR(MAX)  NULL,
    CreatedAt     DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Reviews' AND xtype='U')
CREATE TABLE Reviews (
    Id          INT IDENTITY(1,1) PRIMARY KEY,
    UserId      INT            NULL REFERENCES Users(Id) ON DELETE SET NULL,
    ServiceType NVARCHAR(20)   NOT NULL,
    ServiceId   INT            NOT NULL,
    Rating      INT            NOT NULL CHECK (Rating BETWEEN 1 AND 5),
    Comment     NVARCHAR(MAX)  NULL,
    CreatedAt   DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================
--  BẢNG AI — 3 bảng, chỉ thuộc TravelDb (web C#)
--  LuatFPGrowth: được NẠP TỪ Tourism_DB qua API Python
--  KHÔNG có quan hệ FK với bảng nghiệp vụ (dữ liệu từ nguồn khác)
-- ============================================================

-- Bảng 1: Luật kết hợp — do Python FP-Growth sinh ra, được đẩy vào đây qua API
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LuatFPGrowth' AND xtype='U')
CREATE TABLE LuatFPGrowth (
    Id                    INT IDENTITY(1,1) PRIMARY KEY,
    DichVu_Goc            NVARCHAR(500) NOT NULL,   -- Vế trái:  "DV_Ve_May_Bay, Den_Da_Nang"
    DichVu_GoiY           NVARCHAR(500) NOT NULL,   -- Vế phải:  "DV_Dua_Don_San_Bay"
    Do_Ho_Tro             DECIMAL(10,4) NOT NULL DEFAULT 0,
    Do_Tin_Cay_Confidence DECIMAL(10,4) NOT NULL DEFAULT 0,
    Chi_So_Lift           DECIMAL(10,4) NOT NULL DEFAULT 0,
    CreatedAt             DATETIME2     NOT NULL DEFAULT GETDATE()
    -- KHÔNG có FK → bảng nghiệp vụ vì data đến từ Tourism_DB khác
);
GO

CREATE INDEX IX_LuatFPGrowth_Confidence ON LuatFPGrowth (Do_Tin_Cay_Confidence DESC);
GO

-- Bảng 2: Hành vi người dùng — JS theo dõi gửi về, C# lưu
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='UserBehaviorLogs' AND xtype='U')
CREATE TABLE UserBehaviorLogs (
    Id           INT IDENTITY(1,1) PRIMARY KEY,
    SessionId    NVARCHAR(50)   NOT NULL DEFAULT '',
    UserId       INT            NULL REFERENCES Users(Id) ON DELETE SET NULL,
    PageType     NVARCHAR(50)   NOT NULL DEFAULT '',  -- Tour/Hotel/Flight/Car/Transfer
    ReferenceId  INT            NULL,                 -- Id sản phẩm đang xem
    PageValues   FLOAT          NOT NULL DEFAULT 0,   -- Điểm tương tác tính từ JS
    TimeOnPage   FLOAT          NOT NULL DEFAULT 0,   -- Giây ở trang
    IsWeekend    BIT            NOT NULL DEFAULT 0,
    HasPurchased BIT            NOT NULL DEFAULT 0,
    -- Ngữ cảnh đầy đủ: địa điểm, hãng bay, giá, số ngày...
    -- VD: {"service":"DV_Ve_May_Bay","destination":"Da_Nang","price_tier":"Cao","airline":"VietJet"}
    ContextData  NVARCHAR(1000) NOT NULL DEFAULT '{}',
    LoggedAt     DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO

CREATE INDEX IX_UserBehaviorLogs_Session  ON UserBehaviorLogs (SessionId);
CREATE INDEX IX_UserBehaviorLogs_LoggedAt ON UserBehaviorLogs (LoggedAt DESC);
GO

-- Bảng 3: Voucher đã cấp
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VouchersIssued' AND xtype='U')
CREATE TABLE VouchersIssued (
    Id              INT IDENTITY(1,1) PRIMARY KEY,
    SessionId       NVARCHAR(50)  NOT NULL DEFAULT '',
    UserId          INT           NULL REFERENCES Users(Id) ON DELETE SET NULL,
    VoucherCode     NVARCHAR(50)  NOT NULL UNIQUE,    -- Mã không trùng
    DiscountPercent INT           NOT NULL DEFAULT 10,
    ApplicableType  NVARCHAR(50)  NOT NULL DEFAULT 'All', -- Tour/Hotel/Flight/Car/Transfer/All
    ApplicableId    INT           NULL,               -- Id sản phẩm cụ thể (null = áp dụng tất cả loại đó)
    IssuedAt        DATETIME2     NOT NULL DEFAULT GETDATE(),
    ExpiresAt       DATETIME2     NOT NULL,
    IsUsed          BIT           NOT NULL DEFAULT 0
);
GO

CREATE INDEX IX_VouchersIssued_Session   ON VouchersIssued (SessionId);
CREATE INDEX IX_VouchersIssued_ExpiresAt ON VouchersIssued (ExpiresAt);
GO

-- ============================================================
--  SEED DATA
-- ============================================================

IF NOT EXISTS (SELECT TOP 1 1 FROM Cars)
INSERT INTO Cars (Brand, Model, Year, PricePerDay, IsAvailable, ImageUrl) VALUES
(N'Toyota',   N'Camry',   2020, 800000,  1, 'img/car/1.jpg'),
(N'Honda',    N'Civic',   2021, 650000,  1, 'img/car/2.jpg'),
(N'Hyundai',  N'Tucson',  2022, 900000,  1, 'img/car/3.jpg'),
(N'Ford',     N'Ranger',  2021, 1100000, 1, 'img/car/4.jpg'),
(N'Mazda',    N'CX-5',    2023, 1000000, 0, 'img/car/5.jpg'),
(N'Kia',      N'Morning', 2020, 500000,  1, 'img/car/6.jpg'),
(N'VinFast',  N'VF 8',    2023, 1200000, 1, 'img/car/7.jpg'),
(N'Mercedes', N'C200',    2022, 2500000, 1, 'img/car/8.jpg');
GO

IF NOT EXISTS (SELECT TOP 1 1 FROM Flights)
INSERT INTO Flights (Airline, FlightNumber, Departure, Arrival, DepartureTime, ArrivalTime, Price, AvailableSeats, ImageUrl) VALUES
(N'Vietnam Airlines', N'VN123', N'Hà Nội',          N'TP. Hồ Chí Minh', DATEADD(day,1,GETDATE()), DATEADD(hour,2,DATEADD(day,1,GETDATE())),    1850000, 90,  'img/flight/1.jpg'),
(N'VietJet Air',      N'VJ456', N'TP. Hồ Chí Minh', N'Đà Nẵng',         DATEADD(day,2,GETDATE()), DATEADD(hour,1,DATEADD(day,2,GETDATE())),     750000, 120, 'img/flight/2.jpg'),
(N'Bamboo Airways',   N'QH789', N'Hà Nội',           N'Nha Trang',        DATEADD(day,3,GETDATE()), DATEADD(hour,2,DATEADD(day,3,GETDATE())),    1200000,  80, 'img/flight/3.jpg'),
(N'Vietnam Airlines', N'VN321', N'TP. Hồ Chí Minh', N'Phú Quốc',        DATEADD(day,4,GETDATE()), DATEADD(minute,75,DATEADD(day,4,GETDATE())), 1100000,  60, 'img/flight/4.jpg'),
(N'VietJet Air',      N'VJ654', N'Đà Nẵng',          N'Hà Nội',           DATEADD(day,5,GETDATE()), DATEADD(hour,1,DATEADD(day,5,GETDATE())),    900000, 100, 'img/flight/5.jpg'),
(N'Pacific Airlines', N'BL100', N'Hà Nội',           N'Đà Lạt',           DATEADD(day,6,GETDATE()), DATEADD(hour,2,DATEADD(day,6,GETDATE())),   1300000,  55, 'img/flight/6.jpg');
GO

IF NOT EXISTS (SELECT TOP 1 1 FROM Hotels)
INSERT INTO Hotels (Name, Location, Stars, PricePerNight, HasPool, ImageUrl) VALUES
(N'Hanoi Pearl Hotel',          N'Hà Nội',          5, 2200000, 1, 'img/hotel/1.jpg'),
(N'Saigon Star Hotel',          N'TP. Hồ Chí Minh', 4, 1800000, 1, 'img/hotel/2.jpg'),
(N'Danang Beach Resort',        N'Đà Nẵng',         5, 3500000, 1, 'img/hotel/3.jpg'),
(N'Nha Trang Palace Hotel',     N'Nha Trang',       4, 1500000, 1, 'img/hotel/4.jpg'),
(N'Phu Quoc Island Resort',     N'Phú Quốc',        5, 4200000, 1, 'img/hotel/5.jpg'),
(N'Hoi An Ancient House Hotel', N'Hội An',          3,  900000, 0, 'img/hotel/6.jpg'),
(N'Dalat Flower Hotel',         N'Đà Lạt',          3,  750000, 0, 'img/hotel/7.jpg'),
(N'Ha Long Bay Cruise Hotel',   N'Hạ Long',         4, 2800000, 0, 'img/hotel/8.jpg');
GO

IF NOT EXISTS (SELECT TOP 1 1 FROM Tours)
INSERT INTO Tours (Name, Destination, DurationDays, Price, Description, ImageUrl) VALUES
(N'Du thuyền Hạ Long Bay',      N'Hạ Long',  2, 3500000, N'Khám phá kỳ quan thiên nhiên Vịnh Hạ Long.',                       'img/tour/1.jpg'),
(N'Khám phá Phố Cổ Hội An',    N'Hội An',   3, 2800000, N'Dạo bộ phố cổ, thả đèn hoa đăng trên sông Hoài.',                 'img/tour/2.jpg'),
(N'Trekking Sapa – Fansipan',   N'Sapa',     4, 4200000, N'Chinh phục đỉnh Fansipan – Nóc nhà Đông Dương.',                  'img/tour/3.jpg'),
(N'Khám phá Phú Quốc',         N'Phú Quốc', 5, 6500000, N'Tắm biển, lặn san hô, hải sản tươi ngon.',                        'img/tour/4.jpg'),
(N'Tour Đà Nẵng – Bà Nà Hills',N'Đà Nẵng',  3, 3200000, N'Cầu Vàng, Làng Pháp Bà Nà Hills, bãi biển Mỹ Khê.',              'img/tour/5.jpg'),
(N'Khám phá Tây Nguyên',       N'Đà Lạt',   3, 2500000, N'Vườn hoa, thác Datanla, làng văn hóa Cơ Ho.',                     'img/tour/6.jpg'),
(N'Hành trình Cố đô Huế',      N'Huế',      2, 1800000, N'Đại Nội, lăng tẩm triều Nguyễn, cơm vua.',                        'img/tour/7.jpg'),
(N'Tour Mũi Né – Bình Thuận',  N'Mũi Né',   3, 2200000, N'Đồi cát bay, suối Tiên, bãi biển miền Nam.',                      'img/tour/8.jpg');
GO

IF NOT EXISTS (SELECT TOP 1 1 FROM Transfers)
INSERT INTO Transfers (Type, FromLocation, ToLocation, DepartureTime, Price, Capacity, ImageUrl) VALUES
(N'Taxi',      N'Sân bay Nội Bài',       N'Trung tâm Hà Nội',   DATEADD(hour,2,GETDATE()),  350000, 4,  'img/transfer/1.jpg'),
(N'Taxi',      N'Sân bay Tân Sơn Nhất',  N'Trung tâm TP.HCM',   DATEADD(hour,3,GETDATE()),  280000, 4,  'img/transfer/2.jpg'),
(N'Limousine', N'Hà Nội',                N'Hạ Long',             DATEADD(day,1,GETDATE()),   250000, 9,  'img/transfer/3.jpg'),
(N'Bus',       N'TP. Hồ Chí Minh',       N'Mũi Né',              DATEADD(day,1,GETDATE()),   150000, 40, 'img/transfer/4.jpg'),
(N'Bus',       N'Đà Nẵng',               N'Hội An',              DATEADD(hour,1,GETDATE()),   50000, 25, 'img/transfer/5.jpg'),
(N'Train',     N'Hà Nội',                N'TP. Hồ Chí Minh',     DATEADD(day,1,GETDATE()),   900000, 60, 'img/transfer/6.jpg'),
(N'Limousine', N'Sân bay Đà Nẵng',       N'Hội An',              DATEADD(hour,4,GETDATE()),  180000, 7,  'img/transfer/7.jpg'),
(N'Taxi',      N'Sân bay Phú Quốc',      N'Dương Đông Town',     DATEADD(hour,5,GETDATE()),  200000, 4,  'img/transfer/8.jpg');
GO

-- USERS — mật khẩu hash thực tế cần dùng BCrypt khi deploy
-- '123456' chỉ dùng khi test local với DbInitializer
IF NOT EXISTS (SELECT TOP 1 1 FROM Users)
INSERT INTO Users (FullName, Email, PasswordHash, Phone, DateOfBirth, Hometown, CurrentCity, Role, MemberLevel) VALUES
(N'Admin Hệ Thống',  'admin@viettravel.vn',        '123456', '0901234567', '1990-01-01', N'Hà Nội',    N'Hà Nội',          'Admin', N'VIP'),
(N'Huỳnh Ngọc Khôi', 'khoi@example.com',           '123456', '0901234568', '2005-06-07', N'Nha Trang', N'TP. Hồ Chí Minh', 'User',  N'Thành viên thân thiết'),
(N'Nguyễn Văn A',    'nguyenvana@example.com',      '123456', '0912345678', '1995-03-15', N'Hà Nội',    N'Hà Nội',          'User',  N'Thành viên'),
(N'Trần Thị B',      'tranthib@example.com',        '123456', '0923456789', '1998-07-22', N'Đà Nẵng',   N'TP. Hồ Chí Minh', 'User',  N'Thành viên');
GO

IF NOT EXISTS (SELECT TOP 1 1 FROM Bookings)
INSERT INTO Bookings (UserId, BookingType, ReferenceId, TravelDate, GuestCount, TotalAmount, Status, PaymentStatus) VALUES
(2, 'Flight',   1, DATEADD(day,10,GETDATE()), 1, 1850000, 'Confirmed', 'Paid'),
(2, 'Hotel',    3, DATEADD(day,10,GETDATE()), 2, 7000000, 'Confirmed', 'Paid'),
(2, 'Tour',     2, DATEADD(day,15,GETDATE()), 2, 5600000, 'Pending',   'Unpaid'),
(3, 'Car',      1, DATEADD(day,5,GETDATE()),  1, 2400000, 'Confirmed', 'Paid'),
(4, 'Transfer', 1, DATEADD(day,3,GETDATE()),  3, 1050000, 'Confirmed', 'Paid');
GO

IF NOT EXISTS (SELECT TOP 1 1 FROM Reviews)
INSERT INTO Reviews (UserId, ServiceType, ServiceId, Rating, Comment) VALUES
(2, 'Hotel',    3, 5, N'Resort Đà Nẵng cực đẹp, view biển tuyệt vời!'),
(2, 'Tour',     1, 5, N'Du thuyền Hạ Long Bay trải nghiệm tuyệt vời.'),
(3, 'Car',      1, 4, N'Xe sạch sẽ, đón đúng giờ, tài xế thân thiện.'),
(4, 'Hotel',    1, 4, N'Hanoi Pearl Hotel rất tiện nghi, vị trí đẹp.');
GO

-- ============================================================
-- ============================================================
--  BẢNG LOG VOUCHER (Feature inputs + Decision outputs)
-- ============================================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherFeatureLog' AND xtype='U')
CREATE TABLE VoucherFeatureLog (
    Id                    INT IDENTITY(1,1) PRIMARY KEY,
    SessionId             NVARCHAR(64)      NOT NULL DEFAULT '',
    UserId                INT               NULL,
    TotalLogCount         INT               NOT NULL DEFAULT 0,
    -- 7 Feature gửi lên model
    AdminDuration         DECIMAL(12,4)     NOT NULL DEFAULT 0,   -- Tổng giây trang Info
    InformationalDuration DECIMAL(12,4)     NOT NULL DEFAULT 0,   -- Dự phòng
    ProductDuration       DECIMAL(12,4)     NOT NULL DEFAULT 0,   -- Tổng giây trang dịch vụ
    BounceRate            DECIMAL(8,6)      NOT NULL DEFAULT 0,   -- 1.0 nếu 1 log duy nhất
    ExitRate              DECIMAL(8,6)      NOT NULL DEFAULT 0,   -- 0.1 đã mua / 0.4 chưa
    AvgPageValues         DECIMAL(10,4)     NOT NULL DEFAULT 0,   -- TB PageValues session
    WeekendVal            INT               NOT NULL DEFAULT 0,   -- 1=cuối tuần, 0=ngày thường
    -- Tóm tắt hành vi
    PagesVisited          NVARCHAR(200)     NOT NULL DEFAULT '',  -- "Tour,Hotel,Flight"
    UniquePageCount       INT               NOT NULL DEFAULT 0,
    ComputedAt            DATETIME2         NOT NULL DEFAULT GETDATE()
);
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherDecisionLog' AND xtype='U')
CREATE TABLE VoucherDecisionLog (
    Id                    INT IDENTITY(1,1) PRIMARY KEY,
    SessionId             NVARCHAR(64)      NOT NULL DEFAULT '',
    UserId                INT               NULL,
    FeatureLogId          INT               NULL,   -- FK -> VoucherFeatureLog.Id
    VoucherCode           NVARCHAR(50)      NULL,
    -- Kết quả model
    ModelPredictedRevenue INT               NOT NULL DEFAULT -1,  -- 0=sẽ không mua,1=sẽ mua,-1=lỗi
    ModelDecidedGrant     BIT               NOT NULL DEFAULT 0,   -- Model quyết định cấp?
    DiscountPercent       INT               NOT NULL DEFAULT 0,
    DecisionReason        NVARCHAR(500)     NOT NULL DEFAULT '',  -- debug_info từ Python
    -- Kết quả thực tế (cập nhật sau khi khách dùng hoặc hết hạn)
    ActuallyUsed          BIT               NULL,   -- NULL=chưa biết
    ActuallyPurchased     BIT               NULL,
    -- Đánh giá độ chính xác model:
    --   Grant=1 & Purchased=0 → Đúng (khách cần voucher mới mua)
    --   Grant=1 & Purchased=1 → Sai  (model cấp nhưng khách tự mua rồi)
    --   Grant=0 & Purchased=1 → Đúng (model biết khách tự mua, không lãng phí voucher)
    --   Grant=0 & Purchased=0 → Sai  (lẽ ra nên cấp để kích mua)
    IsModelCorrect        BIT               NULL,   -- NULL=chưa đủ data để đánh giá
    DecidedAt             DATETIME2         NOT NULL DEFAULT GETDATE(),
    EvaluatedAt           DATETIME2         NULL
);
GO

-- FK mềm (không bắt buộc để tránh lỗi nếu FeatureLog bị xóa)
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_VoucherDecision_Feature'
)
ALTER TABLE VoucherDecisionLog
    ADD CONSTRAINT FK_VoucherDecision_Feature
    FOREIGN KEY (FeatureLogId) REFERENCES VoucherFeatureLog(Id)
    ON DELETE SET NULL;
GO

-- ── VIEW: Kiểm tra độ chính xác model voucher ─────────────
IF EXISTS (SELECT * FROM sysobjects WHERE name='vw_VoucherModelAccuracy' AND xtype='V')
    DROP VIEW vw_VoucherModelAccuracy;
GO

CREATE VIEW vw_VoucherModelAccuracy AS
SELECT
    COUNT(*)                                                                         AS TongQuyetDinh,
    SUM(CASE WHEN ModelDecidedGrant = 1    THEN 1 ELSE 0 END)                       AS SoLanCapVoucher,
    SUM(CASE WHEN ModelDecidedGrant = 0    THEN 1 ELSE 0 END)                       AS SoLanKhongCap,
    SUM(CASE WHEN IsModelCorrect    = 1    THEN 1 ELSE 0 END)                       AS SoDung,
    SUM(CASE WHEN IsModelCorrect    = 0    THEN 1 ELSE 0 END)                       AS SoSai,
    SUM(CASE WHEN IsModelCorrect    IS NULL THEN 1 ELSE 0 END)                      AS ChuaDanhGia,
    -- Accuracy % (chỉ tính trên quyết định đã có kết quả thực tế)
    CASE
        WHEN SUM(CASE WHEN IsModelCorrect IS NOT NULL THEN 1 ELSE 0 END) > 0
        THEN CAST(
            SUM(CASE WHEN IsModelCorrect = 1 THEN 1.0 ELSE 0 END) * 100.0
            / SUM(CASE WHEN IsModelCorrect IS NOT NULL THEN 1 ELSE 0 END)
            AS DECIMAL(5,2))
        ELSE NULL
    END                                                                              AS AccuracyPhanTram,
    -- Tỉ lệ voucher đã cấp được dùng thực tế
    CASE
        WHEN SUM(CASE WHEN ModelDecidedGrant = 1 AND ActuallyUsed IS NOT NULL THEN 1 ELSE 0 END) > 0
        THEN CAST(
            SUM(CASE WHEN ModelDecidedGrant = 1 AND ActuallyUsed = 1 THEN 1.0 ELSE 0 END) * 100.0
            / SUM(CASE WHEN ModelDecidedGrant = 1 AND ActuallyUsed IS NOT NULL THEN 1 ELSE 0 END)
            AS DECIMAL(5,2))
        ELSE NULL
    END                                                                              AS TiLeDungVoucher
FROM VoucherDecisionLog;
GO

--  KIỂM TRA
-- ============================================================
PRINT '=== Kiểm tra dữ liệu ==='
SELECT 'Cars'             AS [Bảng], COUNT(*) AS [Số bản ghi] FROM Cars             UNION ALL
SELECT 'Flights',                    COUNT(*)                  FROM Flights           UNION ALL
SELECT 'Hotels',                     COUNT(*)                  FROM Hotels            UNION ALL
SELECT 'Tours',                      COUNT(*)                  FROM Tours             UNION ALL
SELECT 'Transfers',                  COUNT(*)                  FROM Transfers         UNION ALL
SELECT 'Rentals',                    COUNT(*)                  FROM Rentals           UNION ALL
SELECT 'Users',                      COUNT(*)                  FROM Users             UNION ALL
SELECT 'Bookings',                   COUNT(*)                  FROM Bookings          UNION ALL
SELECT 'Reviews',                    COUNT(*)                  FROM Reviews           UNION ALL
SELECT 'LuatFPGrowth (chờ nạp)',     COUNT(*)                  FROM LuatFPGrowth      UNION ALL
SELECT 'UserBehaviorLogs',           COUNT(*)                  FROM UserBehaviorLogs  UNION ALL
SELECT 'VouchersIssued',             COUNT(*)                  FROM VouchersIssued    UNION ALL
SELECT 'VoucherFeatureLog',          COUNT(*)                  FROM VoucherFeatureLog UNION ALL
SELECT 'VoucherDecisionLog',         COUNT(*)                  FROM VoucherDecisionLog;
GO

PRINT N'✅ TravelDb đã sẵn sàng!'
PRINT N'   Lưu ý: LuatFPGrowth sẽ được nạp từ Tourism_DB qua Python API /api/train-rules'
GO
