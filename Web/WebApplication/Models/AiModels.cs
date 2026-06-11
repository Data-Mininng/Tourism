using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TravelApp.Models
{
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
