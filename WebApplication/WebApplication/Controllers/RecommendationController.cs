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

            var behaviors = string.IsNullOrEmpty(sessionId)
                ? new List<UserBehaviorLog>()
                : await _db.UserBehaviorLogs
                    .Where(b => b.SessionId == sessionId && b.LoggedAt > DateTime.Now.AddHours(-4))
                    .OrderByDescending(b => b.LoggedAt).Take(50).ToListAsync();

            // ── Thu thập toàn bộ items ngữ cảnh từ behavior logs ──────────
            var allContextItems = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var visitedLocations = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var visitedServices = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            foreach (var log in behaviors)
            {
                try
                {
                    var ctx = JsonDocument.Parse(log.ContextData ?? "{}").RootElement;
                    if (ctx.TryGetProperty("items", out var itemsArr))
                    {
                        foreach (var item in itemsArr.EnumerateArray())
                        {
                            var s = item.GetString() ?? "";
                            if (!string.IsNullOrEmpty(s))
                            {
                                allContextItems.Add(s);
                                if (s.StartsWith("Den_")) visitedLocations.Add(s.Replace("Den_", ""));
                                if (s.StartsWith("DV_")) visitedServices.Add(s);
                            }
                        }
                    }
                }
                catch { }

                if (!string.IsNullOrEmpty(log.PageType))
                    allContextItems.Add("PageType_" + log.PageType);
            }

            var vm = new RecommendationViewModel
            {
                RecentPageTypes = behaviors.Select(b => b.PageType).Distinct().ToList(),
                VisitedLocations = visitedLocations.ToList(),
                VisitedServices = visitedServices.ToList(),
                AllContextItems = string.Join(",", allContextItems),
            };

            // ── Gọi Python để lấy luật phù hợp với toàn bộ ngữ cảnh ──────
            List<RuleRecommendation> ruleRecs = new();
            if (allContextItems.Any())
            {
                ruleRecs = await GetRuleBasedRecommendationsAsync(string.Join(",", allContextItems), 6);
                vm.RuleRecommendations = ruleRecs;
            }

            // ── Build suggested items DỰA TRÊN LUẬT (không dùng filter thủ công) ──
            // Lấy service keys được gợi ý bởi luật
            var suggestedServiceKeys = ruleRecs
                .SelectMany(r => r.ServiceKeys)
                .Distinct()
                .ToHashSet();

            // Context từ luật (địa điểm, hãng, v.v.)
            var ruleCtx = ruleRecs.FirstOrDefault()?.ExtractedContext ?? new ExtractedContext();

            // Địa điểm ưu tiên: từ luật → từ behavior
            var priorityLocations = ruleCtx.Destinations?.Any() == true
                ? ruleCtx.Destinations
                : visitedLocations.ToList();

            // HOTEL: hiển thị khi luật gợi ý DV_Khach_San_Homestay HOẶC HD_Nghi_Duong_Chua_Lanh
            bool showHotel = !behaviors.Any()
                || suggestedServiceKeys.Contains("DV_Khach_San_Homestay")
                || suggestedServiceKeys.Contains("HD_Nghi_Duong_Chua_Lanh")
                || behaviors.Any(b => b.PageType == "Hotel");

            if (showHotel)
                vm.SuggestedHotels = await QueryHotelsAsync(priorityLocations, ruleCtx);

            // FLIGHT: hiển thị khi luật gợi ý DV_Ve_May_Bay
            bool showFlight = !behaviors.Any()
                || suggestedServiceKeys.Contains("DV_Ve_May_Bay")
                || behaviors.Any(b => b.PageType == "Flight");

            if (showFlight)
                vm.SuggestedFlights = await QueryFlightsAsync(priorityLocations, ruleCtx);

            // TOUR: hiển thị khi luật gợi ý DV_Tour_Va_Khu_Vui_Choi hoặc bất kỳ HD_*
            var tourActivityKeys = new[] {
                "DV_Tour_Va_Khu_Vui_Choi","HD_Tam_Bien","HD_Leo_Nui_Trekking",
                "HD_Tham_Quan_Di_Tich","HD_Am_Thuc","HD_Check_In","HD_Nghi_Duong_Chua_Lanh"
            };
            bool showTour = !behaviors.Any()
                || suggestedServiceKeys.Any(k => tourActivityKeys.Contains(k))
                || behaviors.Any(b => b.PageType == "Tour");

            if (showTour)
                vm.SuggestedTours = await QueryToursAsync(priorityLocations, ruleCtx);

            // CAR: hiển thị khi luật gợi ý DV_Thue_Xe_Tu_Lai
            bool showCar = suggestedServiceKeys.Contains("DV_Thue_Xe_Tu_Lai")
                || behaviors.Any(b => b.PageType == "Car");

            if (showCar)
                vm.SuggestedCars = await QueryCarsAsync(ruleCtx);

            // TRANSFER: hiển thị khi luật gợi ý DV_Dua_Don_San_Bay
            bool showTransfer = suggestedServiceKeys.Contains("DV_Dua_Don_San_Bay")
                || behaviors.Any(b => b.PageType == "Transfer");

            if (showTransfer)
                vm.SuggestedTransfers = await QueryTransfersAsync(priorityLocations, ruleCtx);

            // ── Voucher ────────────────────────────────────────────────────
            ViewBag.ActiveVoucher = string.IsNullOrEmpty(sessionId) ? null
                : await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId && !v.IsUsed && v.ExpiresAt > DateTime.Now)
                    .FirstOrDefaultAsync();

            return View(vm);
        }

        // ── QUERY HELPERS – dùng context từ luật ──────────────────────────

        private async Task<List<Hotel>> QueryHotelsAsync(List<string> locations, ExtractedContext ctx)
        {
            var query = _db.Hotels.AsQueryable();

            if (locations.Any())
            {
                var locNorms = locations.Select(l => NormalizeLocationForDb(l)).ToList();
                // SỬA TẠI ĐÂY: Dùng .Contains thay cho EF.Functions.Like lồng trong .Any
                query = query.Where(h => locNorms.Any(loc => h.Location.Contains(loc)));
            }

            if (ctx.HotelTypes != null && ctx.HotelTypes.Any())
            {
                var starsList = ctx.HotelTypes
                    .Select(s => s.Replace("_Sao", "").Trim())
                    .Select(s => int.TryParse(s, out var v) ? v : 0)
                    .Where(v => v > 0).ToList();

                if (starsList.Any())
                {
                    query = query.Where(h => starsList.Contains(h.Stars));
                }
            }

            if (ctx.HasPool.HasValue)
            {
                query = query.Where(h => h.HasPool == ctx.HasPool.Value);
            }

            return await query.Take(4).ToListAsync();
        }

        private async Task<List<Flight>> QueryFlightsAsync(List<string> locations, ExtractedContext ctx)
        {
            var query = _db.Flights.AsQueryable();

            if (locations.Any())
            {
                var locNorms = locations.Select(l => NormalizeLocationForDb(l)).ToList();
                // SỬA TẠI ĐÂY: Dùng .Contains thay cho EF.Functions.Like lồng trong .Any
                query = query.Where(f => locNorms.Any(loc => f.Arrival.Contains(loc)));
            }

            if (ctx.Airlines != null && ctx.Airlines.Any())
            {
                var airNorms = ctx.Airlines.Select(a => a.Replace("_", " ").ToLower().Trim()).ToList();
                query = query.Where(f => airNorms.Any(a => f.Airline.ToLower().Contains(a)));
            }

            var result = await query.OrderBy(f => f.DepartureTime).Take(4).ToListAsync();
            return result;
        }

        private async Task<List<Tour>> QueryToursAsync(List<string> locations, ExtractedContext ctx)
        {
            var query = _db.Tours.AsQueryable();

            if (locations.Any())
            {
                var locNorms = locations.Select(l => NormalizeLocationForDb(l)).ToList();
                // SỬA TẠI ĐÂY: Dùng .Contains thay cho EF.Functions.Like lồng trong .Any
                query = query.Where(t => locNorms.Any(loc => t.Destination.Contains(loc)));
            }

            return await query.Take(4).ToListAsync();
        }
        private async Task<List<Car>> QueryCarsAsync(ExtractedContext ctx)
        {
            var query = _db.Cars.Where(c => c.IsAvailable);

            if (ctx.CarBrands?.Any() == true)
            {
                var brands = ctx.CarBrands.Select(b => b.Replace("_", " ")).ToList();
                query = query.Where(c => brands.Any(b => EF.Functions.Like(c.Brand, $"%{b}%")));
            }

            var result = await query.Take(4).ToListAsync();
            if (!result.Any())
                result = await _db.Cars.Where(c => c.IsAvailable).Take(4).ToListAsync();
            return result;
        }

        private async Task<List<Transfer>> QueryTransfersAsync(List<string> locations, ExtractedContext ctx)
        {
            var query = _db.Transfers.AsQueryable();

            if (locations.Any())
            {
                var locNorms = locations.Select(l => NormalizeLocationForDb(l)).ToList();
                // SỬA TẠI ĐÂY: Dùng .Contains thay cho EF.Functions.Like lồng trong .Any
                query = query.Where(t => locNorms.Any(loc => t.ToLocation.Contains(loc) || t.FromLocation.Contains(loc)));
            }

            return await query.Take(4).ToListAsync();
        }

        // ── GỌI PYTHON LẤY LUẬT CÓ CONTEXT ──────────────────────────────
        private async Task<List<RuleRecommendation>> GetRuleBasedRecommendationsAsync(string allItems, int limit)
        {
            var results = new List<RuleRecommendation>();

            try
            {
                var client = _http.CreateClient();
                client.Timeout = TimeSpan.FromSeconds(5);
                var url = $"{PythonUrl}/api/recommendations-with-context?service_name={Uri.EscapeDataString(allItems)}&limit={limit}";
                var res = await client.GetAsync(url);

                if (res.IsSuccessStatusCode)
                {
                    var doc = JsonDocument.Parse(await res.Content.ReadAsStringAsync());
                    if (doc.RootElement.TryGetProperty("status", out var st) && st.GetString() == "success"
                        && doc.RootElement.TryGetProperty("data", out var dataArr))
                    {
                        foreach (var item in dataArr.EnumerateArray())
                        {
                            var goiY = item.GetProperty("DichVu_GoiY").GetString() ?? "";
                            var goc = item.GetProperty("DichVu_Goc").GetString() ?? "";
                            var conf = item.GetProperty("Do_Tin_Cay_Confidence").GetDouble();
                            var lift = item.TryGetProperty("Chi_So_Lift", out var lp) ? lp.GetDouble() : 1.0;

                            var serviceKeys = goiY.Split(',', StringSplitOptions.RemoveEmptyEntries)
                                                   .Select(k => k.Trim()).ToList();

                            var ctx = new ExtractedContext();
                            if (item.TryGetProperty("extracted_context", out var ctxEl))
                                ctx = ParseExtractedContext(ctxEl);

                            results.Add(new RuleRecommendation
                            {
                                Antecedent = goc,
                                ServiceKeys = serviceKeys,
                                Confidence = conf,
                                Lift = lift,
                                ExtractedContext = ctx,
                                Reason = BuildReason(goc),
                            });
                        }
                        return results;
                    }
                }
            }
            catch { /* fallback to DB */ }

            // Fallback: query DB trực tiếp
            var inputSet = allItems.Split(',', StringSplitOptions.RemoveEmptyEntries)
                                    .Select(s => s.Trim()).ToHashSet();
            var allRules = await _db.LuatFPGrowth.OrderByDescending(r => r.Do_Tin_Cay_Confidence).ToListAsync();

            var seen = new HashSet<string>();
            foreach (var rule in allRules)
            {
                if (results.Count >= limit) break;
                var ante = rule.DichVu_Goc.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).ToHashSet();
                if (!ante.IsSubsetOf(inputSet)) continue;
                var consq = rule.DichVu_GoiY.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).ToList();
                if (consq.Any(c => inputSet.Contains(c))) continue;
                if (!seen.Add(rule.DichVu_GoiY)) continue;

                // Trích xuất context từ items
                var ctx = ExtractContextFromItemsLocal(inputSet);
                results.Add(new RuleRecommendation
                {
                    Antecedent = rule.DichVu_Goc,
                    ServiceKeys = consq.Where(k => k.StartsWith("DV_") || k.StartsWith("HD_")).ToList(),
                    Confidence = (double)rule.Do_Tin_Cay_Confidence,
                    Lift = (double)rule.Chi_So_Lift,
                    ExtractedContext = ctx,
                    Reason = BuildReason(rule.DichVu_Goc),
                });
            }

            return results;
        }

        private static ExtractedContext ExtractContextFromItemsLocal(HashSet<string> items)
        {
            return new ExtractedContext
            {
                Destinations = items.Where(i => i.StartsWith("Den_")).Select(i => i.Replace("Den_", "")).ToList(),
                Origins = items.Where(i => i.StartsWith("TuDen_")).Select(i => i.Replace("TuDen_", "")).ToList(),
                Airlines = items.Where(i => i.StartsWith("Hang_")).Select(i => i.Replace("Hang_", "")).ToList(),
                HotelTypes = items.Where(i => i.StartsWith("KhachSan_")).Select(i => i.Replace("KhachSan_", "")).ToList(),
                Budgets = items.Where(i => i.StartsWith("NganSach_")).Select(i => i.Replace("NganSach_", "")).ToList(),
                Seasons = items.Where(i => i.StartsWith("Mua_")).Select(i => i.Replace("Mua_", "")).ToList(),
                Durations = items.Where(i => i.StartsWith("SoNgay_")).Select(i => i.Replace("SoNgay_", "")).ToList(),
                CarBrands = items.Where(i => i.StartsWith("Xe_")).Select(i => i.Replace("Xe_", "")).ToList(),
                Activities = items.Where(i => i.StartsWith("HD_")).Select(i => i.Replace("HD_", "")).ToList(),
                HasPool = items.Contains("Co_Ho_Boi") ? true : items.Contains("Khong_Ho_Boi") ? false : null,
            };
        }

        private static ExtractedContext ParseExtractedContext(JsonElement ctxEl)
        {
            var ctx = new ExtractedContext();
            try
            {
                if (ctxEl.TryGetProperty("destinations", out var d))
                    ctx.Destinations = d.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("origins", out var o))
                    ctx.Origins = o.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("airlines", out var a))
                    ctx.Airlines = a.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("hotel_types", out var ht))
                    ctx.HotelTypes = ht.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("budgets", out var b))
                    ctx.Budgets = b.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("seasons", out var s))
                    ctx.Seasons = s.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("durations", out var dur))
                    ctx.Durations = dur.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("car_brands", out var cb))
                    ctx.CarBrands = cb.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("activities", out var act))
                    ctx.Activities = act.EnumerateArray().Select(x => x.GetString() ?? "").ToList();
                if (ctxEl.TryGetProperty("has_pool", out var hp))
                    ctx.HasPool = hp.ValueKind == JsonValueKind.True;
            }
            catch { }
            return ctx;
        }

        // ── 2. TRANG VOUCHER CỦA TÔI ─────────────────────────────────────────
        public async Task<IActionResult> MyVouchers()
        {
            var sessionId = Request.Cookies["vt_session"] ?? "";
            int? userId = null;
            if (int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int uid)) userId = uid;

            List<VoucherIssued> vouchers;
            if (userId.HasValue)
                vouchers = await _db.VouchersIssued.Where(v => v.UserId == userId)
                    .OrderByDescending(v => v.IssuedAt).Take(20).ToListAsync();
            else if (!string.IsNullOrEmpty(sessionId))
                vouchers = await _db.VouchersIssued.Where(v => v.SessionId == sessionId)
                    .OrderByDescending(v => v.IssuedAt).Take(20).ToListAsync();
            else
                vouchers = new List<VoucherIssued>();

            return View(vouchers);
        }

        // ── 3. TEST VOUCHER ────────────────────────────────────────────────
        [HttpPost]
        public async Task<IActionResult> TestVoucher()
        {
            try
            {
                var sessionId = EnsureSession();
                var oldTest = await _db.VouchersIssued
                    .Where(v => v.SessionId == sessionId && v.VoucherCode.StartsWith("TEST-")).ToListAsync();
                if (oldTest.Any()) { _db.VouchersIssued.RemoveRange(oldTest); await _db.SaveChangesAsync(); }

                var features = new
                {
                    administrative_duration = 180.0,
                    informational_duration = 0.0,
                    productrelated_duration = 600.0,
                    bounce_rates = 0.0,
                    exit_rates = 0.05,
                    page_values = 75.0,
                    weekend = 1
                };

                int discount = 15; bool giveVoucher = false; string aiDecision = "fallback";
                try
                {
                    var client = _http.CreateClient(); client.Timeout = TimeSpan.FromSeconds(5);
                    var jsonPayload = JsonSerializer.Serialize(features, new JsonSerializerOptions { PropertyNamingPolicy = null });
                    var resp = await client.PostAsync($"{PythonUrl}/api/predict-voucher",
                        new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json"));
                    if (resp.IsSuccessStatusCode)
                    {
                        var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
                        if (doc.RootElement.TryGetProperty("need_voucher", out var nv)) giveVoucher = nv.GetInt32() == 1;
                        if (doc.RootElement.TryGetProperty("discount_percent", out var dp) && dp.GetInt32() > 0) discount = dp.GetInt32();
                        if (doc.RootElement.TryGetProperty("debug_info", out var di) && di.TryGetProperty("predicted_revenue_intent", out var ri))
                            aiDecision = ri.GetInt32() == 0 ? "model=0(không mua)→cấp" : "model=1(sẽ mua)→không cấp";
                    }
                }
                catch (Exception ex) { giveVoucher = true; aiDecision = "python_offline_fallback: " + ex.Message; }

                if (!giveVoucher) { giveVoucher = true; aiDecision += " [test_override]"; }

                var code = "TEST-" + Guid.NewGuid().ToString("N")[..6].ToUpper();
                var voucher = new VoucherIssued
                {
                    SessionId = sessionId,
                    UserId = int.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out int u) ? u : null,
                    VoucherCode = code,
                    DiscountPercent = discount,
                    ApplicableType = "Test",
                    IssuedAt = DateTime.Now,
                    ExpiresAt = DateTime.Now.AddMinutes(30),
                    IsUsed = false
                };
                _db.VouchersIssued.Add(voucher); await _db.SaveChangesAsync();

                return Json(new
                {
                    success = true,
                    code,
                    discount,
                    expiresAt = voucher.ExpiresAt.ToString("o"),
                    aiDecision,
                    isNew = true,
                    applicableType = "Test",
                    hasVoucher = true
                });
            }
            catch (Exception ex) { return Json(new { success = false, error = ex.Message }); }
        }

        // ── 4. API GỢI Ý LUẬT KẾT HỢP (cho _AssociationSuggestions partial) ──
        [HttpGet]
        public async Task<IActionResult> GetSuggestions(string services, int limit = 4)
        {
            if (string.IsNullOrWhiteSpace(services))
                return Json(new { status = "success", data = Array.Empty<object>() });
            try
            {
                // Gọi Python API mới (có context)
                try
                {
                    var client = _http.CreateClient();
                    client.Timeout = TimeSpan.FromSeconds(4);
                    var url = $"{PythonUrl}/api/recommendations-with-context?service_name={Uri.EscapeDataString(services)}&limit={limit}";
                    var res = await client.GetAsync(url);
                    if (res.IsSuccessStatusCode)
                    {
                        var doc = JsonDocument.Parse(await res.Content.ReadAsStringAsync());
                        if (doc.RootElement.TryGetProperty("status", out var st) && st.GetString() == "success")
                        {
                            var list = new List<object>();
                            JsonElement extractedCtxEl = default;
                            doc.RootElement.TryGetProperty("extracted_context", out extractedCtxEl);
                            var globalCtx = ParseExtractedContext(extractedCtxEl);

                            foreach (var item in doc.RootElement.GetProperty("data").EnumerateArray())
                            {
                                var goiY = item.GetProperty("DichVu_GoiY").GetString() ?? "";
                                var goc = item.GetProperty("DichVu_Goc").GetString() ?? "";
                                var conf = Math.Round(item.GetProperty("Do_Tin_Cay_Confidence").GetDouble() * 100, 1);
                                var lift = item.TryGetProperty("Chi_So_Lift", out var lp) ? Math.Round(lp.GetDouble(), 2) : 1.0;

                                var itemCtx = globalCtx;
                                if (item.TryGetProperty("extracted_context", out var ic))
                                    itemCtx = ParseExtractedContext(ic);

                                var serviceKeys = goiY.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(k => k.Trim()).ToList();
                                var display = serviceKeys.Select(k => ServiceInfoWithContext(k.Trim(), itemCtx)).ToList();

                                list.Add(new
                                {
                                    dichVu_Goc = goc,
                                    dichVu_GoiY = goiY,
                                    do_Tin_Cay = conf,
                                    chi_So_Lift = lift,
                                    displayItems = display,
                                    lyDoGoiY = BuildReason(goc),
                                    extractedContext = new
                                    {
                                        destinations = itemCtx.Destinations ?? new(),
                                        airlines = itemCtx.Airlines ?? new(),
                                        hotelTypes = itemCtx.HotelTypes ?? new(),
                                        budgets = itemCtx.Budgets ?? new(),
                                    }
                                });
                            }
                            return Json(new { status = "success", data = list });
                        }
                    }
                }
                catch { /* fallback DB */ }

                // Fallback DB
                var inputSet = services.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).ToHashSet();
                var ctx = ExtractContextFromItemsLocal(inputSet);
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
                        displayItems = consq.Select(k => ServiceInfoWithContext(k, ctx)).ToList(),
                        lyDoGoiY = BuildReason(rule.DichVu_Goc),
                        extractedContext = new { destinations = ctx.Destinations ?? new(), airlines = ctx.Airlines ?? new() }
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

        // ── 6. CHECK VOUCHER ────────────────────────────────────────────────
        [HttpPost]
        public async Task<IActionResult> CheckVoucher()
        {
            try
            {
                var sessionId = EnsureSession();
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

                var logs = await _db.UserBehaviorLogs
                    .Where(b => b.SessionId == sessionId && b.LoggedAt > DateTime.Now.AddHours(-4)).ToListAsync();
                if (logs.Count < 2) return Json(new { hasVoucher = false });

                double adminDuration = logs.Where(b => b.PageType == "Info").Sum(b => b.TimeOnPage);
                double productDuration = logs.Where(b => b.PageType is "Tour" or "Hotel" or "Flight" or "Car" or "Transfer").Sum(b => b.TimeOnPage);
                double avgPV = logs.Any() ? logs.Average(b => b.PageValues) : 0.0;
                double bounceRate = logs.Count == 1 ? 1.0 : 0.0;
                double exitRate = logs.Any(b => b.HasPurchased) ? 0.1 : 0.4;
                int weekendVal = logs.Any(b => b.IsWeekend) ? 1 : 0;

                bool giveVoucher = false; int discount = 10;
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
                    var client = _http.CreateClient(); client.Timeout = TimeSpan.FromSeconds(5);
                    var jsonPayload = JsonSerializer.Serialize(features, new JsonSerializerOptions { PropertyNamingPolicy = null });
                    var resp = await client.PostAsync($"{PythonUrl}/api/predict-voucher",
                        new StringContent(jsonPayload, System.Text.Encoding.UTF8, "application/json"));
                    if (!resp.IsSuccessStatusCode) throw new Exception($"Python API error: {resp.StatusCode}");
                    var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
                    if (doc.RootElement.TryGetProperty("need_voucher", out var nv)) giveVoucher = nv.GetInt32() == 1;
                    if (doc.RootElement.TryGetProperty("discount_percent", out var dp) && dp.GetInt32() > 0) discount = dp.GetInt32();
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[Voucher Fallback] {ex.Message}");
                    var totalTime = logs.Sum(b => b.TimeOnPage); var pages = logs.Select(b => b.PageType).Distinct().Count();
                    giveVoucher = totalTime > 90 && avgPV > 10 && pages >= 2 && !logs.Any(b => b.HasPurchased);
                    if (giveVoucher) discount = avgPV > 40 ? 20 : avgPV > 20 ? 15 : 10;
                }

                if (!giveVoucher) return Json(new { hasVoucher = false });

                string targetType = "Tour"; int? targetId = null;
                if (logs.Any())
                {
                    var top = logs.GroupBy(b => new { b.PageType, b.ReferenceId })
                                  .OrderByDescending(g => g.Sum(b => b.TimeOnPage + b.PageValues)).First();
                    targetType = top.Key.PageType; targetId = top.Key.ReferenceId;
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
                    IsUsed = false
                };
                _db.VouchersIssued.Add(voucher); await _db.SaveChangesAsync();

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
            catch (Exception ex) { return Json(new { hasVoucher = false, error = ex.Message }); }
        }

        // ── PRIVATE HELPERS ──────────────────────────────────────────────────
        private string EnsureSession()
        {
            var id = Request.Cookies["vt_session"];
            if (!string.IsNullOrEmpty(id)) return id;
            id = Guid.NewGuid().ToString("N")[..16];
            Response.Cookies.Append("vt_session", id, new CookieOptions
            { Expires = DateTimeOffset.Now.AddDays(1), HttpOnly = false, SameSite = SameSiteMode.Lax });
            return id;
        }

        private static string NormalizeLocationForDb(string slugLoc)
            => (slugLoc ?? "").Replace("_", " ").Trim();

        private static string BuildReason(string antecedent)
        {
            if (string.IsNullOrEmpty(antecedent)) return "";
            var parts = antecedent.Split(',', StringSplitOptions.RemoveEmptyEntries)
                .Select(s => s.Trim())
                .Where(s => s.StartsWith("Den_") || s.StartsWith("NganSach_") || s.StartsWith("Hang_")
                         || s.StartsWith("Mua_") || s.StartsWith("KhachSan_") || s.StartsWith("SoNguoi_"))
                .Select(s =>
                {
                    if (s.StartsWith("Den_")) return "Đến " + s.Replace("Den_", "").Replace("_", " ");
                    if (s.StartsWith("Hang_")) return "Hãng " + s.Replace("Hang_", "").Replace("_", " ");
                    if (s.StartsWith("NganSach_")) return "Ngân sách " + s.Replace("NganSach_", "").Replace("_", " ").ToLower();
                    if (s.StartsWith("Mua_")) return "Mùa " + s.Replace("Mua_", "").ToLower();
                    if (s.StartsWith("KhachSan_")) return s.Replace("KhachSan_", "Khách sạn ").Replace("_", " ");
                    if (s.StartsWith("SoNguoi_")) return "Nhóm " + s.Replace("SoNguoi_", "").ToLower();
                    return s.Replace("_", " ");
                }).Take(3).ToList();
            return parts.Any() ? string.Join(" · ", parts) : "";
        }

        /// <summary>ServiceInfo có context → sinh URL có query string đúng địa điểm</summary>
        private static object ServiceInfoWithContext(string key, ExtractedContext ctx)
        {
            var firstDest = ctx.Destinations?.FirstOrDefault() ?? "";
            var destParam = !string.IsNullOrEmpty(firstDest) ? $"?location={Uri.EscapeDataString(firstDest.Replace("_", " "))}" : "";
            var destParamFlight = !string.IsNullOrEmpty(firstDest) ? $"?arrival={Uri.EscapeDataString(firstDest.Replace("_", " "))}" : "";

            return key switch
            {
                "DV_Khach_San_Homestay" => new
                {
                    icon = "🏨",
                    url = $"/Hotel{destParam}",
                    name = "Khách sạn & Homestay",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "DV_Ve_May_Bay" => new
                {
                    icon = "✈️",
                    url = $"/Flight{destParamFlight}",
                    name = "Vé máy bay",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "DV_Dua_Don_San_Bay" => new
                {
                    icon = "🚗",
                    url = $"/Transfer{destParam}",
                    name = "Đưa đón sân bay",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "DV_Tour_Va_Khu_Vui_Choi" => new
                {
                    icon = "🗺️",
                    url = $"/Tour{destParam}",
                    name = "Tour & Khu vui chơi",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "DV_Thue_Xe_Tu_Lai" => new
                {
                    icon = "🚙",
                    url = "/Car",
                    name = "Thuê xe tự lái",
                    locationHint = "",
                    serviceKey = key
                },
                "HD_Tam_Bien" => new
                {
                    icon = "🏖️",
                    url = $"/Tour{destParam}",
                    name = "Tour tắm biển",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "HD_Leo_Nui_Trekking" => new
                {
                    icon = "⛰️",
                    url = $"/Tour{destParam}",
                    name = "Tour leo núi / Trekking",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "HD_Tham_Quan_Di_Tich" => new
                {
                    icon = "🏛️",
                    url = $"/Tour{destParam}",
                    name = "Tham quan di tích",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "HD_Am_Thuc" => new
                {
                    icon = "🍜",
                    url = $"/Tour{destParam}",
                    name = "Tour ẩm thực",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "HD_Check_In" => new
                {
                    icon = "📸",
                    url = $"/Tour{destParam}",
                    name = "Địa điểm check-in",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                "HD_Nghi_Duong_Chua_Lanh" => new
                {
                    icon = "🧘",
                    url = $"/Hotel{destParam}",
                    name = "Nghỉ dưỡng chữa lành",
                    locationHint = firstDest.Replace("_", " "),
                    serviceKey = key
                },
                _ => new
                {
                    icon = "📦",
                    url = "/",
                    name = key.Replace("Den_", "Đến ").Replace("NganSach_", "Ngân sách ")
                    .Replace("Hang_", "Hãng ").Replace("Mua_", "Mùa ").Replace("_", " "),
                    locationHint = "",
                    serviceKey = key
                }
            };
        }
    }

    // ── VIEW MODELS & DTOs ────────────────────────────────────────────────────

    public class RecommendationViewModel
    {
        public List<string> RecentPageTypes { get; set; } = new();
        public List<string> VisitedLocations { get; set; } = new();
        public List<string> VisitedServices { get; set; } = new();
        public string AllContextItems { get; set; } = "";
        public List<RuleRecommendation> RuleRecommendations { get; set; } = new();
        public List<Tour> SuggestedTours { get; set; } = new();
        public List<Hotel> SuggestedHotels { get; set; } = new();
        public List<Flight> SuggestedFlights { get; set; } = new();
        public List<Car> SuggestedCars { get; set; } = new();
        public List<Transfer> SuggestedTransfers { get; set; } = new();
    }

    public class RuleRecommendation
    {
        public string Antecedent { get; set; } = "";
        public List<string> ServiceKeys { get; set; } = new();
        public double Confidence { get; set; }
        public double Lift { get; set; }
        public ExtractedContext ExtractedContext { get; set; } = new();
        public string Reason { get; set; } = "";
    }

    public class ExtractedContext
    {
        public List<string>? Destinations { get; set; }
        public List<string>? Origins { get; set; }
        public List<string>? Airlines { get; set; }
        public List<string>? HotelTypes { get; set; }
        public List<string>? Budgets { get; set; }
        public List<string>? Seasons { get; set; }
        public List<string>? Durations { get; set; }
        public List<string>? CarBrands { get; set; }
        public List<string>? Activities { get; set; }
        public List<string>? GroupSizes { get; set; }
        public bool? HasPool { get; set; }
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