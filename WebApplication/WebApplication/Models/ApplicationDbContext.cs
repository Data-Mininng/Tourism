using Microsoft.EntityFrameworkCore;
using TravelApp.Models; // Khai báo namespace chứa các Models

namespace TravelApp.Data // Tùy thuộc vào namespace hiện tại của bạn
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options) { }

        // Các DbSet cũ của bạn (giữ nguyên)
        public DbSet<Car> Cars { get; set; }
        public DbSet<Flight> Flights { get; set; }
        public DbSet<Hotel> Hotels { get; set; }
        public DbSet<Tour> Tours { get; set; }
        public DbSet<Transfer> Transfers { get; set; }
        public DbSet<Rental> Rentals { get; set; }

        // MỚI THÊM: Khai báo 3 DbSet mới
        public DbSet<User> Users { get; set; }
        public DbSet<Booking> Bookings { get; set; }
        public DbSet<Review> Reviews { get; set; }

        // Thiết lập ràng buộc khóa ngoại map với SQL (ON DELETE SET NULL)
        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Cấu hình quan hệ User - Bookings
            modelBuilder.Entity<Booking>()
                .HasOne(b => b.User)
                .WithMany(u => u.Bookings)
                .HasForeignKey(b => b.UserId)
                .OnDelete(DeleteBehavior.SetNull); // Khi xóa User, UserId trong Booking bị set Null thay vì xóa luôn Booking

            // Cấu hình quan hệ User - Reviews
            modelBuilder.Entity<Review>()
                .HasOne(r => r.User)
                .WithMany(u => u.Reviews)
                .HasForeignKey(r => r.UserId)
                .OnDelete(DeleteBehavior.SetNull);
        }
    }
}