using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using TravelApp.Data;
using TravelApp.Models;
using TravelApp.Repositories;

namespace TravelApp.Controllers;

public class FlightController : Controller
{
    private readonly IFlightRepository _flightRepo;
    private readonly ApplicationDbContext _context;

    public FlightController(IFlightRepository flightRepo, ApplicationDbContext context)
    {
        _flightRepo = flightRepo;
        _context = context;
    }

    public async Task<IActionResult> Index() => View(await _flightRepo.GetAllAsync());

    [HttpPost]
    [Authorize]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Book(int id)
    {
        var flight = await _flightRepo.GetByIdAsync(id);
        if (flight == null) return NotFound();

        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(userIdString, out int userId))
        {
            var booking = new Booking
            {
                UserId = userId,
                BookingType = "Flight",
                ReferenceId = flight.Id,
                TotalAmount = flight.Price,
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
    public async Task<IActionResult> Create(Flight flight)
    {
        if (ModelState.IsValid)
        {
            await _flightRepo.AddAsync(flight);
            await _flightRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(flight);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Edit(int id)
    {
        var flight = await _flightRepo.GetByIdAsync(id);
        if (flight == null) return NotFound();
        return View(flight);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(int id, Flight flight)
    {
        if (id != flight.Id) return NotFound();
        if (ModelState.IsValid)
        {
            _flightRepo.Update(flight);
            await _flightRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(flight);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        var flight = await _flightRepo.GetByIdAsync(id);
        if (flight == null) return NotFound();
        return View(flight);
    }

    [HttpPost, ActionName("Delete")]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteConfirmed(int id)
    {
        var flight = await _flightRepo.GetByIdAsync(id);
        if (flight != null)
        {
            _flightRepo.Delete(flight);
            await _flightRepo.SaveAsync();
        }
        return RedirectToAction(nameof(Index));
    }

    public async Task<IActionResult> Details(int id)
    {
        var flight = await _flightRepo.GetByIdAsync(id);
        if (flight == null) return NotFound();
        return View(flight);
    }
}