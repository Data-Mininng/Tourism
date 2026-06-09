-- ============================================================
--  VIETTRAVEL DATABASE - TravelDb
--  Tương thích: SQL Server 2019+ / SQL Server Express / LocalDB
--  Tạo bởi: VietTravel Setup Script
-- ============================================================

USE master;
GO

-- Xóa DB cũ nếu tồn tại (bỏ comment nếu muốn tạo lại từ đầu)
-- IF EXISTS (SELECT name FROM sys.databases WHERE name = N'TravelDb')
-- BEGIN
--     ALTER DATABASE TravelDb SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
--     DROP DATABASE TravelDb;
-- END
-- GO

-- Tạo Database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'TravelDb')
BEGIN
    CREATE DATABASE TravelDb;
END
GO

USE TravelDb;
GO

-- ============================================================
--  TABLE: Cars (Xe cho thuê)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Cars' AND xtype='U')
BEGIN
    CREATE TABLE Cars (
        Id          INT IDENTITY(1,1) PRIMARY KEY,
        Brand       NVARCHAR(100)  NOT NULL,
        Model       NVARCHAR(100)  NOT NULL,
        Year        INT            NOT NULL DEFAULT 2020,
        PricePerDay DECIMAL(18,2)  NOT NULL DEFAULT 0,
        IsAvailable BIT            NOT NULL DEFAULT 1,
        -- Cột gợi ý mở rộng (bỏ comment để dùng):
        -- ImageUrl    NVARCHAR(500)  NULL,
        -- SeatCount   INT            NULL DEFAULT 5,
        -- LicensePlate NVARCHAR(20)  NULL,
        CreatedAt   DATETIME2      NOT NULL DEFAULT GETDATE(),
        UpdatedAt   DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Rentals (Lịch thuê xe)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Rentals' AND xtype='U')
BEGIN
    CREATE TABLE Rentals (
        Id           INT IDENTITY(1,1) PRIMARY KEY,
        CarId        INT            NOT NULL REFERENCES Cars(Id) ON DELETE CASCADE,
        CustomerName NVARCHAR(200)  NOT NULL,
        RentDate     DATETIME2      NOT NULL,
        ReturnDate   DATETIME2      NOT NULL,
        TotalPrice   DECIMAL(18,2)  NOT NULL DEFAULT 0,
        -- Cột gợi ý mở rộng:
        -- Status       NVARCHAR(20)  NOT NULL DEFAULT 'Pending', -- Pending/Confirmed/Cancelled
        -- PhoneNumber  NVARCHAR(20)  NULL,
        -- Email        NVARCHAR(200) NULL,
        CreatedAt    DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Flights (Chuyến bay)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Flights' AND xtype='U')
BEGIN
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
        -- Cột gợi ý mở rộng:
        -- Class        NVARCHAR(20)  NOT NULL DEFAULT 'Economy', -- Economy/Business/First
        -- DepartureCode NVARCHAR(10)  NULL, -- Mã sân bay VD: SGN, HAN
        -- ArrivalCode  NVARCHAR(10)   NULL,
        -- AirlineLogo  NVARCHAR(500)  NULL,
        CreatedAt      DATETIME2      NOT NULL DEFAULT GETDATE(),
        UpdatedAt      DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Hotels (Khách sạn)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Hotels' AND xtype='U')
BEGIN
    CREATE TABLE Hotels (
        Id           INT IDENTITY(1,1) PRIMARY KEY,
        Name         NVARCHAR(300)  NOT NULL,
        Location     NVARCHAR(300)  NOT NULL,
        Stars        INT            NOT NULL DEFAULT 3,
        PricePerNight DECIMAL(18,2) NOT NULL DEFAULT 0,
        HasPool      BIT            NOT NULL DEFAULT 0,
        -- Cột gợi ý mở rộng:
        -- ImageUrl     NVARCHAR(500)  NULL,
        -- Description  NVARCHAR(MAX)  NULL,
        -- TotalRooms   INT            NULL DEFAULT 50,
        -- Address      NVARCHAR(500)  NULL,
        -- Phone        NVARCHAR(20)   NULL,
        -- Email        NVARCHAR(200)  NULL,
        CreatedAt    DATETIME2      NOT NULL DEFAULT GETDATE(),
        UpdatedAt    DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Tours (Tour du lịch)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tours' AND xtype='U')
BEGIN
    CREATE TABLE Tours (
        Id           INT IDENTITY(1,1) PRIMARY KEY,
        Name         NVARCHAR(300)  NOT NULL,
        Destination  NVARCHAR(200)  NOT NULL,
        DurationDays INT            NOT NULL DEFAULT 1,
        Price        DECIMAL(18,2)  NOT NULL DEFAULT 0,
        Description  NVARCHAR(MAX)  NULL,
        -- Cột gợi ý mở rộng:
        -- ImageUrl     NVARCHAR(500)  NULL,
        -- MaxPeople    INT            NULL DEFAULT 20,
        -- StartDate    DATETIME2      NULL,
        -- Category     NVARCHAR(100)  NULL, -- Biển/Núi/Văn hóa
        -- IsActive     BIT            NOT NULL DEFAULT 1,
        CreatedAt    DATETIME2      NOT NULL DEFAULT GETDATE(),
        UpdatedAt    DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Transfers (Dịch vụ đưa đón)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Transfers' AND xtype='U')
BEGIN
    CREATE TABLE Transfers (
        Id            INT IDENTITY(1,1) PRIMARY KEY,
        Type          NVARCHAR(50)   NOT NULL, -- Taxi / Bus / Train / Limousine
        FromLocation  NVARCHAR(200)  NOT NULL,
        ToLocation    NVARCHAR(200)  NOT NULL,
        DepartureTime DATETIME2      NOT NULL,
        Price         DECIMAL(18,2)  NOT NULL DEFAULT 0,
        Capacity      INT            NOT NULL DEFAULT 4,
        -- Cột gợi ý mở rộng:
        -- AvailableSlots INT         NULL,
        -- DriverName    NVARCHAR(200) NULL,
        -- VehicleCode   NVARCHAR(50)  NULL,
        CreatedAt     DATETIME2      NOT NULL DEFAULT GETDATE(),
        UpdatedAt     DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Users (Tài khoản người dùng)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
BEGIN
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
        Role         NVARCHAR(20)   NOT NULL DEFAULT 'User', -- User / Admin
        MemberLevel  NVARCHAR(50)   NOT NULL DEFAULT 'Thành viên', -- Thành viên / Thân thiết / VIP
        IsActive     BIT            NOT NULL DEFAULT 1,
        CreatedAt    DATETIME2      NOT NULL DEFAULT GETDATE(),
        UpdatedAt    DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Bookings (Lịch sử đặt chỗ)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Bookings' AND xtype='U')
BEGIN
    CREATE TABLE Bookings (
        Id            INT IDENTITY(1,1) PRIMARY KEY,
        UserId        INT            NULL REFERENCES Users(Id) ON DELETE SET NULL,
        BookingType   NVARCHAR(20)   NOT NULL, -- Flight / Hotel / Tour / Car / Transfer
        ReferenceId   INT            NOT NULL, -- Id của bản ghi trong bảng tương ứng
        BookingDate   DATETIME2      NOT NULL DEFAULT GETDATE(),
        TravelDate    DATETIME2      NULL,
        GuestCount    INT            NOT NULL DEFAULT 1,
        TotalAmount   DECIMAL(18,2)  NOT NULL DEFAULT 0,
        Status        NVARCHAR(20)   NOT NULL DEFAULT 'Pending', -- Pending / Confirmed / Cancelled / Completed
        PaymentStatus NVARCHAR(20)   NOT NULL DEFAULT 'Unpaid',  -- Unpaid / Paid / Refunded
        Notes         NVARCHAR(MAX)  NULL,
        CreatedAt     DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  TABLE: Reviews (Đánh giá)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Reviews' AND xtype='U')
BEGIN
    CREATE TABLE Reviews (
        Id          INT IDENTITY(1,1) PRIMARY KEY,
        UserId      INT            NULL REFERENCES Users(Id) ON DELETE SET NULL,
        ServiceType NVARCHAR(20)   NOT NULL, -- Hotel / Tour / Car / Transfer
        ServiceId   INT            NOT NULL,
        Rating      INT            NOT NULL CHECK (Rating BETWEEN 1 AND 5),
        Comment     NVARCHAR(MAX)  NULL,
        CreatedAt   DATETIME2      NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
--  DỮ LIỆU MẪU (SEED DATA)
-- ============================================================

-- Cars
IF NOT EXISTS (SELECT TOP 1 1 FROM Cars)
BEGIN
    INSERT INTO Cars (Brand, Model, Year, PricePerDay, IsAvailable) VALUES
    (N'Toyota',     N'Camry',     2020, 800000,  1),
    (N'Honda',      N'Civic',     2021, 650000,  1),
    (N'Hyundai',    N'Tucson',    2022, 900000,  1),
    (N'Ford',       N'Ranger',    2021, 1100000, 1),
    (N'Mazda',      N'CX-5',      2023, 1000000, 0),
    (N'Kia',        N'Morning',   2020, 500000,  1),
    (N'VinFast',    N'VF 8',      2023, 1200000, 1),
    (N'Mercedes',   N'C200',      2022, 2500000, 1);
END
GO

-- Flights
IF NOT EXISTS (SELECT TOP 1 1 FROM Flights)
BEGIN
    INSERT INTO Flights (Airline, FlightNumber, Departure, Arrival, DepartureTime, ArrivalTime, Price, AvailableSeats) VALUES
    (N'Vietnam Airlines',   N'VN123',  N'Hà Nội',         N'TP. Hồ Chí Minh', DATEADD(day,1,GETDATE()),               DATEADD(hour,2,DATEADD(day,1,GETDATE())),  1850000,  90),
    (N'VietJet Air',        N'VJ456',  N'TP. Hồ Chí Minh',N'Đà Nẵng',         DATEADD(day,2,GETDATE()),               DATEADD(hour,1,DATEADD(day,2,GETDATE())),  750000,  120),
    (N'Bamboo Airways',     N'QH789',  N'Hà Nội',         N'Nha Trang',        DATEADD(day,3,GETDATE()),               DATEADD(hour,2,DATEADD(day,3,GETDATE())),  1200000, 80),
    (N'Vietnam Airlines',   N'VN321',  N'TP. Hồ Chí Minh',N'Phú Quốc',        DATEADD(day,4,GETDATE()),               DATEADD(minute,75,DATEADD(day,4,GETDATE())), 1100000, 60),
    (N'VietJet Air',        N'VJ654',  N'Đà Nẵng',        N'Hà Nội',           DATEADD(day,5,GETDATE()),               DATEADD(hour,1,DATEADD(day,5,GETDATE())),  900000,  100),
    (N'Pacific Airlines',   N'BL100',  N'Hà Nội',         N'Đà Lạt',           DATEADD(day,6,GETDATE()),               DATEADD(hour,2,DATEADD(day,6,GETDATE())),  1300000, 55);
END
GO

-- Hotels
IF NOT EXISTS (SELECT TOP 1 1 FROM Hotels)
BEGIN
    INSERT INTO Hotels (Name, Location, Stars, PricePerNight, HasPool) VALUES
    (N'Hanoi Pearl Hotel',          N'Hà Nội',          5, 2200000, 1),
    (N'Saigon Star Hotel',          N'TP. Hồ Chí Minh', 4, 1800000, 1),
    (N'Danang Beach Resort',        N'Đà Nẵng',         5, 3500000, 1),
    (N'Nha Trang Palace Hotel',     N'Nha Trang',       4, 1500000, 1),
    (N'Phu Quoc Island Resort',     N'Phú Quốc',        5, 4200000, 1),
    (N'Hoi An Ancient House Hotel', N'Hội An',          3, 900000,  0),
    (N'Dalat Flower Hotel',         N'Đà Lạt',          3, 750000,  0),
    (N'Ha Long Bay Cruise Hotel',   N'Hạ Long',         4, 2800000, 0);
END
GO

-- Tours
IF NOT EXISTS (SELECT TOP 1 1 FROM Tours)
BEGIN
    INSERT INTO Tours (Name, Destination, DurationDays, Price, Description) VALUES
    (N'Du thuyền Hạ Long Bay',         N'Hạ Long',      2, 3500000, N'Khám phá kỳ quan thiên nhiên thế giới Vịnh Hạ Long với du thuyền 5 sao.'),
    (N'Khám phá Phố Cổ Hội An',        N'Hội An',       3, 2800000, N'Dạo bộ phố cổ, thả đèn hoa đăng trên sông Hoài, thưởng thức ẩm thực địa phương.'),
    (N'Trekking Sapa – Fansipan',       N'Sapa',         4, 4200000, N'Chinh phục đỉnh Fansipan – Nóc nhà Đông Dương, ngắm ruộng bậc thang mùa lúa chín.'),
    (N'Khám phá Phú Quốc',             N'Phú Quốc',     5, 6500000, N'Tắm biển, lặn san hô, thưởng thức hải sản tươi ngon tại hòn đảo ngọc của Việt Nam.'),
    (N'Tour Đà Nẵng – Bà Nà Hills',    N'Đà Nẵng',      3, 3200000, N'Tham quan Cầu Vàng, Làng Pháp Bà Nà Hills, bãi biển Mỹ Khê.'),
    (N'Khám phá Tây Nguyên',           N'Đà Lạt',       3, 2500000, N'Vườn hoa thành phố, thác Datanla, làng văn hóa Cơ Ho.'),
    (N'Hành trình Cố đô Huế',          N'Huế',          2, 1800000, N'Thăm Đại Nội, lăng tẩm vua chúa triều Nguyễn, thưởng thức cơm vua.'),
    (N'Tour Mũi Né – Bình Thuận',      N'Mũi Né',       3, 2200000, N'Đồi cát bay, suối Tiên, làng chài ngư dân, bãi biển đẹp nhất miền Nam.');
END
GO

-- Transfers
IF NOT EXISTS (SELECT TOP 1 1 FROM Transfers)
BEGIN
    INSERT INTO Transfers (Type, FromLocation, ToLocation, DepartureTime, Price, Capacity) VALUES
    (N'Taxi',      N'Sân bay Nội Bài',    N'Trung tâm Hà Nội',     DATEADD(hour,2,GETDATE()),  350000, 4),
    (N'Taxi',      N'Sân bay Tân Sơn Nhất', N'Trung tâm TP.HCM',   DATEADD(hour,3,GETDATE()),  280000, 4),
    (N'Limousine', N'Hà Nội',             N'Hạ Long',               DATEADD(day,1,GETDATE()),   250000, 9),
    (N'Bus',       N'TP. Hồ Chí Minh',   N'Mũi Né',                DATEADD(day,1,GETDATE()),   150000, 40),
    (N'Bus',       N'Đà Nẵng',           N'Hội An',                 DATEADD(hour,1,GETDATE()),   50000, 25),
    (N'Train',     N'Hà Nội',            N'TP. Hồ Chí Minh',        DATEADD(day,1,GETDATE()),   900000, 60),
    (N'Limousine', N'Sân bay Đà Nẵng',   N'Hội An',                 DATEADD(hour,4,GETDATE()),  180000, 7),
    (N'Taxi',      N'Sân bay Phú Quốc',  N'Dương Đông Town',        DATEADD(hour,5,GETDATE()),  200000, 4);
END
GO

-- ====================================================================================
--  MỚI CẬP NHẬT: Thay đổi PasswordHash từ mã hóa BCrypt sang chữ '123456' thuần túy để test
-- ====================================================================================
IF NOT EXISTS (SELECT TOP 1 1 FROM Users)
BEGIN
    INSERT INTO Users (FullName, Email, PasswordHash, Phone, DateOfBirth, Hometown, CurrentCity, Role, MemberLevel) VALUES
    (N'Admin Hệ Thống',       'admin@viettravel.vn',   '123456',     '0901234567', '1990-01-01', N'Hà Nội',    N'Hà Nội',          'Admin', N'VIP'),
    (N'Huỳnh Ngọc Khôi',     'khoi@example.com',      '123456',      '0901234568', '2005-06-07', N'Nha Trang', N'TP. Hồ Chí Minh', 'User',  N'Thành viên thân thiết'),
    (N'Nguyễn Văn A',        'nguyenvana@example.com', '123456',      '0912345678', '1995-03-15', N'Hà Nội',    N'Hà Nội',          'User',  N'Thành viên'),
    (N'Trần Thị B',          'tranthib@example.com',  '123456',       '0923456789', '1998-07-22', N'Đà Nẵng',   N'TP. Hồ Chí Minh', 'User',  N'Thành viên');
END
GO

-- Bookings mẫu (liên kết với user Id=2 là Khôi)
IF NOT EXISTS (SELECT TOP 1 1 FROM Bookings)
BEGIN
    INSERT INTO Bookings (UserId, BookingType, ReferenceId, TravelDate, GuestCount, TotalAmount, Status, PaymentStatus) VALUES
    (2, 'Flight',   1, DATEADD(day,10,GETDATE()), 1, 1850000, 'Confirmed', 'Paid'),
    (2, 'Hotel',    3, DATEADD(day,10,GETDATE()), 2, 7000000, 'Confirmed', 'Paid'),
    (2, 'Tour',     2, DATEADD(day,15,GETDATE()), 2, 5600000, 'Pending',   'Unpaid'),
    (3, 'Car',      1, DATEADD(day,5,GETDATE()),  1, 2400000, 'Confirmed', 'Paid'),
    (4, 'Transfer', 1, DATEADD(day,3,GETDATE()),  3, 1050000, 'Confirmed', 'Paid');
END
GO

-- Reviews mẫu
IF NOT EXISTS (SELECT TOP 1 1 FROM Reviews)
BEGIN
    INSERT INTO Reviews (UserId, ServiceType, ServiceId, Rating, Comment) VALUES
    (2, 'Hotel', 3, 5, N'Resort Đà Nẵng cực đẹp, view biển tuyệt vời, nhân viên phục vụ rất nhiệt tình!'),
    (2, 'Tour',  1, 5, N'Du thuyền Hạ Long Bay trải nghiệm tuyệt vời, đồ ăn ngon, hướng dẫn viên chuyên nghiệp.'),
    (3, 'Car',   1, 4, N'Xe sạch sẽ, đón đúng giờ, tài xế thân thiện. Sẽ thuê lại.'),
    (4, 'Hotel', 1, 4, N'Hanoi Pearl Hotel rất tiện nghi, vị trí đẹp gần hồ Hoàn Kiếm.');
END
GO

-- ============================================================
--  KIỂM TRA DỮ LIỆU
-- ============================================================
PRINT '=== Kiểm tra dữ liệu đã tạo ==='
SELECT 'Cars'      AS [Bảng], COUNT(*) AS [Số bản ghi] FROM Cars      UNION ALL
SELECT 'Flights',              COUNT(*)                 FROM Flights    UNION ALL
SELECT 'Hotels',               COUNT(*)                 FROM Hotels     UNION ALL
SELECT 'Tours',                COUNT(*)                 FROM Tours      UNION ALL
SELECT 'Transfers',            COUNT(*)                 FROM Transfers  UNION ALL
SELECT 'Rentals',              COUNT(*)                 FROM Rentals    UNION ALL
SELECT 'Users',                COUNT(*)                 FROM Users      UNION ALL
SELECT 'Bookings',             COUNT(*)                 FROM Bookings   UNION ALL
SELECT 'Reviews',              COUNT(*)                 FROM Reviews;
GO

PRINT '✅ TravelDb đã được tạo và seed dữ liệu thành công!'
GO