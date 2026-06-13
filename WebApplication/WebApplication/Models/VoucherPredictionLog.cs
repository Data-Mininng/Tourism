namespace TravelApp.Models
{
    public class VoucherPredictionLog
    {
        public int Id { get; set; }

        public string? SessionId { get; set; }
        public int? UserId { get; set; }

        public double AdministrativeDuration { get; set; }
        public double InformationalDuration { get; set; }
        public double ProductRelatedDuration { get; set; }

        public double BounceRate { get; set; }
        public double ExitRate { get; set; }
        public double PageValues { get; set; }

        public bool Weekend { get; set; }

        public bool NeedVoucher { get; set; }
        public int DiscountPercent { get; set; }

        public DateTime CreatedAt { get; set; }
    }
}
