using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TravelApp.Models
{
    public class Booking
    {
        [Key]
        public int Id { get; set; }

        public int? UserId { get; set; }

        [Required, MaxLength(20)]
        public string BookingType { get; set; } // Flight / Hotel / Tour / Car / Transfer

        public int ReferenceId { get; set; }

        public DateTime BookingDate { get; set; } = DateTime.Now;
        public DateTime? TravelDate { get; set; }

        public int GuestCount { get; set; } = 1;

        [Column(TypeName = "decimal(18,2)")]
        public decimal TotalAmount { get; set; } = 0;

        [Required, MaxLength(20)]
        public string Status { get; set; } = "Pending";

        [Required, MaxLength(20)]
        public string PaymentStatus { get; set; } = "Unpaid";

        public string? Notes { get; set; }
        public DateTime CreatedAt { get; set; } = DateTime.Now;

        // Navigation Property: Trỏ ngược về bảng User
        [ForeignKey("UserId")]
        public User User { get; set; }
    }
}