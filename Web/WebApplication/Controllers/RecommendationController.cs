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
        private readonly IHttpClientFactory _http;
        private readonly IConfiguration _cfg;
        private string PythonUrl => _cfg["PythonApi:BaseUrl"] ?? "http://127.0.0.1:5000";

        public RecommendationController(ApplicationDbContext db, IHttpClientFactory http, IConfiguration cfg)
        { _db = db; _http = http; _cfg = cfg; }

        // ── 1. TRANG DÀNH CHO BẠN ────────────────────────────────────────────
        public async Task<IActionResult> Index()
        {
            var sessionId = Request.Cookies["vt_session"] ?? "";

            // Lấy log hành vi trong 4 giờ gần nhất
            var behaviors = string.IsNullOrEmpty(sessionId)
                ? new List<UserBehaviorLog>()
                : await _db.UserBehaviorLogs
                    .Where(b => b.SessionId == sessionId && b.LoggedAt > DateTime.Now.AddHours(-4))
                    .OrderByDescending(b => b.LoggedAt).Take(50).ToListAsync();

            // ── Giải mã ngữ cảnh từ ContextData JSON ──────────────────────
            // Thu thập địa điểm người dùng đã xem
            var visitedLocations = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var visitedServices = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            foreach (var log in behaviors)
            {
                try
                {
                    var ctx = JsonDocument.Parse(log.ContextData ?? "{}").RootElement;
                    // Đọc items[] để lấy Den_*, TuDen_*, service codes
                    if (ctx.TryGetProperty("items", out var itemsArr))
                    {
                        foreach (var item in itemsArr.EnumerateArray())
                        {
                            var s = item.GetString() ?? "";
                            if (s.StartsWith("Den_")) visitedLocations.Add(s.Replace("Den_", ""));
                            if (s.StartsWith("DV_")) visitedServices.Add(s);
                        }
                    }
                }
                catch { /* ContextData bị lỗi JSON, bỏ qua */ }

                // Cũng ghi nhận PageType
                if (!string.IsNullOrEmpty(log.PageType))
                    visitedServices.Add("PageType_" + log.PageType);
            }

            var vm = new RecommendationViewModel
            {
                RecentPageTypes = behaviors.Select(b => b.PageType).Distinct().ToList(),
                VisitedLocations = visitedLocations.ToList(),
                VisitedServices = visitedServices.ToList(),
            };

            // ── Gợi ý thông minh theo địa điểm đã xem ─────────────────────

            // HOTEL: ưu tiên theo location đã ghé
            if (!behaviors.Any() || behaviors.Any(b => b.PageType == "Hotel"))
            {
                if (visitedLocations.Any())
                {
                    // Tìm hotels khớp địa điểm user đã xem
                    var locationFiltered = new List<Hotel>();
                    foreach (var loc in visitedLocations)
                    {
                        var locNorm = NormalizeLocationForDb(loc);
                        var matched = await _db.Hotels
                            .Where(h => EF.Functions.Like(h.Location, $"%{locNorm}%"))
                            .Take(4).ToListAsync();
                        locationFiltered.AddRange(matched);
                    }
                    vm.SuggestedHotels = locationFiltered.DistinctBy(h => h.Id).Take(4).ToList();
                }

                // Fallback nếu không tìm được theo location
                if (!vm.SuggestedHotels.Any())
                    vm.SuggestedHotels = await _db.Hotels.OrderBy(_ => Guid.NewGuid()).Take(4).ToListAsync();
            }

            // FLIGHT: ưu tiên flight đến địa điểm user đã xem khách sạn/tour
            if (!behaviors.Any() || behaviors.Any(b => b.PageType == "Flight"))
            {
                if (visitedLocations.Any())
                {
                    var locFiltered = new List<Flight>();
                    foreach (var loc in visitedLocations)
                    {
                        var locNorm = NormalizeLocationForDb(loc);
                        var matched = await _db.Flights
                            .Where(f => EF.Functions.Like(f.Arrival, $"%{locNorm}%"))
                            .OrderBy(f => f.DepartureTime)
                            .Take(3).ToListAsync();
                        locFiltered.AddRange(matched);
                    }
                    vm.SuggestedFlights = locFiltered.DistinctBy(f => f.Id).Take(4).ToList();
                }

                if (!vm.SuggestedFlights.Any())
                    vm.SuggestedFlights = await _db.Flights.OrderBy(_ => Guid.NewGuid()).Take(4).ToListAsync();
            }

            // TOUR: ưu tiên theo Destination
            if (!behaviors.Any() || behaviors.Any(b => b.PageType == "Tour"))
            {
                if (visitedLocations.Any())
                {
                    var locFiltered = new List<Tour>();
                    foreach (var loc in visitedLocations)
                    {
                        var locNorm = NormalizeLocationForDb(loc);
                        var matched = await _db.Tours
                            .Where(t => EF.Functions.Like(t.Destination, $"%{locNorm}%"))
                            .Take(4).ToListAsync();
                        locFiltered.AddRange(matched);
                    }
                    vm.SuggestedTours = locFiltered.DistinctBy(t => t.Id).Take(4).ToList();
                }

                if (!vm.SuggestedTours.Any())
                    vm.SuggestedTours = await _db.Tours.OrderBy(_ => Guid.NewGuid()).Take(4).ToListAsync();
            }

            // CAR & TRANSFER — không phụ thuộc địa điểm nhiều
            if (behaviors.Any(b => b.PageType == "Car"))
                vm.SuggestedCars = await _db.Cars.Where(c => c.IsAvailable).Take(4).ToListAsync();

            if (behaviors.Any(b => b.PageType == "Transfer"))
                vm.SuggestedTransfers = await _db.Transfers.Take(4).ToListAsync();

            // ── Voucher đang hoạt động ─────────────────────────────────────
            ViewBag.ActiveVoucher = string.IsNullOrEmpty(sessionId) ? null
                : await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId && !v.IsUsed && v.ExpiresAt > DateTime.Now)
                    .FirstOrDefaultAsync();

            return View(vm);
        }

        // ── 2. TRANG VOUCHER CỦA TÔI ─────────────────────────────────────────
        public async Task<IActionResult> MyVouchers()
        {
            var sessionId = Request.Cookies["vt_session"] ?? "";
            int? userId = null;
            if (int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int uid)) userId = uid;

            List<VoucherIssued> vouchers;

            if (userId.HasValue)
            {
                // Người dùng đã đăng nhập → lấy tất cả voucher của họ
                vouchers = await _db.VouchersIssued
                    .Where(v => v.UserId == userId)
                    .OrderByDescending(v => v.IssuedAt)
                    .Take(20).ToListAsync();
            }
            else if (!string.IsNullOrEmpty(sessionId))
            {
                // Chưa đăng nhập → lấy theo session
                vouchers = await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId)
                    .OrderByDescending(v => v.IssuedAt)
                    .Take(20).ToListAsync();
            }
            else
            {
                vouchers = new List<VoucherIssued>();
            }

            return View(vouchers);
        }

        // ── 3. NÚT TEST VOUCHER (cấp ngay 1 voucher test) ──────────────────
        [HttpPost]
        public async Task<IActionResult> TestVoucher()
        {
            try
            {
                var sessionId = EnsureSession();

                // Xóa voucher test cũ của session này (để test lại)
                var oldTest = await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId && v.VoucherCode.StartsWith("TEST-"))
                    .ToListAsync();
                if (oldTest.Any())
                {
                    _db.VouchersIssued.RemoveRange(oldTest);
                    await _db.SaveChangesAsync();
                }

                // Gọi Python với dữ liệu ép để chắc chắn model cấp voucher
                var features = new
                {
                    administrative_duration = 180.0,
                    informational_duration = 0.0,
                    productrelated_duration = 600.0,  // xem sản phẩm rất lâu → model dự đoán không mua → cấp voucher
                    bounce_rates = 0.0,
                    exit_rates = 0.05,
                    page_values = 75.0,   // page_values cao → intent mua nhưng chưa chốt
                    weekend = 1
                };

                int discount = 15;
                bool giveVoucher = false;
                string aiDecision = "fallback";

                try
                {
                    var client = _http.CreateClient();
                    client.Timeout = TimeSpan.FromSeconds(5);
                    var jsonPayload = JsonSerializer.Serialize(features, new JsonSerializerOptions { PropertyNamingPolicy = null });
                    var resp = await client.PostAsync($"{PythonUrl}/api/predict-voucher",
                        new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json"));

                    if (resp.IsSuccessStatusCode)
                    {
                        var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
                        if (doc.RootElement.TryGetProperty("need_voucher", out var nv))
                            giveVoucher = nv.GetInt32() == 1;
                        if (doc.RootElement.TryGetProperty("discount_percent", out var dp) && dp.GetInt32() > 0)
                            discount = dp.GetInt32();
                        if (doc.RootElement.TryGetProperty("debug_info", out var di)
                            && di.TryGetProperty("predicted_revenue_intent", out var ri))
                            aiDecision = ri.GetInt32() == 0 ? "model=0(không mua)→cấp" : "model=1(sẽ mua)→không cấp";
                    }
                }
                catch (Exception ex)
                {
                    // Python offline → fallback: test mode luôn cấp
                    giveVoucher = true;
                    aiDecision = "python_offline_fallback: " + ex.Message;
                }

                // Test mode: nếu model không cấp thì vẫn tạo voucher test để demo UI
                if (!giveVoucher)
                {
                    giveVoucher = true;
                    aiDecision += " [test_override]";
                }

                var code = "TEST-" + Guid.NewGuid().ToString("N")[..6].ToUpper();
                var voucher = new VoucherIssued
                {
                    SessionId = sessionId,
                    UserId = int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int u) ? u : null,
                    VoucherCode = code,
                    DiscountPercent = discount,
                    ApplicableType = "Test",
                    ApplicableId = null,
                    IssuedAt = DateTime.Now,
                    ExpiresAt = DateTime.Now.AddMinutes(30),
                    IsUsed = false,
                };
                _db.VouchersIssued.Add(voucher);
                await _db.SaveChangesAsync();

                return Json(new
                {
                    success = true,
                    code,
                    discount,
                    expiresAt = voucher.ExpiresAt.ToString("o"),
                    aiDecision,
                    isNew = true,
                    applicableType = "Test",
                    hasVoucher = true,
                });
            }
            catch (Exception ex)
            {
                return Json(new { success = false, error = ex.Message });
            }
        }

        // ── 4. API GỢI Ý LUẬT KẾT HỢP ───────────────────────────────────────
        [HttpGet]
        public async Task<IActionResult> GetSuggestions(string services, int limit = 4)
        {
            if (string.IsNullOrWhiteSpace(services))
                return Json(new { status = "success", data = Array.Empty<object>() });
            try
            {
                // Gọi Python API trước
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
                                var goiY = item.GetProperty("DichVu_GoiY").GetString() ?? "";
                                var goc = item.GetProperty("DichVu_Goc").GetString() ?? "";
                                var display = goiY.Split(',', StringSplitOptions.RemoveEmptyEntries)
                                                   .Select(k => ServiceInfo(k.Trim())).ToList();
                                var reason = BuildReason(goc);
                                list.Add(new
                                {
                                    dichVu_Goc = goc,
                                    dichVu_GoiY = goiY,
                                    do_Tin_Cay = Math.Round(item.GetProperty("Do_Tin_Cay_Confidence").GetDouble() * 100, 1),
                                    chi_So_Lift = item.TryGetProperty("Chi_So_Lift", out var lp) ? Math.Round(lp.GetDouble(), 2) : 1.0,
                                    displayItems = display,
                                    lyDoGoiY = reason,
                                });
                            }
                            return Json(new { status = "success", data = list });
                        }
                    }
                }
                catch { /* fallback DB */ }

                // Fallback: query DB
                var inputSet = services.Split(',', StringSplitOptions.RemoveEmptyEntries)
                                        .Select(s => s.Trim()).ToHashSet();
                var allRules = await _db.LuatFPGrowth.OrderByDescending(r => r.Do_Tin_Cay_Confidence).ToListAsync();
                var dbResult = new List<object>();
                var seen = new HashSet<string>();

                foreach (var rule in allRules)
                {
                    if (dbResult.Count >= limit) break;
                    var ante = rule.DichVu_Goc.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).ToHashSet();
                    if (!ante.IsSubsetOf(inputSet)) continue;
                    var consq = rule.DichVu_GoiY.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).ToList();
                    if (consq.Any(c => inputSet.Contains(c))) continue;
                    if (!seen.Add(rule.DichVu_GoiY)) continue;

                    dbResult.Add(new
                    {
                        dichVu_Goc = rule.DichVu_Goc,
                        dichVu_GoiY = rule.DichVu_GoiY,
                        do_Tin_Cay = Math.Round((double)rule.Do_Tin_Cay_Confidence * 100, 1),
                        chi_So_Lift = Math.Round((double)rule.Chi_So_Lift, 2),
                        displayItems = consq.Select(k => ServiceInfo(k)).ToList(),
                        lyDoGoiY = BuildReason(rule.DichVu_Goc),
                    });
                }
                return Json(new { status = "success", data = dbResult });
            }
            catch (Exception ex) { return Json(new { status = "error", message = ex.Message }); }
        }

        // ── 5. LOG HÀNH VI ───────────────────────────────────────────────────
        [HttpPost]
        public async Task<IActionResult> LogBehavior([FromBody] BehaviorLogRequest req)
        {
            try
            {
                var sessionId = EnsureSession();
                int? userId = null;
                if (int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int uid)) userId = uid;

                _db.UserBehaviorLogs.Add(new UserBehaviorLog
                {
                    SessionId = sessionId,
                    UserId = userId,
                    PageType = req.PageType ?? "",
                    ReferenceId = req.ReferenceId,
                    PageValues = req.PageValues,
                    TimeOnPage = req.TimeOnPage,
                    ContextData = req.ContextData ?? "{}",
                    IsWeekend = DateTime.Now.DayOfWeek is DayOfWeek.Saturday or DayOfWeek.Sunday,
                    HasPurchased = false,
                    LoggedAt = DateTime.Now
                });
                await _db.SaveChangesAsync();
                return Json(new { status = "ok", sessionId });
            }
            catch (Exception ex) { return Json(new { status = "error", message = ex.Message }); }
        }

        // ── 6. XÉT CẤP VOUCHER (gọi từ tracker sau mỗi 3 trang) ────────────
        [HttpPost]
        public async Task<IActionResult> CheckVoucher()
        {
            try
            {
                var sessionId = EnsureSession();

                // Đã có voucher còn hiệu lực → trả về luôn (không cấp mới)
                var existing = await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId && !v.IsUsed && v.ExpiresAt > DateTime.Now)
                    .FirstOrDefaultAsync();
                if (existing != null)
                    return Json(new
                    {
                        hasVoucher = true,
                        isNew = false,
                        code = existing.VoucherCode,
                        discount = existing.DiscountPercent,
                        expiresAt = existing.ExpiresAt.ToString("o"),
                        applicableType = existing.ApplicableType,
                        applicableId = existing.ApplicableId
                    });

                // Lấy logs
                var logs = await _db.UserBehaviorLogs
                    .Where(b => b.SessionId == sessionId && b.LoggedAt > DateTime.Now.AddHours(-4))
                    .ToListAsync();

                if (logs.Count < 2) return Json(new { hasVoucher = false });

                // ── Tính features thực từ behavior logs ───────────────────
                double adminDuration = logs.Where(b => b.PageType == "Info").Sum(b => b.TimeOnPage);
                double productDuration = logs.Where(b => b.PageType is "Tour" or "Hotel" or "Flight" or "Car" or "Transfer")
                                            .Sum(b => b.TimeOnPage);
                double avgPV = logs.Any() ? logs.Average(b => b.PageValues) : 0.0;
                double bounceRate = logs.Count == 1 ? 1.0 : 0.0;
                double exitRate = logs.Any(b => b.HasPurchased) ? 0.1 : 0.4;
                int weekendVal = logs.Any(b => b.IsWeekend) ? 1 : 0;

                bool giveVoucher = false;
                int discount = 10;

                // ── Gọi Python model dự đoán Revenue ─────────────────────
                try
                {
                    var features = new
                    {
                        administrative_duration = adminDuration,
                        informational_duration = 0.0,
                        productrelated_duration = productDuration,
                        bounce_rates = bounceRate,
                        exit_rates = exitRate,
                        page_values = avgPV,
                        weekend = weekendVal
                    };

                    var client = _http.CreateClient();
                    client.Timeout = TimeSpan.FromSeconds(5);
                    var jsonPayload = JsonSerializer.Serialize(features, new JsonSerializerOptions { PropertyNamingPolicy = null });
                    var resp = await client.PostAsync($"{PythonUrl}/api/predict-voucher",
                        new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json"));

                    if (!resp.IsSuccessStatusCode)
                        throw new Exception($"Python API error: {resp.StatusCode}");

                    var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
                    if (doc.RootElement.TryGetProperty("need_voucher", out var nv))
                        giveVoucher = nv.GetInt32() == 1;
                    if (doc.RootElement.TryGetProperty("discount_percent", out var dp) && dp.GetInt32() > 0)
                        discount = dp.GetInt32();
                }
                catch (Exception ex)
                {
                    // Python offline → fallback heuristic (KHÔNG dùng if cấp voucher thủ công,
                    // chỉ dùng khi Python không phản hồi)
                    System.Diagnostics.Debug.WriteLine($"[Voucher Fallback] {ex.Message}");
                    var totalTime = logs.Sum(b => b.TimeOnPage);
                    var pages = logs.Select(b => b.PageType).Distinct().Count();
                    giveVoucher = totalTime > 90 && avgPV > 10 && pages >= 2 && !logs.Any(b => b.HasPurchased);
                    if (giveVoucher) discount = avgPV > 40 ? 20 : avgPV > 20 ? 15 : 10;
                }

                if (!giveVoucher) return Json(new { hasVoucher = false });

                // ── Xác định dịch vụ phù hợp nhất để gán voucher ─────────
                string targetType = "Tour";
                int? targetId = null;
                if (logs.Any())
                {
                    var top = logs.GroupBy(b => new { b.PageType, b.ReferenceId })
                                  .OrderByDescending(g => g.Sum(b => b.TimeOnPage + b.PageValues))
                                  .First();
                    targetType = top.Key.PageType;
                    targetId = top.Key.ReferenceId;
                }

                var code = "VTV-" + Guid.NewGuid().ToString("N")[..8].ToUpper();
                var voucher = new VoucherIssued
                {
                    SessionId = sessionId,
                    UserId = int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int u2) ? u2 : null,
                    VoucherCode = code,
                    DiscountPercent = discount,
                    ApplicableType = targetType,
                    ApplicableId = targetId,
                    IssuedAt = DateTime.Now,
                    ExpiresAt = DateTime.Now.AddMinutes(15),
                    IsUsed = false,
                };
                _db.VouchersIssued.Add(voucher);
                await _db.SaveChangesAsync();

                return Json(new
                {
                    hasVoucher = true,
                    isNew = true,
                    code,
                    discount,
                    expiresAt = voucher.ExpiresAt.ToString("o"),
                    applicableType = voucher.ApplicableType,
                    applicableId = voucher.ApplicableId
                });
            }
            catch (Exception ex)
            {
                return Json(new { hasVoucher = false, error = ex.Message });
            }
        }

        // ── PRIVATE HELPERS ──────────────────────────────────────────────────

        private string EnsureSession()
        {
            var id = Request.Cookies["vt_session"];
            if (!string.IsNullOrEmpty(id)) return id;
            id = Guid.NewGuid().ToString("N")[..16];
            Response.Cookies.Append("vt_session", id, new CookieOptions
            {
                Expires = DateTimeOffset.Now.AddDays(1),
                HttpOnly = false,
                SameSite = SameSiteMode.Lax
            });
            return id;
        }

        /// <summary>Chuyển slug địa điểm (Ha_Noi) → chuỗi tìm kiếm DB ("Hà Nội" / "Ha Noi")</summary>
        private static string NormalizeLocationForDb(string slugLoc)
        {
            return (slugLoc ?? "").Replace("_", " ").Trim();
        }

        /// <summary>Tạo câu lý do gợi ý dễ đọc từ antecedent của luật</summary>
        private static string BuildReason(string antecedent)
        {
            if (string.IsNullOrEmpty(antecedent)) return "";
            var parts = antecedent.Split(',', StringSplitOptions.RemoveEmptyEntries)
                .Select(s => s.Trim())
                .Where(s => s.StartsWith("Den_") || s.StartsWith("NganSach_") || s.StartsWith("Hang_")
                         || s.StartsWith("Mua_") || s.StartsWith("KhachSan_"))
                .Select(s =>
                {
                    if (s.StartsWith("Den_")) return "Đến " + s.Replace("Den_", "").Replace("_", " ");
                    if (s.StartsWith("Hang_")) return "Hãng " + s.Replace("Hang_", "").Replace("_", " ");
                    if (s.StartsWith("NganSach_")) return "Ngân sách " + s.Replace("NganSach_", "").Replace("_", " ").ToLower();
                    if (s.StartsWith("Mua_")) return "Mùa " + s.Replace("Mua_", "").ToLower();
                    if (s.StartsWith("KhachSan_")) return s.Replace("KhachSan_", "Khách sạn ").Replace("_", " ");
                    return s.Replace("_", " ");
                })
                .Take(2).ToList();
            return parts.Any() ? string.Join(" · ", parts) : "";
        }

        private static object ServiceInfo(string key) => key switch
        {
            "DV_Khach_San_Homestay" => new { icon = "🏨", url = "/Hotel", name = "Khách sạn & Homestay" },
            "DV_Ve_May_Bay" => new { icon = "✈️", url = "/Flight", name = "Vé máy bay" },
            "DV_Dua_Don_San_Bay" => new { icon = "🚗", url = "/Transfer", name = "Đưa đón sân bay" },
            "DV_Tour_Va_Khu_Vui_Choi" => new { icon = "🗺️", url = "/Tour", name = "Tour & Khu vui chơi" },
            "DV_Thue_Xe_Tu_Lai" => new { icon = "🚙", url = "/Car", name = "Thuê xe tự lái" },
            "HD_Tam_Bien" => new { icon = "🏖️", url = "/Tour", name = "Tour tắm biển" },
            "HD_Leo_Nui_Trekking" => new { icon = "⛰️", url = "/Tour", name = "Tour leo núi" },
            "HD_Tham_Quan_Di_Tich" => new { icon = "🏛️", url = "/Tour", name = "Tham quan di tích" },
            "HD_Am_Thuc" => new { icon = "🍜", url = "/Tour", name = "Tour ẩm thực" },
            "HD_Check_In" => new { icon = "📸", url = "/Tour", name = "Địa điểm check-in" },
            "HD_Nghi_Duong_Chua_Lanh" => new { icon = "🧘", url = "/Hotel", name = "Nghỉ dưỡng chữa lành" },
            _ => new
            {
                icon = "📦",
                url = "/",
                name = key.Replace("Den_", "Đến ").Replace("NganSach_", "Ngân sách ")
                                 .Replace("Hang_", "Hãng ").Replace("Mua_", "Mùa ")
                                 .Replace("_", " ")
            }
        };
    }

    // ── VIEW MODELS ──────────────────────────────────────────────────────────

    public class RecommendationViewModel
    {
        public List<string> RecentPageTypes { get; set; } = new();
        public List<string> VisitedLocations { get; set; } = new();  // ← MỚI
        public List<string> VisitedServices { get; set; } = new();  // ← MỚI
        public List<Tour> SuggestedTours { get; set; } = new();
        public List<Hotel> SuggestedHotels { get; set; } = new();
        public List<Flight> SuggestedFlights { get; set; } = new();
        public List<Car> SuggestedCars { get; set; } = new();
        public List<Transfer> SuggestedTransfers { get; set; } = new();
    }

    public class BehaviorLogRequest
    {
        public string? PageType { get; set; }
        public int? ReferenceId { get; set; }
        public double PageValues { get; set; }
        public double TimeOnPage { get; set; }
        public string? ContextData { get; set; }
        public string? AllItems { get; set; }
    }
}