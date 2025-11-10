import folium
from folium import raster_layers
import requests
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import base64
from io import BytesIO
import os

# Cities list
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
    {"name": "Washington DC", "lat": 38.9072, "lon": -77.0369},
    {"name": "Atlanta", "lat": 33.7490, "lon": -84.3880},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
    {"name": "Las Vegas", "lat": 36.1699, "lon": -115.1398},
    {"name": "Portland", "lat": 45.5152, "lon": -122.6784},
    {"name": "Minneapolis", "lat": 44.9778, "lon": -93.2650},
    {"name": "New Orleans", "lat": 29.9511, "lon": -90.0715},
    {"name": "Salt Lake City", "lat": 40.7608, "lon": -111.8910},
    {"name": "Tampa", "lat": 27.9506, "lon": -82.4572},
    {"name": "Kansas City", "lat": 39.0997, "lon": -94.5786},
    {"name": "Nashville", "lat": 36.1627, "lon": -86.7816}
]

api_key = "5b5018f6a2f88c720738cb591971059b"

def fetch_temperature_data():
    """Fetch temperature data from the weather API."""
    weather_data = []
    print("Fetching temperature data...")
    
    for i, city in enumerate(cities):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={city['lat']}&lon={city['lon']}&appid={api_key}&units=imperial"
            response = requests.get(url)
            data = response.json()
            
            if data.get("main"):
                temp_f = data["main"]["temp"]
                weather_data.append({
                    'lat': city['lat'],
                    'lon': city['lon'],
                    'temp': temp_f,
                    'name': city['name']
                })
                print(f"✓ {city['name']}: {temp_f:.1f}°F")
            else:
                print(f"✗ Failed to get data for {city['name']}")
                
        except Exception as e:
            print(f"✗ Error fetching data for {city['name']}: {e}")
            
    return weather_data

def generate_temperature_contours(weather_data):
    """Generate temperature contours from the weather data."""
    if len(weather_data) < 4:
        print("Not enough weather data for contour creation")
        return None
    
    # Extract coordinates and temperatures
    lats = [d['lat'] for d in weather_data]
    lons = [d['lon'] for d in weather_data]
    temps = [d['temp'] for d in weather_data]
    
    # Create grid for interpolation
    lat_min, lat_max = min(lats) - 2, max(lats) + 2
    lon_min, lon_max = min(lons) - 2, max(lons) + 2
    
    # Create interpolation grid
    grid_lat = np.linspace(lat_min, lat_max, 80)
    grid_lon = np.linspace(lon_min, lon_max, 80)
    grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
    
    # Interpolate temperature data
    points = np.column_stack((lons, lats))
    grid_temp = griddata(points, temps, (grid_lon_mesh, grid_lat_mesh), method='cubic')
    
    # Create contour plot
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    
    # Define temperature levels and colors
    levels = np.arange(int(min(temps)) - 5, int(max(temps)) + 10, 5)
    
    # Create colormap
    colors_list = ['#000080', '#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF8000', '#FF0000', '#800000']
    n_bins = len(levels) - 1
    cmap = colors.LinearSegmentedColormap.from_list('temp', colors_list, N=n_bins)
    
    # Create filled contours
    contourf = ax.contourf(grid_lon_mesh, grid_lat_mesh, grid_temp, levels=levels, cmap=cmap, alpha=0.6)
    
    # Create contour lines
    contour = ax.contour(grid_lon_mesh, grid_lat_mesh, grid_temp, levels=levels, colors='black', alpha=0.4, linewidths=0.5)
    
    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    
    # Save to memory
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, transparent=True, dpi=150)
    buffer.seek(0)
    
    # Convert to base64 for web use
    img_str = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return img_str, lat_min, lat_max, lon_min, lon_max

def create_temperature_map(weather_data):
    """Create a temperature contour map."""
    # Create the base map focused on continental US
    m = folium.Map(
        location=[39.8283, -98.5795],  # Center of continental US
        zoom_start=4,
        tiles='OpenStreetMap'
    )
    
    # Generate contours
    contour_result = generate_temperature_contours(weather_data)
    
    if contour_result and contour_result[0]:  # Check if contour_img exists
        contour_img, lat_min, lat_max, lon_min, lon_max = contour_result
        
        # Add contour overlay to map
        raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{contour_img}",
            bounds=[[lat_min, lon_min], [lat_max, lon_max]],
            opacity=0.6,
            name="Temperature Contours"
        ).add_to(m)
    
    # Add temperature legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Temperature (°F)</b></p>
    <p><span style="color:blue">■</span> Cold (< 40°F)</p>
    <p><span style="color:cyan">■</span> Cool (40-60°F)</p>
    <p><span style="color:yellow">■</span> Warm (60-80°F)</p>
    <p><span style="color:red">■</span> Hot (> 80°F)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def display_temperature_map(map_obj):
    """Display the temperature contour map."""
    if map_obj:
        # Ensure the maps directory exists
        os.makedirs("D:/Documents/Python_work/maps", exist_ok=True)
        
        # Save the map
        map_obj.save("D:/Documents/Python_work/maps/temperature_contour_map.html")
        print("\n✓ Temperature contour map saved as 'temperature_contour_map.html'")
        print("Open the file in your browser to view the temperature contours!")
        return True
    else:
        print("Failed to create temperature map")
        return False

# Main execution
if __name__ == "__main__":
    try:
        # Fetch temperature data
        weather_data = fetch_temperature_data()
        
        if weather_data:
            print(f"\nCreating temperature contour map with {len(weather_data)} data points...")
            
            # Create temperature map
            map_obj = create_temperature_map(weather_data)
            
            # Display/save the map
            display_temperature_map(map_obj)
        else:
            print("No weather data available!")
    except Exception as e:
        print(f"Error creating temperature contour map: {e}")