using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace TravelApp.Migrations
{
    /// <inheritdoc />
    public partial class AddVoucherFeatureAndDecisionLogs : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // 1. Tạo bảng VoucherFeatureLog trước
            migrationBuilder.CreateTable(
                name: "VoucherFeatureLog",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    SessionId = table.Column<string>(type: "nvarchar(64)", maxLength: 64, nullable: false),
                    AdminDuration = table.Column<decimal>(type: "decimal(12,4)", nullable: false),
                    InformationalDuration = table.Column<decimal>(type: "decimal(12,4)", nullable: false),
                    ProductDuration = table.Column<decimal>(type: "decimal(12,4)", nullable: false),
                    BounceRate = table.Column<decimal>(type: "decimal(8,6)", nullable: false),
                    ExitRate = table.Column<decimal>(type: "decimal(8,6)", nullable: false),
                    PagesVisited = table.Column<string>(type: "nvarchar(200)", maxLength: 200, nullable: false),
                    AvgPageValues = table.Column<decimal>(type: "decimal(10,4)", nullable: false),
                    UniquePageCount = table.Column<int>(type: "int", nullable: false),
                    TotalLogCount = table.Column<int>(type: "int", nullable: false),
                    WeekendVal = table.Column<int>(type: "int", nullable: false),
                    ComputedAt = table.Column<DateTime>(type: "datetime2", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_VoucherFeatureLog", x => x.Id);
                });

            // 2. Tạo bảng VoucherDecisionLog sau
            migrationBuilder.CreateTable(
                name: "VoucherDecisionLog",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    SessionId = table.Column<string>(type: "nvarchar(64)", maxLength: 64, nullable: false),
                    FeatureLogId = table.Column<int>(type: "int", nullable: true), // Cho phép null để SetNull khi xóa
                    ModelPredictedRevenue = table.Column<int>(type: "int", nullable: false),
                    ModelDecidedGrant = table.Column<bool>(type: "bit", nullable: false),
                    DiscountPercent = table.Column<int>(type: "int", nullable: false),
                    DecisionReason = table.Column<string>(type: "nvarchar(500)", maxLength: 500, nullable: false),
                    DecidedAt = table.Column<DateTime>(type: "datetime2", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_VoucherDecisionLog", x => x.Id);
                    // Tạo khóa ngoại nối sang bảng VoucherFeatureLog
                    table.ForeignKey(
                        name: "FK_VoucherDecisionLog_VoucherFeatureLog_FeatureLogId",
                        column: x => x.FeatureLogId,
                        principalTable: "VoucherFeatureLog",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                });

            // 3. Thêm các cột ImageUrl vào các bảng dịch vụ cũ (như trong file đầu tiên bạn muốn)
            migrationBuilder.AddColumn<string>(name: "ImageUrl", table: "Transfers", type: "nvarchar(300)", maxLength: 300, nullable: false, defaultValue: "");
            migrationBuilder.AddColumn<string>(name: "ImageUrl", table: "Tours", type: "nvarchar(300)", maxLength: 300, nullable: false, defaultValue: "");
            migrationBuilder.AddColumn<string>(name: "ImageUrl", table: "Hotels", type: "nvarchar(300)", maxLength: 300, nullable: false, defaultValue: "");
            migrationBuilder.AddColumn<string>(name: "ImageUrl", table: "Flights", type: "nvarchar(300)", maxLength: 300, nullable: false, defaultValue: "");
            migrationBuilder.AddColumn<string>(name: "ImageUrl", table: "Cars", type: "nvarchar(300)", maxLength: 300, nullable: false, defaultValue: "");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            // Hạ cấp: Xóa các cột và bảng đã thêm nếu Rollback
            migrationBuilder.DropColumn(name: "ImageUrl", table: "Transfers");
            migrationBuilder.DropColumn(name: "ImageUrl", table: "Tours");
            migrationBuilder.DropColumn(name: "ImageUrl", table: "Hotels");
            migrationBuilder.DropColumn(name: "ImageUrl", table: "Flights");
            migrationBuilder.DropColumn(name: "ImageUrl", table: "Cars");

            migrationBuilder.DropTable(name: "VoucherDecisionLog");
            migrationBuilder.DropTable(name: "VoucherFeatureLog");
        }
    }
}