namespace TravelBookingWebsite.Models
{
    public class AirportResponse
    {
        public List<AirportPlace> Places { get; set; }
    }

    public class AirportPlace
    {
        public string SkyId { get; set; }
        public string Name { get; set; }
        public string CityName { get; set; }
        public string CountryName { get; set; }
        public string PlaceType { get; set; }
    }
}