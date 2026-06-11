using Microsoft.EntityFrameworkCore;
using TravelApp.Data;
using TravelApp.Models;

namespace TravelApp.Repositories;

public class TransferRepository : ITransferRepository
{
    private readonly ApplicationDbContext _context;
    public TransferRepository(ApplicationDbContext context) => _context = context;

    public async Task<IEnumerable<Transfer>> GetAllAsync() => await _context.Transfers.ToListAsync();
    public async Task<Transfer?> GetByIdAsync(int id) => await _context.Transfers.FindAsync(id);
    public async Task AddAsync(Transfer entity) => await _context.Transfers.AddAsync(entity);
    public void Update(Transfer entity) => _context.Transfers.Update(entity);
    public void Delete(Transfer entity) => _context.Transfers.Remove(entity);
    public async Task SaveAsync() => await _context.SaveChangesAsync();
}