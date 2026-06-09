using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using TravelApp.Data;
using TravelApp.Models;
using TravelApp.Repositories;

namespace TravelApp.Controllers;

public class TransferController : Controller
{
    private readonly ITransferRepository _transferRepo;
    private readonly ApplicationDbContext _context;

    public TransferController(ITransferRepository transferRepo, ApplicationDbContext context)
    {
        _transferRepo = transferRepo;
        _context = context;
    }

    public async Task<IActionResult> Index() => View(await _transferRepo.GetAllAsync());

    [HttpPost]
    [Authorize]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Book(int id)
    {
        var transfer = await _transferRepo.GetByIdAsync(id);
        if (transfer == null) return NotFound();

        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(userIdString, out int userId))
        {
            var booking = new Booking
            {
                UserId = userId,
                BookingType = "Transfer",
                ReferenceId = transfer.Id,
                TotalAmount = transfer.Price,
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
    public async Task<IActionResult> Create(Transfer transfer)
    {
        if (ModelState.IsValid)
        {
            await _transferRepo.AddAsync(transfer);
            await _transferRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(transfer);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Edit(int id)
    {
        var transfer = await _transferRepo.GetByIdAsync(id);
        if (transfer == null) return NotFound();
        return View(transfer);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(int id, Transfer transfer)
    {
        if (id != transfer.Id) return NotFound();
        if (ModelState.IsValid)
        {
            _transferRepo.Update(transfer);
            await _transferRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(transfer);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        var transfer = await _transferRepo.GetByIdAsync(id);
        if (transfer == null) return NotFound();
        return View(transfer);
    }

    [HttpPost, ActionName("Delete")]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteConfirmed(int id)
    {
        var transfer = await _transferRepo.GetByIdAsync(id);
        if (transfer != null)
        {
            _transferRepo.Delete(transfer);
            await _transferRepo.SaveAsync();
        }
        return RedirectToAction(nameof(Index));
    }

    public async Task<IActionResult> Details(int id)
    {
        var transfer = await _transferRepo.GetByIdAsync(id);
        if (transfer == null) return NotFound();
        return View(transfer);
    }
}