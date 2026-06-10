using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Text;
using System.Text.Json;
using TravelApp.Data;

namespace TravelApp.Controllers
{
    [Authorize(Roles = "Admin")]
    public class AdminController : Controller
    {
        private readonly ApplicationDbContext _context;

        public AdminController(ApplicationDbContext context)
        {
            _context = context;
        }

        public IActionResult Dashboard()
        {
            ViewBag.UserCount = _context.Users.Count();
            ViewBag.CarCount = _context.Cars.Count();
            ViewBag.BookingCount = _context.Bookings.Count();
            ViewBag.FlightCount = _context.Flights.Count();
            ViewBag.HotelCount = _context.Hotels.Count();
            ViewBag.TourCount = _context.Tours.Count();
            ViewBag.TransferCount = _context.Transfers.Count();
            return View();
        }

        public async Task<IActionResult> ManageBookings()
        {
            var bookings = await Microsoft.EntityFrameworkCore.EntityFrameworkQueryableExtensions.Include(_context.Bookings, b => b.User)
                .OrderByDescending(b => b.BookingDate)
                .ToListAsync();
            return View(bookings);
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> ApproveBooking(int id)
        {
            var booking = await _context.Bookings.FindAsync(id);
            if (booking != null)
            {
                booking.Status = "Confirmed";
                await _context.SaveChangesAsync();
            }
            return RedirectToAction(nameof(ManageBookings));
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> RejectBooking(int id)
        {
            var booking = await _context.Bookings.FindAsync(id);
            if (booking != null)
            {
                booking.Status = "Rejected";
                await _context.SaveChangesAsync();
            }
            return RedirectToAction(nameof(ManageBookings));
        }



        // GET: /Admin/RuleManagement
        [HttpGet]
        public IActionResult RuleManagement()
        {
            ViewData["Title"] = "Cấu hình thuật toán sinh luật AI";
            return View();
        }

        // POST: /Admin/ExecuteTrainRules
        [HttpPost]
        public async Task<IActionResult> ExecuteTrainRules(double min_support, double min_confidence)
        {
            try
            {
                using (var client = new HttpClient())
                {
                    // Trỏ chính xác đến Server API FastAPI chạy nội bộ
                    client.BaseAddress = new Uri("http://127.0.0.1:5000/");
                    client.Timeout = TimeSpan.FromMinutes(3); // Cấu hình phòng trường hợp tập dữ liệu lớn cần tính toán lâu

                    // Khởi tạo Object đúng cấu trúc cấu hình tham số Schema bên Python (RuleParams)
                    var requestData = new
                    {
                        min_support = min_support,
                        min_confidence = min_confidence
                    };

                    string jsonPayload = JsonSerializer.Serialize(requestData);
                    var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

                    // Bắn dữ liệu sang Endpoint /api/train-rules của FastAPI
                    HttpResponseMessage response = await client.PostAsync("api/train-rules", content);

                    if (response.IsSuccessStatusCode)
                    {
                        string responseString = await response.Content.ReadAsStringAsync();
                        using (JsonDocument doc = JsonDocument.Parse(responseString))
                        {
                            JsonElement root = doc.RootElement;
                            string status = root.GetProperty("status").GetString();

                            if (status == "success")
                            {
                                int totalRules = root.GetProperty("total_rules_generated").GetInt32();
                                return Json(new { status = "success", message = "Cập nhật ma trận luật thành công!", total_rules = totalRules });
                            }
                            else
                            {
                                string errMsg = root.GetProperty("message").GetString();
                                return Json(new { status = "error", message = errMsg });
                            }
                        }
                    }
                    else
                    {
                        return Json(new { status = "error", message = $"Server API Python trả về mã phản hồi lỗi: {response.StatusCode}" });
                    }
                }
            }
            catch (Exception ex)
            {
                return Json(new { status = "error", message = $"Lỗi kết nối hoặc xử lý hệ thống: {ex.Message}" });
            }
        }
    }
}