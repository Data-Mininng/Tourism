-- ══════════════════════════════════════════════════════════════════════
-- SQL Migration  –  Vietnam Travel AI System
-- Chạy script này trên SQL Server (Tourism_DB) nếu chưa có các cột mới
-- ══════════════════════════════════════════════════════════════════════

USE Tourism_DB;
GO

-- ── 1. Thêm cột ContextData vào UserBehaviorLogs (nếu chưa có) ─────────
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'UserBehaviorLogs' AND COLUMN_NAME = 'ContextData'
)
BEGIN
    ALTER TABLE UserBehaviorLogs
        ADD ContextData NVARCHAR(1000) NOT NULL DEFAULT '{}';
    PRINT 'Added ContextData column to UserBehaviorLogs';
END
GO

-- ── 2. Thêm cột IsWeekend vào UserBehaviorLogs (nếu chưa có) ───────────
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'UserBehaviorLogs' AND COLUMN_NAME = 'IsWeekend'
)
BEGIN
    ALTER TABLE UserBehaviorLogs
        ADD IsWeekend BIT NOT NULL DEFAULT 0;
    PRINT 'Added IsWeekend column to UserBehaviorLogs';
END
GO

-- ── 3. Bảng VouchersIssued (tạo mới nếu chưa có) ──────────────────────
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'VouchersIssued')
BEGIN
    CREATE TABLE VouchersIssued (
        Id              INT IDENTITY(1,1) PRIMARY KEY,
        SessionId       NVARCHAR(50)  NOT NULL DEFAULT '',
        UserId          INT           NULL,
        VoucherCode     NVARCHAR(50)  NOT NULL,
        DiscountPercent INT           NOT NULL DEFAULT 10,
        ApplicableType  NVARCHAR(50)  NOT NULL DEFAULT 'All',
        ApplicableId    INT           NULL,
        IssuedAt        DATETIME2     NOT NULL DEFAULT GETDATE(),
        ExpiresAt       DATETIME2     NOT NULL,
        IsUsed          BIT           NOT NULL DEFAULT 0
    );
    PRINT 'Created VouchersIssued table';
END
GO

-- ── 4. Bảng Luat_FPGrowth (tạo mới nếu chưa có) ───────────────────────
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Luat_FPGrowth')
BEGIN
    CREATE TABLE Luat_FPGrowth (
        Id                      INT IDENTITY(1,1) PRIMARY KEY,
        DichVu_Goc              NVARCHAR(500) NOT NULL,
        DichVu_GoiY             NVARCHAR(500) NOT NULL,
        Do_Ho_Tro               DECIMAL(10,4) NOT NULL DEFAULT 0,
        Do_Tin_Cay_Confidence   DECIMAL(10,4) NOT NULL DEFAULT 0,
        Chi_So_Lift             DECIMAL(10,4) NOT NULL DEFAULT 1,
        CreatedAt               DATETIME2     NOT NULL DEFAULT GETDATE()
    );
    PRINT 'Created Luat_FPGrowth table';
END
GO

-- ── 5. Index tăng tốc query voucher theo session ────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_VouchersIssued_Session')
BEGIN
    CREATE INDEX IX_VouchersIssued_Session
        ON VouchersIssued (SessionId, IsUsed, ExpiresAt);
    PRINT 'Created index IX_VouchersIssued_Session';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_UserBehaviorLogs_Session')
BEGIN
    CREATE INDEX IX_UserBehaviorLogs_Session
        ON UserBehaviorLogs (SessionId, LoggedAt DESC);
    PRINT 'Created index IX_UserBehaviorLogs_Session';
END
GO

PRINT '✅ Migration hoàn thành!';
GO
