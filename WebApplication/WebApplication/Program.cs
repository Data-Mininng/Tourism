using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.EntityFrameworkCore;
using TravelApp.Data;
using TravelApp.Models;
using TravelApp.Repositories;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllersWithViews();

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// Register Repositories (GIỮ NGUYÊN)
builder.Services.AddScoped<ICarRepository, CarRepository>();
builder.Services.AddScoped<IFlightRepository, FlightRepository>();
builder.Services.AddScoped<IHotelRepository, HotelRepository>();
builder.Services.AddScoped<ITourRepository, TourRepository>();
builder.Services.AddScoped<ITransferRepository, TransferRepository>();

// ── MỚI THÊM: HttpClient để gọi Python API ──────────────────────────
builder.Services.AddHttpClient();

builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath        = "/Account/Login";
        options.AccessDeniedPath = "/Account/AccessDenied";
        options.ExpireTimeSpan   = TimeSpan.FromDays(7);
    });

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    db.Database.EnsureCreated();

    // ── Tạo các bảng AI mới nếu chưa tồn tại (EnsureCreated không tạo bảng mới khi DB đã có) ──
    db.Database.ExecuteSqlRaw(@"
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherFeatureLog' AND xtype='U')
        CREATE TABLE VoucherFeatureLog (
            Id                    INT IDENTITY(1,1) PRIMARY KEY,
            SessionId             NVARCHAR(64)      NOT NULL DEFAULT '',
            UserId                INT               NULL,
            TotalLogCount         INT               NOT NULL DEFAULT 0,
            AdminDuration         DECIMAL(12,4)     NOT NULL DEFAULT 0,
            InformationalDuration DECIMAL(12,4)     NOT NULL DEFAULT 0,
            ProductDuration       DECIMAL(12,4)     NOT NULL DEFAULT 0,
            BounceRate            DECIMAL(8,6)      NOT NULL DEFAULT 0,
            ExitRate              DECIMAL(8,6)      NOT NULL DEFAULT 0,
            AvgPageValues         DECIMAL(10,4)     NOT NULL DEFAULT 0,
            WeekendVal            INT               NOT NULL DEFAULT 0,
            PagesVisited          NVARCHAR(200)     NOT NULL DEFAULT '',
            UniquePageCount       INT               NOT NULL DEFAULT 0,
            ComputedAt            DATETIME2         NOT NULL DEFAULT GETDATE()
        );
    ");

    db.Database.ExecuteSqlRaw(@"
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VoucherDecisionLog' AND xtype='U')
        CREATE TABLE VoucherDecisionLog (
            Id                    INT IDENTITY(1,1) PRIMARY KEY,
            SessionId             NVARCHAR(64)      NOT NULL DEFAULT '',
            UserId                INT               NULL,
            FeatureLogId          INT               NULL,
            VoucherCode           NVARCHAR(50)      NULL,
            ModelPredictedRevenue INT               NOT NULL DEFAULT -1,
            ModelDecidedGrant     BIT               NOT NULL DEFAULT 0,
            DiscountPercent       INT               NOT NULL DEFAULT 0,
            DecisionReason        NVARCHAR(500)     NOT NULL DEFAULT '',
            ActuallyUsed          BIT               NULL,
            ActuallyPurchased     BIT               NULL,
            IsModelCorrect        BIT               NULL,
            DecidedAt             DATETIME2         NOT NULL DEFAULT GETDATE(),
            EvaluatedAt           DATETIME2         NULL,
            CONSTRAINT FK_VoucherDecisionLog_FeatureLog
                FOREIGN KEY (FeatureLogId) REFERENCES VoucherFeatureLog(Id)
        );
    ");

    DbInitializer.Seed(db);
}

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthentication();
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
