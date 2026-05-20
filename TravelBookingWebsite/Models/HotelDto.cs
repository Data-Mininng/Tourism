using System.Text.Json.Serialization;
using System.Collections.Generic;

namespace TravelBookingWebsite.Models
{
    /// <summary>
    /// Đối tượng vận chuyển dữ liệu khách sạn nhận về từ LiteAPI
    /// </summary>
    public class HotelDto
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("address")]
        public string Address { get; set; }

        [JsonPropertyName("stars")]
        public double Stars { get; set; }

        [JsonPropertyName("city")]
        public string City { get; set; }

        // Link ảnh gốc chuẩn từ LiteAPI
        [JsonPropertyName("main_photo")]
        public string MainPhoto { get; set; }

        [JsonPropertyName("thumbnail")]
        public string Thumbnail { get; set; }
    }

    /// <summary>
    /// Khuôn bọc gói dữ liệu gốc trả về từ LiteAPI v3.0
    /// </summary>
    public class LiteApiHotelResponse
    {
        // Mảng chứa danh sách khách sạn nằm trong thuộc tính "data" của JSON thật
        [JsonPropertyName("data")]
        public List<HotelDto> Data { get; set; }
    }
}