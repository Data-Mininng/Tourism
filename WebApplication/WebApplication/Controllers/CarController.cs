using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using TravelApp.Data;
using TravelApp.Models;
using TravelApp.Repositories;

namespace TravelApp.Controllers;

public class CarController : Controller
{
    private readonly ICarRepository _carRepo;
    private readonly ApplicationDbContext _context;

    public CarController(ICarRepository carRepo, ApplicationDbContext context)
    {
        _carRepo = carRepo;
        _context = context;
    }

    // ========================================================
    // KHU VỰC CÔNG KHAI (Ai cũng xem được, không cần đăng nhập)
    // ========================================================

    public async Task<IActionResult> Index() => View(await _carRepo.GetAllAsync());

    public async Task<IActionResult> Details(int id)
    {
        var car = await _carRepo.GetByIdAsync(id);
        if (car == null) return NotFound();
        return View(car);
    }

    // ========================================================
    // KHU VỰC QUẢN TRỊ (Bắt buộc đăng nhập và phải có Role="Admin")
    // ========================================================

    [Authorize(Roles = "Admin")]
    public IActionResult Create() => View();

    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(Car car)
    {
        if (ModelState.IsValid)
        {
            await _carRepo.AddAsync(car);
            await _carRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(car);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Edit(int id)
    {
        var car = await _carRepo.GetByIdAsync(id);
        if (car == null) return NotFound();
        return View(car);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(int id, Car car)
    {
        if (id != car.Id) return NotFound();
        if (ModelState.IsValid)
        {
            _carRepo.Update(car);
            await _carRepo.SaveAsync();
            return RedirectToAction(nameof(Index));
        }
        return View(car);
    }

    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        var car = await _carRepo.GetByIdAsync(id);
        if (car == null) return NotFound();
        return View(car);
    }

    [HttpPost, ActionName("Delete")]
    [Authorize(Roles = "Admin")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteConfirmed(int id)
    {
        var car = await _carRepo.GetByIdAsync(id);
        if (car != null)
        {
            _carRepo.Delete(car);
            await _carRepo.SaveAsync();
        }
        return RedirectToAction(nameof(Index));
    }
}