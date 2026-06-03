using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.SqlClient; // Thư viện truy vấn DB chuẩn
using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using TravelBookingWebsite.Models; // Tên Project của mày, nhớ check lại cái này

namespace TravelBookingWebsite.Controllers
{
    public class TestFlowController : Controller
    {
        // KẾT NỐI CHUẨN VÀO DATABASE "Tourism_DB" CỦA MÀY
        private readonly string _connectionString = "Server=.;Database=Tourism_DB;Trusted_Connection=True;TrustServerCertificate=True;";

        public async Task<IActionResult> Index(string cartItem = "DV_Ve_May_Bay")
        {
            // Truyền hành vi khách hàng ra View
            ViewBag.CartItem = cartItem;

            string aiRecommendation = "";
            double ruleConfidence = 0;

            // ==========================================
            // LUỒNG 1: TRUY VẤN CSDL XEM AI ĐÃ TRAIN RA LUẬT GÌ
            // ==========================================
            try
            {
                using (SqlConnection conn = new SqlConnection(_connectionString))
                {
                    await conn.OpenAsync();

                    // SỬA LẠI TÊN CỘT CHUẨN XÁC THEO FILE RULE_GENERATOR.PY
                    string query = "SELECT TOP 1 DichVu_GoiY, Do_Tin_Cay_Confidence FROM Luat_FPGrowth WHERE DichVu_Goc LIKE '%' + @Antecedent + '%' ORDER BY Do_Tin_Cay_Confidence DESC";

                    using (SqlCommand cmd = new SqlCommand(query, conn))
                    {
                        cmd.Parameters.AddWithValue("@Antecedent", cartItem);

                        using (SqlDataReader reader = await cmd.ExecuteReaderAsync())
                        {
                            if (reader.Read())
                            {
                                // Lấy trực tiếp tên cột tiếng Việt, không cần replace vì Python đã ép kiểu String sạch sẽ
                                aiRecommendation = reader["DichVu_GoiY"].ToString().Trim();

                                ruleConfidence = Convert.ToDouble(reader["Do_Tin_Cay_Confidence"]);
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                ViewBag.DbError = "Lỗi chọc vào SQL Server: " + ex.Message;
            }

            // Đẩy cái luật thật ra View cho thầy cô xem
            ViewBag.AiRule = aiRecommendation;
            ViewBag.Confidence = Math.Round(ruleConfidence * 100, 2); // Đổi ra phần trăm %

            var hotelList = new List<HotelDto>();

            // ==========================================
            // LUỒNG 2: NẾU LUẬT KHAI PHÁ BẢO GỢI Ý KHÁCH SẠN, CHỌC SANG LITEAPI LẤY ẢNH
            // ==========================================
            if (aiRecommendation.Contains("DV_Khach_San_Resort"))
            {
                using (var client = new HttpClient())
                {
                    // LẤY KEY SANDBOX CỦA LITEAPI NÉM LẠI VÀO ĐÂY
                    client.DefaultRequestHeaders.Add("X-API-Key", "sand_88c1802f-ae53-4b6c-87ff-12e890148264");

                    var response = await client.GetAsync("https://api.liteapi.travel/v3.0/data/hotels?countryCode=VN&limit=3");
                    if (response.IsSuccessStatusCode)
                    {
                        var json = await response.Content.ReadAsStringAsync();
                        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                        var apiData = JsonSerializer.Deserialize<LiteApiHotelResponse>(json, options);

                        if (apiData?.Data != null)
                        {
                            hotelList = apiData.Data;
                        }
                    }
                }
            }

            return View(hotelList);
        }
    }
}