using TravelApp.Data;

namespace TravelApp.Models
{
    public static class DbInitializer
    {
        public static void Seed(ApplicationDbContext db)
        {
            // Nếu DB đã có user thì không seed nữa
            if (db.Users.Any()) return;

            var adminUser = new User
            {
                FullName = "Admin",
                Email = "admin@travel.com",
                PasswordHash = BCrypt.Net.BCrypt.HashPassword("Admin@123"),
                Phone = "0900000000",
                Role = "Admin",
                MemberLevel = "VIP",
                IsActive = true,
                CreatedAt = DateTime.Now,
                UpdatedAt = DateTime.Now
            };

            db.Users.Add(adminUser);
            db.SaveChanges();
        }
    }
}
