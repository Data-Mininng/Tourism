using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
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
    }
}