using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Security.Claims;
using System.Text.Json;
using TravelApp.Data;
using TravelApp.Models;

namespace TravelApp.Controllers
{
    public class RecommendationController : Controller
    {
        private readonly ApplicationDbContext _db;
        private readonly IHttpClientFactory   _http;
        private readonly IConfiguration       _cfg;
        private string PythonUrl => _cfg["PythonApi:BaseUrl"] ?? "http://127.0.0.1:5000";

        public RecommendationController(ApplicationDbContext db, IHttpClientFactory http, IConfiguration cfg)
        { _db = db; _http = http; _cfg = cfg; }

        // ── 1. TRANG DÀNH CHO BẠN ────────────────────────────────────────
        public async Task<IActionResult> Index()
        {
            var sessionId = Request.Cookies["vt_session"] ?? "";
            var behaviors = string.IsNullOrEmpty(sessionId) ? new List<UserBehaviorLog>()
                : await _db.UserBehaviorLogs
                    .Where(b => b.SessionId == sessionId && b.LoggedAt > DateTime.Now.AddHours(-4))
                    .OrderByDescending(b => b.LoggedAt).Take(30).ToListAsync();

            var vm = new RecommendationViewModel
            {
                RecentPageTypes = behaviors.Select(b => b.PageType).Distinct().ToList()
            };

            if (!behaviors.Any() || behaviors.Any(b => b.PageType == "Tour"))
                vm.SuggestedTours = await _db.Tours.OrderBy(_ => Guid.NewGuid()).Take(4).ToListAsync();
            if (!behaviors.Any() || behaviors.Any(b => b.PageType == "Hotel"))
                vm.SuggestedHotels = await _db.Hotels.OrderBy(_ => Guid.NewGuid()).Take(4).ToListAsync();
            if (!behaviors.Any() || behaviors.Any(b => b.PageType == "Flight"))
                vm.SuggestedFlights = await _db.Flights.OrderBy(_ => Guid.NewGuid()).Take(4).ToListAsync();
            if (behaviors.Any(b => b.PageType == "Car"))
                vm.SuggestedCars = await _db.Cars.Where(c => c.IsAvailable).Take(4).ToListAsync();
            if (behaviors.Any(b => b.PageType == "Transfer"))
                vm.SuggestedTransfers = await _db.Transfers.Take(4).ToListAsync();

            ViewBag.ActiveVoucher = string.IsNullOrEmpty(sessionId) ? null
                : await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId && !v.IsUsed && v.ExpiresAt > DateTime.Now)
                    .FirstOrDefaultAsync();
            return View(vm);
        }

