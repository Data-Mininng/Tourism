using System.ComponentModel.DataAnnotations;

namespace TravelApp.Models;

public class Car
{
    public int Id { get; set; }
    [Required]
    public string Brand { get; set; } = string.Empty;
    [Required]
    public string Model { get; set; } = string.Empty;
    public int Year { get; set; }
    public decimal PricePerDay { get; set; }
    public bool IsAvailable { get; set; }

    /// <summary>Đường dẫn ảnh đại diện, VD: img/car/1.jpg</summary>
    [MaxLength(300)]
    public string ImageUrl { get; set; } = "img/car/default.jpg";

    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime UpdatedAt { get; set; } = DateTime.Now;
}

public class Rental
{
    public int Id { get; set; }
    public int CarId { get; set; }
    public string CustomerName { get; set; } = string.Empty;
    public DateTime RentDate { get; set; }
    public DateTime ReturnDate { get; set; }
    public decimal TotalPrice { get; set; }
}
