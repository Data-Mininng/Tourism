using System.ComponentModel.DataAnnotations;

namespace TravelApp.Models;

public class Transfer
{
    public int Id { get; set; }
    [Required]
    public string Type { get; set; } = string.Empty; // Taxi, Bus, Train
    public string FromLocation { get; set; } = string.Empty;
    public string ToLocation { get; set; } = string.Empty;
    public DateTime DepartureTime { get; set; }
    public decimal Price { get; set; }
    public int Capacity { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime UpdatedAt { get; set; } = DateTime.Now;
}