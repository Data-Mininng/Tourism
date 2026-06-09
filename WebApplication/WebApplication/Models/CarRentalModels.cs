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