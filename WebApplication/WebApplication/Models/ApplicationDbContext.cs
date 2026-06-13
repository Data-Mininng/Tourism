using Microsoft.EntityFrameworkCore;
using TravelApp.Models;

namespace TravelApp.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options) { }

        // ── DbSet cũ (GIỮ NGUYÊN) ──────────────────────────────────────
        public DbSet<Car>      Cars      { get; set; }
        public DbSet<Flight>   Flights   { get; set; }
        public DbSet<Hotel>    Hotels    { get; set; }
        public DbSet<Tour>     Tours     { get; set; }
        public DbSet<Transfer> Transfers { get; set; }
        public DbSet<Rental>   Rentals   { get; set; }
        public DbSet<User>     Users     { get; set; }
        public DbSet<Booking>  Bookings  { get; set; }
        public DbSet<Review>   Reviews   { get; set; }

        // ── DbSet MỚI THÊM (3 bảng AI + 2 bảng log voucher) ────────────
        public DbSet<LuatFPGrowth>       LuatFPGrowth       { get; set; }
        public DbSet<UserBehaviorLog>    UserBehaviorLogs   { get; set; }
        public DbSet<VoucherIssued>      VouchersIssued     { get; set; }
        public DbSet<VoucherFeatureLog>  VoucherFeatureLogs { get; set; }
        public DbSet<VoucherDecisionLog> VoucherDecisionLogs { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Cấu hình cũ (GIỮ NGUYÊN)
            modelBuilder.Entity<Booking>()
                .HasOne(b => b.User)
                .WithMany(u => u.Bookings)
                .HasForeignKey(b => b.UserId)
                .OnDelete(DeleteBehavior.SetNull);

            modelBuilder.Entity<Review>()
                .HasOne(r => r.User)
                .WithMany(u => u.Reviews)
                .HasForeignKey(r => r.UserId)
                .OnDelete(DeleteBehavior.SetNull);
        }
    }
}