        // ── 2. API GỢI Ý LUẬT KẾT HỢP ───────────────────────────────────
        // Nhận chuỗi items đầy đủ: "DV_Ve_May_Bay,Den_Da_Nang,NganSach_Cao,Hang_VietJet"
        [HttpGet]
        public async Task<IActionResult> GetSuggestions(string services, int limit = 4)
        {
            if (string.IsNullOrWhiteSpace(services))
                return Json(new { status = "success", data = Array.Empty<object>() });
            try
            {
                // Thử Python API trước
                try
                {
                    var client = _http.CreateClient();
                    client.Timeout = TimeSpan.FromSeconds(4);
                    var url = $"{PythonUrl}/api/recommendations?service_name={Uri.EscapeDataString(services)}&limit={limit}";
                    var res = await client.GetAsync(url);
                    if (res.IsSuccessStatusCode)
                    {
                        var doc = JsonDocument.Parse(await res.Content.ReadAsStringAsync());
                        if (doc.RootElement.TryGetProperty("status", out var st) && st.GetString() == "success")
                        {
                            var list = new List<object>();
                            foreach (var item in doc.RootElement.GetProperty("data").EnumerateArray())
                            {
                                var goiY    = item.GetProperty("DichVu_GoiY").GetString() ?? "";
                                var display = goiY.Split(',', StringSplitOptions.RemoveEmptyEntries)
                                                   .Select(k => ServiceInfo(k.Trim())).ToList();
                                list.Add(new
                                {
                                    dichVu_Goc  = item.GetProperty("DichVu_Goc").GetString(),
                                    dichVu_GoiY = goiY,
                                    do_Tin_Cay  = Math.Round(item.GetProperty("Do_Tin_Cay_Confidence").GetDouble() * 100, 1),
                                    chi_So_Lift = item.TryGetProperty("Chi_So_Lift", out var lp) ? Math.Round(lp.GetDouble(), 2) : 1.0,
                                    displayItems = display
                                });
                            }
                            return Json(new { status = "success", data = list });
                        }
                    }
                }
                catch { /* fallback xuống DB */ }

                // Fallback: query DB — vế trái là tập con của allItems
                var inputSet = services.Split(',', StringSplitOptions.RemoveEmptyEntries)
                                       .Select(s => s.Trim()).ToHashSet();

                var allRules    = await _db.LuatFPGrowth.OrderByDescending(r => r.Do_Tin_Cay_Confidence).ToListAsync();
                var dbResult    = new List<object>();
                var seenOutputs = new HashSet<string>();

                foreach (var rule in allRules)
                {
                    if (dbResult.Count >= limit) break;

                    var ante  = rule.DichVu_Goc.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).ToHashSet();
                    if (!ante.IsSubsetOf(inputSet)) continue;

                    var consq = rule.DichVu_GoiY.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).ToList();
                    if (consq.Any(c => inputSet.Contains(c))) continue;

                    if (!seenOutputs.Add(rule.DichVu_GoiY)) continue;

                    dbResult.Add(new
                    {
                        dichVu_Goc   = rule.DichVu_Goc,
                        dichVu_GoiY  = rule.DichVu_GoiY,
                        do_Tin_Cay   = Math.Round((double)rule.Do_Tin_Cay_Confidence * 100, 1),
                        chi_So_Lift  = Math.Round((double)rule.Chi_So_Lift, 2),
                        displayItems = consq.Select(k => ServiceInfo(k)).ToList()
                    });
                }
                return Json(new { status = "success", data = dbResult });
            }
            catch (Exception ex) { return Json(new { status = "error", message = ex.Message }); }
        }

        // ── 3. LOG HÀNH VI — nhận thêm contextData và allItems ──────────
        [HttpPost]
        public async Task<IActionResult> LogBehavior([FromBody] BehaviorLogRequest req)
        {
            try
            {
                var sessionId = EnsureSession();
                int? userId   = null;
                if (int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int uid)) userId = uid;

                _db.UserBehaviorLogs.Add(new UserBehaviorLog
                {
                    SessionId    = sessionId,
                    UserId       = userId,
                    PageType     = req.PageType     ?? "",
                    ReferenceId  = req.ReferenceId,
                    PageValues   = req.PageValues,
                    TimeOnPage   = req.TimeOnPage,
                    ContextData  = req.ContextData  ?? "{}",   // ← lưu ngữ cảnh đầy đủ
                    IsWeekend    = DateTime.Now.DayOfWeek is DayOfWeek.Saturday or DayOfWeek.Sunday,
                    HasPurchased = false,
                    LoggedAt     = DateTime.Now
                });
                await _db.SaveChangesAsync();
                return Json(new { status = "ok", sessionId });
            }
            catch (Exception ex) { return Json(new { status = "error", message = ex.Message }); }
        }

        // ── 4. XÉT CẤP VOUCHER ───────────────────────────────────────────
        [HttpPost]
        public async Task<IActionResult> CheckVoucher()
        {
            try
            {
                var sessionId = EnsureSession();
                var existing  = await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId && !v.IsUsed && v.ExpiresAt > DateTime.Now)
                    .FirstOrDefaultAsync();
                if (existing != null)
                    return Json(new { hasVoucher = true, code = existing.VoucherCode,
                        discount = existing.DiscountPercent, expiresAt = existing.ExpiresAt.ToString("o"),
                        applicableType = existing.ApplicableType, applicableId = existing.ApplicableId });

                var logs = await _db.UserBehaviorLogs
                    .Where(b => b.SessionId == sessionId && b.LoggedAt > DateTime.Now.AddHours(-2))
                    .ToListAsync();
                if (logs.Count < 2) return Json(new { hasVoucher = false });

                bool giveVoucher = false;
                int  discount    = 10;
                var  totalTime   = logs.Sum(b => b.TimeOnPage);
                var  avgPV       = logs.Average(b => b.PageValues);

                try
                {
                    var features = new {
                        administrative_duration  = 0.0,
                        informational_duration   = Math.Min(logs.Count(b => b.PageType == "Flight") * 30.0 / 600, 1.0),
                        productrelated_duration  = Math.Min(totalTime / 3600, 1.0),
                        bounce_rates             = logs.Count == 1 ? 1.0 : 0.1,
                        exit_rates               = 0.3,
                        page_values              = Math.Min(avgPV / 60.0, 1.0),
                        weekend                  = logs.Any(b => b.IsWeekend) ? 1 : 0
                    };
                    var client  = _http.CreateClient();
                    client.Timeout = TimeSpan.FromSeconds(4);
                    var resp    = await client.PostAsync($"{PythonUrl}/api/predict-voucher",
                        new StringContent(JsonSerializer.Serialize(features), System.Text.Encoding.UTF8, "application/json"));
                    if (resp.IsSuccessStatusCode)
                    {
                        var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
                        giveVoucher = doc.RootElement.GetProperty("need_voucher").GetInt32() == 1;
                        if (doc.RootElement.TryGetProperty("discount_percent", out var dp)) discount = dp.GetInt32();
                    }
                }
                catch
                {
                    var pages = logs.Select(b => b.PageType).Distinct().Count();
                    giveVoucher = totalTime > 120 && avgPV > 5 && pages >= 2 && !logs.Any(b => b.HasPurchased);
                    if (giveVoucher) discount = avgPV > 30 ? 20 : avgPV > 15 ? 15 : 10;
                }

                if (!giveVoucher) return Json(new { hasVoucher = false });

                var top = logs.GroupBy(b => new { b.PageType, b.ReferenceId })
                              .OrderByDescending(g => g.Sum(b => b.TimeOnPage + b.PageValues)).First();
                var code    = "VTV-" + Guid.NewGuid().ToString("N")[..8].ToUpper();
                var voucher = new VoucherIssued
                {
                    SessionId       = sessionId,
                    UserId          = int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int u2) ? u2 : null,
                    VoucherCode     = code,
                    DiscountPercent = discount,
                    ApplicableType  = top.Key.PageType,
                    ApplicableId    = top.Key.ReferenceId,
                    IssuedAt        = DateTime.Now,
                    ExpiresAt       = DateTime.Now.AddMinutes(15),
                    IsUsed          = false
                };
                _db.VouchersIssued.Add(voucher);
                await _db.SaveChangesAsync();
                return Json(new { hasVoucher = true, isNew = true, code, discount,
                    expiresAt = voucher.ExpiresAt.ToString("o"),
                    applicableType = voucher.ApplicableType, applicableId = voucher.ApplicableId });
            }
            catch (Exception ex) { return Json(new { hasVoucher = false, error = ex.Message }); }
        }

        private string EnsureSession()
        {
            var id = Request.Cookies["vt_session"];
            if (!string.IsNullOrEmpty(id)) return id;
            id = Guid.NewGuid().ToString("N")[..16];
            Response.Cookies.Append("vt_session", id, new CookieOptions
                { Expires = DateTimeOffset.Now.AddDays(1), HttpOnly = false, SameSite = SameSiteMode.Lax });
            return id;
        }

        private static object ServiceInfo(string key) => key switch
        {
            "DV_Khach_San_Homestay"    => new { icon = "🏨", url = "/Hotel",    name = "Khách sạn & Homestay" },
            "DV_Ve_May_Bay"            => new { icon = "✈️", url = "/Flight",   name = "Vé máy bay" },
            "DV_Dua_Don_San_Bay"       => new { icon = "🚗", url = "/Transfer", name = "Đưa đón sân bay" },
            "DV_Tour_Va_Khu_Vui_Choi"  => new { icon = "🗺️", url = "/Tour",    name = "Tour & Khu vui chơi" },
            "DV_Thue_Xe_Tu_Lai"        => new { icon = "🚙", url = "/Car",      name = "Thuê xe tự lái" },
            "HD_Tam_Bien"              => new { icon = "🏖️", url = "/Tour",     name = "Tour tắm biển" },
            "HD_Leo_Nui_Trekking"      => new { icon = "⛰️", url = "/Tour",     name = "Tour leo núi" },
            "HD_Tham_Quan_Di_Tich"     => new { icon = "🏛️", url = "/Tour",     name = "Tham quan di tích" },
            "HD_Am_Thuc"               => new { icon = "🍜", url = "/Tour",     name = "Tour ẩm thực" },
            "HD_Check_In"              => new { icon = "📸", url = "/Tour",     name = "Địa điểm check-in" },
            "HD_Nghi_Duong_Chua_Lanh"  => new { icon = "🧘", url = "/Hotel",    name = "Nghỉ dưỡng chữa lành" },
            _                          => new { icon = "📦", url = "/",          name = key.Replace("Den_","").Replace("NganSach_","").Replace("_"," ") }
        };
    }

    public class RecommendationViewModel
    {
        public List<string>   RecentPageTypes    { get; set; } = new();
        public List<Tour>     SuggestedTours     { get; set; } = new();
        public List<Hotel>    SuggestedHotels    { get; set; } = new();
        public List<Flight>   SuggestedFlights   { get; set; } = new();
        public List<Car>      SuggestedCars      { get; set; } = new();
        public List<Transfer> SuggestedTransfers { get; set; } = new();
    }

    public class BehaviorLogRequest
    {
        public string? PageType     { get; set; }
        public int?    ReferenceId  { get; set; }
        public double  PageValues   { get; set; }
        public double  TimeOnPage   { get; set; }
        public string? ContextData  { get; set; }  // ← MỚI
        public string? AllItems     { get; set; }  // ← MỚI: toàn bộ items tích lũy
    }
}
