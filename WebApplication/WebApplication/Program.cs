using Microsoft.AspNetCore.Authentication.Cookies; // MỚI THÊM: Import thư viện Cookie
using Microsoft.EntityFrameworkCore;
using TravelApp.Data;
using TravelApp.Models;
using TravelApp.Repositories;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllersWithViews();

// Add DbContext
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// Register Repositories
builder.Services.AddScoped<ICarRepository, CarRepository>();
builder.Services.AddScoped<IFlightRepository, FlightRepository>();
builder.Services.AddScoped<IHotelRepository, HotelRepository>();
builder.Services.AddScoped<ITourRepository, TourRepository>();
builder.Services.AddScoped<ITransferRepository, TransferRepository>();

// =========================================================================
// 1. ĐĂNG KÝ DỊCH VỤ AUTHENTICATION (MỚI THÊM)
// =========================================================================
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath = "/Account/Login"; // Chuyển hướng về đây nếu chưa đăng nhập
        options.AccessDeniedPath = "/Account/AccessDenied"; // Chuyển hướng nếu không đủ quyền
        options.ExpireTimeSpan = TimeSpan.FromDays(7);
    });

var app = builder.Build();

// Seed database
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    db.Database.EnsureCreated();
    // Giả định DbInitializer của bạn đã được cấu hình đúng
    DbInitializer.Seed(db);
}

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

// =========================================================================
// 2. MIDDLEWARE XÁC THỰC VÀ PHÂN QUYỀN (MỚI THÊM UseAuthentication)
// Thứ tự 2 dòng này cực kỳ quan trọng, không được đảo ngược.
// =========================================================================
app.UseAuthentication(); // Ai đang truy cập? (Đã Login chưa)
app.UseAuthorization();  // Người đó được phép làm gì? (Có quyền vào link này không)

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();