using Microsoft.EntityFrameworkCore;
using TravelApp.Data;
using TravelApp.Models;

namespace TravelApp.Repositories;

public class CarRepository : ICarRepository
{
    private readonly ApplicationDbContext _context;
    public CarRepository(ApplicationDbContext context) => _context = context;

    public async Task<IEnumerable<Car>> GetAllAsync() => await _context.Cars.ToListAsync();
    public async Task<Car?> GetByIdAsync(int id) => await _context.Cars.FindAsync(id);
    public async Task AddAsync(Car entity) => await _context.Cars.AddAsync(entity);
    public void Update(Car entity) => _context.Cars.Update(entity);
    public void Delete(Car entity) => _context.Cars.Remove(entity);
    public async Task SaveAsync() => await _context.SaveChangesAsync();
}