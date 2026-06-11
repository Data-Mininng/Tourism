using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TravelApp.Models
{
    public class User
    {
        [Key]
        public int Id { get; set; }

        [Required, MaxLength(200)]
        public string FullName { get; set; } = string.Empty;

        [Required, MaxLength(200)]
        public string Email { get; set; } = string.Empty;

        [Required, MaxLength(500)]
        public string PasswordHash { get; set; } = string.Empty;

        [MaxLength(20)]
        public string? Phone { get; set; }

        [MaxLength(500)]
        public string? AvatarUrl { get; set; }

        public DateTime? DateOfBirth { get; set; }

        [MaxLength(200)]
        public string? Hometown { get; set; }

        [MaxLength(200)]
        public string? CurrentCity { get; set; }

        [Required, MaxLength(20)]
        public string Role { get; set; } = "User";

        [Required, MaxLength(50)]
        public string MemberLevel { get; set; } = "Thành viên";

        public bool IsActive { get; set; } = true;
        public DateTime CreatedAt { get; set; } = DateTime.Now;
        public DateTime UpdatedAt { get; set; } = DateTime.Now;

        // Navigation Properties (Quan hệ 1-N)
        public ICollection<Booking> Bookings { get; set; } = new List<Booking>();
        public ICollection<Review> Reviews { get; set; } = new List<Review>();
    }
}