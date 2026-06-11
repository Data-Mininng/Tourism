using Microsoft.EntityFrameworkCore;
using TravelApp.Data;
using TravelApp.Models;

namespace TravelApp.Repositories;

public class TourRepository : ITourRepository
{
    private readonly ApplicationDbContext _context;
    public TourRepository(ApplicationDbContext context) => _context = context;

    public async Task<IEnumerable<Tour>> GetAllAsync() => await _context.Tours.ToListAsync();
    public async Task<Tour?> GetByIdAsync(int id) => await _context.Tours.FindAsync(id);
    public async Task AddAsync(Tour entity) => await _context.Tours.AddAsync(entity);
    public void Update(Tour entity) => _context.Tours.Update(entity);
    public void Delete(Tour entity) => _context.Tours.Remove(entity);
    public async Task SaveAsync() => await _context.SaveChangesAsync();
}