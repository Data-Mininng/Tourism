var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllersWithViews();
var rapidApiKey = builder.Configuration["RapidApi:Key"];
var rapidApiHost = builder.Configuration["RapidApi:Host"];
// Đăng ký HttpClient có tên nhận diện là "FlightApi"
builder.Services.AddHttpClient("FlightApi", client =>
{
    // Tự động gán Host làm URL gốc
    client.BaseAddress = new Uri($"https://{rapidApiHost}");

    // Tự động nhét API Key và Host vào Header của mọi Request
    client.DefaultRequestHeaders.Add("X-RapidAPI-Key", rapidApiKey);
    client.DefaultRequestHeaders.Add("X-RapidAPI-Host", rapidApiHost);
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseRouting();

app.UseAuthorization();

app.MapStaticAssets();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}")
    .WithStaticAssets();


app.Run();
