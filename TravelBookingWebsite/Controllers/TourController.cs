using Microsoft.AspNetCore.Mvc;
using System.Net.Http;
using System.Threading.Tasks;
using System;
using Microsoft.Extensions.Configuration;
namespace TravelBookingWebsite.Controllers
{
    public class TourController : Controller
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;

        // Tiêm (Inject) cấu hình và HttpClientFactory vào Controller
        public TourController(IHttpClientFactory httpClientFactory, IConfiguration configuration)
        {
            _httpClientFactory = httpClientFactory;
            _configuration = configuration;
        }

        [HttpGet]
        public async Task<IActionResult> SearchTour(string query)
        {
            if (string.IsNullOrEmpty(query))
            {
                return Json(new { status = "error", message = "Nhập chữ vào đã đại ca ơi!" });
            }

            string apiKey = _configuration["RapidAPI_Tour:ApiKey"];
            string apiHost = _configuration["RapidAPI_Tour:TourRadarHost"];
            var client = _httpClientFactory.CreateClient();

            try
            {
                // ------------------------------------------------------------------
                // BƯỚC 1: Gọi API phụ để tra cứu ID từ cái CHỮ người dùng gõ
                // Endpoint "suggest" này giúp biến "vietnam" -> ID 2358 ngầm bên dưới
                // ------------------------------------------------------------------
                var suggestRequest = new HttpRequestMessage
                {
                    Method = HttpMethod.Get,
                    RequestUri = new Uri($"https://{apiHost}/tours/list?query={Uri.EscapeDataString(query)}")
                };
                suggestRequest.Headers.Add("x-rapidapi-key", apiKey);
                suggestRequest.Headers.Add("x-rapidapi-host", apiHost);

                string locationId = "";
                string locationType = "country"; // Mặc định hoặc lấy động từ API

                using (var suggestResponse = await client.SendAsync(suggestRequest))
                {
                    if (suggestResponse.IsSuccessStatusCode)
                    {
                        var suggestBody = await suggestResponse.Content.ReadAsStringAsync();

                        // Phân tích cú pháp JSON để lấy cái ID đầu tiên tìm được
                        using (var doc = System.Text.Json.JsonDocument.Parse(suggestBody))
                        {
                            var root = doc.RootElement;
                            // Thường kết quả nằm trong mảng data hoặc items, ví dụ: data[0].id
                            if (root.TryGetProperty("data", out var dataArray) && dataArray.GetArrayLength() > 0)
                            {
                                var firstResult = dataArray[0];
                                locationId = firstResult.GetProperty("id").ToString();

                                if (firstResult.TryGetProperty("type", out var typeProp))
                                {
                                    locationType = typeProp.ToString(); // Lấy loại địa danh: country, city...
                                }
                            }
                        }
                    }
                }

                // Nếu không tìm thấy ID nào khớp với chữ người dùng nhập thì báo lỗi luôn
                if (string.IsNullOrEmpty(locationId))
                {
                    return Json(new { status = "error", message = $"Không tìm thấy địa danh nào tên là '{query}'" });
                }

                // ------------------------------------------------------------------
                // BƯỚC 2: Có ID số rồi (VD: 2358), giờ bắn vào API lấy Tour như cũ
                // ------------------------------------------------------------------
                var tourRequest = new HttpRequestMessage
                {
                    Method = HttpMethod.Get,
                    RequestUri = new Uri($"https://{apiHost}/tours/list?locationType={locationType}&locationId={locationId}&pm3Days=false")
                };
                tourRequest.Headers.Add("x-rapidapi-key", apiKey);
                tourRequest.Headers.Add("x-rapidapi-host", apiHost);

                using (var tourResponse = await client.SendAsync(tourRequest))
                {
                    tourResponse.EnsureSuccessStatusCode();
                    var body = await tourResponse.Content.ReadAsStringAsync();

                    // Trả JSON danh sách tour về cho Frontend vẽ giao diện
                    return Content(body, "application/json");
                }
            }
            catch (Exception ex)
            {
                return Json(new { status = "error", message = "Lỗi hệ thống: " + ex.Message });
            }
        }
        public IActionResult Index()
        {
            // Lệnh này sẽ tự động tìm và render file file Views/Tour/Index.cshtml
            return View();
        }
    }
}
