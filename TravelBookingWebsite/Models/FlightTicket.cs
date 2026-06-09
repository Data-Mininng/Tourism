using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace TravelBookingWebsite.Models
{
    // 1. Class dùng để truyền sang View hiển thị
    public class FlightTicket
    {
        public string Airline { get; set; }
        public string FlightNumber { get; set; }
        public string OriginCode { get; set; }
        public string DestinationCode { get; set; }
        public string DepartureTime { get; set; }
        public string ArrivalTime { get; set; }
        public string Duration { get; set; }
        public decimal Price { get; set; }
        public string Currency { get; set; }
        public string AirlineLogo { get; set; } // Thêm logo hãng bay
    }

    // ==========================================
    // CÁC CLASS DƯỚI ĐÂY ĐỂ ĐỌC JSON TỪ GOOGLE API
    // ==========================================
    public class GoogleFlightResponse
    {
        [JsonPropertyName("data")]
        public FlightData Data { get; set; }
    }


    public class FlightData
    {
        [JsonPropertyName("itineraries")]
        public FlightItineraries Itineraries { get; set; }
    }

    public class FlightItineraries
    {
        [JsonPropertyName("topFlights")]
        public List<TopFlight> TopFlights { get; set; }
    }

    public class TopFlight
    {
        [JsonPropertyName("departure_time")]
        public string DepartureTime { get; set; }

        [JsonPropertyName("arrival_time")]
        public string ArrivalTime { get; set; }

        [JsonPropertyName("duration")]
        public FlightDuration Duration { get; set; }

        [JsonPropertyName("flights")]
        public List<FlightDetail> Flights { get; set; }

        [JsonPropertyName("price")]
        public decimal Price { get; set; }

        [JsonPropertyName("airline_logo")]
        public string AirlineLogo { get; set; }
    }

    public class FlightDuration
    {
        [JsonPropertyName("text")]
        public string Text { get; set; }
    }

    public class FlightDetail
    {
        [JsonPropertyName("departure_airport")]
        public AirportInfo DepartureAirport { get; set; }

        [JsonPropertyName("arrival_airport")]
        public AirportInfo ArrivalAirport { get; set; }

        [JsonPropertyName("airline")]
        public string Airline { get; set; }

        [JsonPropertyName("flight_number")]
        public string FlightNumber { get; set; }
    }

    public class AirportInfo
    {
        [JsonPropertyName("airport_code")]
        public string AirportCode { get; set; }
    }
}