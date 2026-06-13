using System.ComponentModel.DataAnnotations;

namespace TravelApp.Models;

public class Tour
{
    public int Id { get; set; }
    [Required]
    public string Name { get; set; } = string.Empty;
    public string Destination { get; set; } = string.Empty;
    public int DurationDays { get; set; }
    public decimal Price { get; set; }
    public string Description { get; set; } = string.Empty;

    /// <summary>Đường dẫn ảnh đại diện, VD: img/tour/1.jpg</summary>
    [MaxLength(300)]
    public string ImageUrl { get; set; } = "img/tour/default.jpg";

    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime UpdatedAt { get; set; } = DateTime.Now;
}
