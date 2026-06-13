using System.ComponentModel.DataAnnotations;

namespace TravelApp.Models;

public class Hotel
{
    public int Id { get; set; }
    [Required]
    public string Name { get; set; } = string.Empty;
    public string Location { get; set; } = string.Empty;
    public int Stars { get; set; }
    public decimal PricePerNight { get; set; }
    public bool HasPool { get; set; }

    /// <summary>Đường dẫn ảnh đại diện, VD: img/hotel/1.jpg</summary>
    [MaxLength(300)]
    public string ImageUrl { get; set; } = "img/hotel/default.jpg";

    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime UpdatedAt { get; set; } = DateTime.Now;
}
