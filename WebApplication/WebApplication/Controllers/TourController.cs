using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using TravelApp.Data;
using TravelApp.Models;
using TravelApp.Repositories;

namespace TravelApp.Controllers;

public class TourController : Controller
{
    private readonly ITourRepository _tourRepo;
    private readonly ApplicationDbContext _context;

    public TourController(ITourRepository tourRepo, ApplicationDbContext context)
    {
        _tourRepo = tourRepo;
        _context = context;
    }

    public async Task<IActionResult> Index() => View(await _tourRepo.GetAllAsync());

    [HttpPost]
    [Authorize]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Book(int id)
    {
        var tour = await _tourRepo.GetByIdAsync(id);
        if (tour == null) return NotFound();

        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(userIdString, out int userId))
        {
            var booking = new Booking
            {
                UserId = userId,
                BookingType = "Tour",
                ReferenceId = tour.Id,
                TotalAmount = tour.Price,
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
    public async Task<IActionResult> Create(Tour tour)
    {
        if (ModelState.IsValid)
        {
            await _tourRepo.AddAsync(tour);
            await _tourRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(tour);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Edit(int id)
    {
        var tour = await _tourRepo.GetByIdAsync(id);
        if (tour == null) return NotFound();
        return View(tour);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(int id, Tour tour)
    {
        if (id != tour.Id) return NotFound();
        if (ModelState.IsValid)
        {
            _tourRepo.Update(tour);
            await _tourRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(tour);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        var tour = await _tourRepo.GetByIdAsync(id);
        if (tour == null) return NotFound();
        return View(tour);
    }

    [HttpPost, ActionName("Delete")]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteConfirmed(int id)
    {
        var tour = await _tourRepo.GetByIdAsync(id);
        if (tour != null)
        {
            _tourRepo.Delete(tour);
            await _tourRepo.SaveAsync();
        }
        return RedirectToAction(nameof(Index));
    }

    public async Task<IActionResult> Details(int id)
    {
        var tour = await _tourRepo.GetByIdAsync(id);
        if (tour == null) return NotFound();
        return View(tour);
    }
}