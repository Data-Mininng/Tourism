using System.Linq.Expressions;
using TravelApp.Models;

namespace TravelApp.Repositories;

public interface IRepository<T> where T : class
{
    Task<IEnumerable<T>> GetAllAsync();
    Task<T?> GetByIdAsync(int id);
    Task AddAsync(T entity);
    void Update(T entity);
    void Delete(T entity);
    Task SaveAsync();
}

// Specific interfaces
public interface ICarRepository : IRepository<Car> { }
public interface IFlightRepository : IRepository<Flight> { }
public interface IHotelRepository : IRepository<Hotel> { }
public interface ITourRepository : IRepository<Tour> { }
public interface ITransferRepository : IRepository<Transfer> { }