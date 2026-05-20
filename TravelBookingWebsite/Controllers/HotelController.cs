using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using TravelBookingWebsite.Models; // Nhớ đổi tên namespace cho đúng project của mày

namespace TravelBookingWebsite.Controllers
{
    public class HotelController : Controller
    {
        public async Task<IActionResult> Index()
        {
            // 1. Khởi tạo HttpClient để thực hiện cuộc gọi qua Internet
            using (var client = new HttpClient())
            {
                try
                {
                    // 2. Cấu hình các Header bắt buộc theo tài liệu gốc của LiteAPI
                    // Điền chính xác cái Sandbox Key (sand_88...8264) của mày vào đây
                    client.DefaultRequestHeaders.Add("X-API-Key", "sand_88c1802f-ae53-4b6c-87ff-12e890148264");

                    // 3. Đường dẫn API v3.0 lấy danh sách khách sạn tại Việt Nam (Lấy giới hạn 9 căn để test)
                    string url = "https://api.liteapi.travel/v3.0/data/hotels?countryCode=VN&limit=9";

                    // Gửi request HTTP GET lên server LiteAPI
                    var response = await client.GetAsync(url);

                    // Nếu phía đối tác xác thực Key đúng và trả về dữ liệu thành công (Status 200 OK)
                    if (response.IsSuccessStatusCode)
                    {
                        // Đọc toàn bộ chuỗi JSON trả về
                        var jsonString = await response.Content.ReadAsStringAsync();

                        // Cấu hình bỏ qua việc phân biệt chữ hoa chữ thường khi map dữ liệu
                        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };

                        // Rã băng JSON theo cấu trúc Class LiteApiHotelResponse tao với mày vừa tạo ở Bước 2
                        var hotelResponse = JsonSerializer.Deserialize<LiteApiHotelResponse>(jsonString, options);

                        // Nếu có dữ liệu bên trong mảng "data", ném cái danh sách List<HotelDto> đó ra View
                        if (hotelResponse != null && hotelResponse.Data != null)
                        {
                            return View(hotelResponse.Data);
                        }
                    }
                }
                catch (Exception ex)
                {
                    // Ghi log lỗi nếu hệ thống mất mạng hoặc rớt kết nối giữa chừng
                    Console.WriteLine($"Lỗi gọi API: {ex.Message}");
                }
            }

            // Nếu API lỗi, trả về một danh sách rỗng để tránh giao diện bị crash bể hình
            return View(new System.Collections.Generic.List<HotelDto>());
        }
    }
}