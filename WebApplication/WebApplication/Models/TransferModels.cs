using System.ComponentModel.DataAnnotations;

namespace TravelApp.Models;

public class Transfer
{
    public int Id { get; set; }
    [Required]
    public string Type { get; set; } = string.Empty; // Taxi, Bus, Train, Limousine
    public string FromLocation { get; set; } = string.Empty;
    public string ToLocation { get; set; } = string.Empty;
    public DateTime DepartureTime { get; set; }
    public decimal Price { get; set; }
    public int Capacity { get; set; }

    /// <summary>Đường dẫn ảnh đại diện, VD: img/transfer/1.jpg</summary>
    [MaxLength(300)]
    public string ImageUrl { get; set; } = "img/transfer/default.jpg";

    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime UpdatedAt { get; set; } = DateTime.Now;
}
