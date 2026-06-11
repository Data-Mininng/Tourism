using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using TravelApp.Data;
using TravelApp.Models;
using TravelApp.Repositories;

namespace TravelApp.Controllers;

public class HotelController : Controller
{
    private readonly IHotelRepository _hotelRepo;
    private readonly ApplicationDbContext _context;

    public HotelController(IHotelRepository hotelRepo, ApplicationDbContext context)
    {
        _hotelRepo = hotelRepo;
        _context = context;
    }

    public async Task<IActionResult> Index() => View(await _hotelRepo.GetAllAsync());

    [HttpPost]
    [Authorize]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Book(int id)
    {
        var hotel = await _hotelRepo.GetByIdAsync(id);
        if (hotel == null) return NotFound();

        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(userIdString, out int userId))
        {
            var booking = new Booking
            {
                UserId = userId,
                BookingType = "Hotel",
                ReferenceId = hotel.Id,
                TotalAmount = hotel.PricePerNight,
                Status = "Pending",
                PaymentStatus = "Unpaid",
                BookingDate = System.DateTime.Now
            };
            _context.Bookings.Add(booking);
            await _context.SaveChangesAsync();
        }
        return RedirectToAction("Index", "Dashboard");
    }

    [Authorize(Roles = "Admin")]
    public IActionResult Create() => View();

    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(Hotel hotel)
    {
        if (ModelState.IsValid)
        {
            await _hotelRepo.AddAsync(hotel);
            await _hotelRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(hotel);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Edit(int id)
    {
        var hotel = await _hotelRepo.GetByIdAsync(id);
        if (hotel == null) return NotFound();
        return View(hotel);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(int id, Hotel hotel)
    {
        if (id != hotel.Id) return NotFound();
        if (ModelState.IsValid)
        {
            _hotelRepo.Update(hotel);
            await _hotelRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(hotel);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        var hotel = await _hotelRepo.GetByIdAsync(id);
        if (hotel == null) return NotFound();
        return View(hotel);
    }

    [HttpPost, ActionName("Delete")]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteConfirmed(int id)
    {
        var hotel = await _hotelRepo.GetByIdAsync(id);
        if (hotel != null)
        {
            _hotelRepo.Delete(hotel);
            await _hotelRepo.SaveAsync();
        }
        return RedirectToAction(nameof(Index));
    }

    public async Task<IActionResult> Details(int id)
    {
        var hotel = await _hotelRepo.GetByIdAsync(id);
        if (hotel == null) return NotFound();
        return View(hotel);
    }
}