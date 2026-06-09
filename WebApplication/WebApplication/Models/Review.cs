using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TravelApp.Models
{
    public class Review
    {
        [Key]
        public int Id { get; set; }

        public int? UserId { get; set; }

        [Required, MaxLength(20)]
        public string ServiceType { get; set; } // Hotel / Tour / Car / Transfer

        public int ServiceId { get; set; }

        [Range(1, 5)]
        public int Rating { get; set; }

        public string Comment { get; set; }
        public DateTime CreatedAt { get; set; } = DateTime.Now;

        // Navigation Property: Trỏ ngược về bảng User
        [ForeignKey("UserId")]
        public User User { get; set; }
    }
}