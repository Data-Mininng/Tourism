using Microsoft.EntityFrameworkCore;
using TravelApp.Data;
using TravelApp.Models;

namespace TravelApp.Repositories;

public class FlightRepository : IFlightRepository
{
    private readonly ApplicationDbContext _context;
    public FlightRepository(ApplicationDbContext context) => _context = context;

    public async Task<IEnumerable<Flight>> GetAllAsync() => await _context.Flights.ToListAsync();
    public async Task<Flight?> GetByIdAsync(int id) => await _context.Flights.FindAsync(id);
    public async Task AddAsync(Flight entity) => await _context.Flights.AddAsync(entity);
    public void Update(Flight entity) => _context.Flights.Update(entity);
    public void Delete(Flight entity) => _context.Flights.Remove(entity);
    public async Task SaveAsync() => await _context.SaveChangesAsync();
}