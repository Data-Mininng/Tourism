using System.ComponentModel.DataAnnotations;

namespace TravelApp.Models;

public class Flight
{
    public int Id { get; set; }
    [Required]
    public string Airline { get; set; } = string.Empty;
    public string FlightNumber { get; set; } = string.Empty;
    public string Departure { get; set; } = string.Empty;
    public string Arrival { get; set; } = string.Empty;
    public DateTime DepartureTime { get; set; }
    public DateTime ArrivalTime { get; set; }
    public decimal Price { get; set; }
    public int AvailableSeats { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime UpdatedAt { get; set; } = DateTime.Now;
}