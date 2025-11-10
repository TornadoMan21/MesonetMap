def get_weather_data(api_key):
    """Fetch weather data for all cities"""
    weather_data = []
    print("Fetching weather data...")
    
    cities = [
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
        {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
        {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
        {"name": "Miami", "lat": 25.7617, "lon": -80.1918},
        {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
        {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
        {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740},
        {"name": "Boston", "lat": 42.3601, "lon": -71.0589},
        # Add more cities as needed
    ]
    
    for city in cities:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={city['lat']}&lon={city['lon']}&appid={api_key}&units=imperial"
            response = requests.get(url)
            data = response.json()
            
            if data.get("main"):
                temp_f = data["main"]["temp"]
                pressure_hpa = data["main"]["pressure"]
                weather_data.append({
                    'lat': city['lat'],
                    'lon': city['lon'],
                    'temp': temp_f,
                    'pressure': pressure_hpa,
                    'name': city['name']
                })
                print(f"✓ {city['name']}: {temp_f:.1f}°F, Pressure: {pressure_hpa} hPa")
            else:
                print(f"✗ Failed to get data for {city['name']}")
                
        except Exception as e:
            print(f"✗ Error fetching data for {city['name']}: {e}")
    
    return weather_data