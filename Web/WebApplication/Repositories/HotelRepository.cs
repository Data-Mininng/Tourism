using Microsoft.EntityFrameworkCore;
using TravelApp.Data;
using TravelApp.Models;

namespace TravelApp.Repositories;

public class HotelRepository : IHotelRepository
{
    private readonly ApplicationDbContext _context;
    public HotelRepository(ApplicationDbContext context) => _context = context;

    public async Task<IEnumerable<Hotel>> GetAllAsync() => await _context.Hotels.ToListAsync();
    public async Task<Hotel?> GetByIdAsync(int id) => await _context.Hotels.FindAsync(id);
    public async Task AddAsync(Hotel entity) => await _context.Hotels.AddAsync(entity);
    public void Update(Hotel entity) => _context.Hotels.Update(entity);
    public void Delete(Hotel entity) => _context.Hotels.Remove(entity);
    public async Task SaveAsync() => await _context.SaveChangesAsync();
}