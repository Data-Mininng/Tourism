using Microsoft.AspNetCore.Mvc;
using System.Net.Http;
using System.Threading.Tasks;
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Linq; // Thêm thư viện này để dùng LINQ
using TravelBookingWebsite.Models;

namespace TravelBookingWebsite.Controllers
{
    public class FlightController : Controller
    {
        private readonly IHttpClientFactory _httpClientFactory;

        public FlightController(IHttpClientFactory httpClientFactory)
        {
            _httpClientFactory = httpClientFactory;
        }

        [HttpGet]
        public async Task<IActionResult> Index()
        {
            var client = _httpClientFactory.CreateClient("FlightApi");
            string endpoint = "/api/v1/searchFlights?departure_id=SGN&arrival_id=HAN&outbound_date=2026-06-20&travel_class=ECONOMY&adults=1&currency=VND";

            try
            {
                var response = await client.GetAsync(endpoint);
                response.EnsureSuccessStatusCode();

                var jsonString = await response.Content.ReadAsStringAsync();

                // 1. Ép chuỗi JSON khổng lồ vào Model GoogleFlightResponse
                var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var apiResult = JsonSerializer.Deserialize<GoogleFlightResponse>(jsonString, options);

                // 2. Chuyển đổi data Google sang List vé máy bay của mình
                var ticketList = new List<FlightTicket>();

                if (apiResult?.Data?.Itineraries?.TopFlights != null)
                {
                    foreach (var flight in apiResult.Data.Itineraries.TopFlights)
                    {
                        var firstLeg = flight.Flights?.FirstOrDefault();
                        if (firstLeg != null)
                        {
                            ticketList.Add(new FlightTicket
                            {
                                Airline = firstLeg.Airline,
                                FlightNumber = firstLeg.FlightNumber,
                                OriginCode = firstLeg.DepartureAirport?.AirportCode,
                                DestinationCode = firstLeg.ArrivalAirport?.AirportCode,
                                DepartureTime = flight.DepartureTime,
                                ArrivalTime = flight.ArrivalTime,
                                Duration = flight.Duration?.Text,
                                Price = flight.Price,
                                Currency = "VND",
                                AirlineLogo = flight.AirlineLogo
                            });
                        }
                    }
                }

                // 3. Truyền list vé đã bóc tách ngon lành sang View
                return View(ticketList);
            }
            catch (Exception ex)
            {
                return BadRequest($"Toang rồi thằng anh ơi: {ex.Message}");
            }
        }
    }
}