using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TravelApp.Models
{
    /// <summary>
    /// Lưu các feature đã tính từ UserBehaviorLogs trước khi gửi lên model dự đoán voucher.
    /// Mục đích: kiểm tra dữ liệu đầu vào có hợp lý không, debug, phân tích sau.
    /// </summary>
    [Table("VoucherFeatureLog")]
    public class VoucherFeatureLog
    {
        [Key] public int Id { get; set; }

        // ── Định danh phiên ─────────────────────────────────────────────
        [MaxLength(64)]  public string SessionId { get; set; } = string.Empty;
        public int? UserId { get; set; }

        // ── Số logs đầu vào ─────────────────────────────────────────────
        public int TotalLogCount { get; set; }       // Tổng số UserBehaviorLog dùng để tính

        // ── 7 Feature gửi lên model ─────────────────────────────────────
        [Column(TypeName = "decimal(12,4)")]
        public decimal AdminDuration { get; set; }        // Tổng thời gian trang Info (giây)

        [Column(TypeName = "decimal(12,4)")]
        public decimal InformationalDuration { get; set; } // Luôn = 0 hiện tại, để trống khi cần

        [Column(TypeName = "decimal(12,4)")]
        public decimal ProductDuration { get; set; }      // Tổng thời gian trang Tour/Hotel/Flight/Car/Transfer (giây)

        [Column(TypeName = "decimal(8,6)")]
        public decimal BounceRate { get; set; }           // 1.0 nếu chỉ 1 log, 0.0 nếu nhiều log

        [Column(TypeName = "decimal(8,6)")]
        public decimal ExitRate { get; set; }             // 0.1 nếu đã mua, 0.4 nếu chưa

        [Column(TypeName = "decimal(10,4)")]
        public decimal AvgPageValues { get; set; }        // Trung bình PageValues của session

        public int WeekendVal { get; set; }               // 1 = cuối tuần, 0 = ngày thường

        // ── Các trang đã xem ────────────────────────────────────────────
        [MaxLength(200)]
        public string PagesVisited { get; set; } = string.Empty;  // "Tour,Hotel,Flight" etc.

        public int UniquePageCount { get; set; }

        // ── Thời gian tính ──────────────────────────────────────────────
        public DateTime ComputedAt { get; set; } = DateTime.Now;
    }

    /// <summary>
    /// Lưu quyết định cấp voucher của model + kết quả thực tế.
    /// Mục đích: so sánh model dự đoán có đúng không (precision/recall).
    /// </summary>
    [Table("VoucherDecisionLog")]
    public class VoucherDecisionLog
    {
        [Key] public int Id { get; set; }

        // ── Liên kết ────────────────────────────────────────────────────
        [MaxLength(64)]  public string SessionId    { get; set; } = string.Empty;
        public int? UserId       { get; set; }
        public int? FeatureLogId { get; set; }  // FK sang VoucherFeatureLog
        [MaxLength(50)]  public string? VoucherCode { get; set; }

        // ── Đầu vào model ───────────────────────────────────────────────
        /// <summary>Model dự đoán biến Revenue: 0 = không mua, 1 = sẽ mua</summary>
        public int ModelPredictedRevenue { get; set; }  // 0 hoặc 1

        // ── Quyết định cấp ──────────────────────────────────────────────
        /// <summary>Model + logic có cấp voucher không</summary>
        public bool ModelDecidedGrant { get; set; }

        public int DiscountPercent { get; set; }   // % giảm nếu được cấp

        [MaxLength(500)]
        public string DecisionReason { get; set; } = string.Empty;  // Lý do từ debug_info

        // ── Kết quả thực tế (cập nhật sau khi khách dùng hoặc hết hạn) ─
        /// <summary>Khách có thực sự dùng voucher không (cập nhật sau)</summary>
        public bool? ActuallyUsed { get; set; }     // null = chưa biết, true/false = đã biết

        /// <summary>Khách có mua sau khi xem không (cập nhật sau)</summary>
        public bool? ActuallyPurchased { get; set; }

        /// <summary>
        /// Model đúng không: 
        ///   - Nếu Grant=true và ActuallyPurchased=true → Sai (model cấp nhưng khách tự mua rồi)
        ///   - Nếu Grant=true và ActuallyPurchased=false → Đúng (cần voucher để kích mua)
        ///   - Nếu Grant=false và ActuallyPurchased=true → Đúng (model biết khách sẽ tự mua)
        ///   - Nếu Grant=false và ActuallyPurchased=false → Sai (lẽ ra nên cấp)
        /// </summary>
        public bool? IsModelCorrect { get; set; }   // null = chưa đủ dữ liệu để đánh giá

        // ── Thời gian ───────────────────────────────────────────────────
        public DateTime DecidedAt  { get; set; } = DateTime.Now;
        public DateTime? EvaluatedAt { get; set; }  // Khi nào được đánh giá kết quả
    }

    public class LuatFPGrowth
    {
        [Key] public int Id { get; set; }
        [Required, MaxLength(500)] public string DichVu_Goc  { get; set; } = string.Empty;
        [Required, MaxLength(500)] public string DichVu_GoiY { get; set; } = string.Empty;
        [Column(TypeName = "decimal(10,4)")] public decimal Do_Ho_Tro             { get; set; }
        [Column(TypeName = "decimal(10,4)")] public decimal Do_Tin_Cay_Confidence { get; set; }
        [Column(TypeName = "decimal(10,4)")] public decimal Chi_So_Lift           { get; set; }
        public DateTime CreatedAt { get; set; } = DateTime.Now;
    }

    public class UserBehaviorLog
    {
        [Key] public int Id { get; set; }
        public string SessionId    { get; set; } = string.Empty;
        public int?   UserId       { get; set; }
        public string PageType     { get; set; } = string.Empty;
        public int?   ReferenceId  { get; set; }
        public double PageValues   { get; set; } = 0;
        public double TimeOnPage   { get; set; } = 0;
        public bool   IsWeekend    { get; set; }
        public bool   HasPurchased { get; set; } = false;

        // Lưu ngữ cảnh đầy đủ: địa điểm, giá, số người, loại xe, hãng bay...
        // VD Flight: {"destination":"Da_Nang","departure":"HCM","price_tier":"high","seats":2}
        // VD Hotel:  {"location":"Ha_Noi","stars":4,"price_tier":"medium","has_pool":true}
        // VD Tour:   {"destination":"Phu_Quoc","duration_days":3,"price_tier":"high"}
        // VD Car:    {"brand":"Toyota","price_tier":"medium"}
        // VD Trans:  {"from":"HCM","to":"Da_Nang","type":"Xe_khach"}
        [MaxLength(1000)]
        public string ContextData { get; set; } = "{}";

        public DateTime LoggedAt { get; set; } = DateTime.Now;
    }

    public class VoucherIssued
    {
        [Key] public int Id { get; set; }
        public string SessionId       { get; set; } = string.Empty;
        public int?   UserId          { get; set; }
        [Required, MaxLength(50)]
        public string VoucherCode     { get; set; } = string.Empty;
        public int    DiscountPercent { get; set; } = 10;
        public string ApplicableType  { get; set; } = "All";
        public int?   ApplicableId    { get; set; }
        public DateTime IssuedAt  { get; set; } = DateTime.Now;
        public DateTime ExpiresAt { get; set; }
        public bool     IsUsed    { get; set; } = false;
    }
}
