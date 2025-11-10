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

# Cities list - moved here since it's not imported
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
    {"name": "Nashville", "lat": 36.1627, "lon": -86.7816},
    {"name": "Cleveland", "lat": 41.4993, "lon": -81.6944},
    {"name": "Pittsburgh", "lat": 40.4406, "lon": -79.9959},
    {"name": "San Antonio", "lat": 29.4241, "lon": -98.4936},
    {"name": "San Diego", "lat": 32.7157, "lon": -117.1611},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "Detroit", "lat": 42.3314, "lon": -83.0458},
    {"name": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
    {"name": "Charlotte", "lat": 35.2271, "lon": -80.8431},
    {"name": "Indianapolis", "lat": 39.7684, "lon": -86.1581},
    {"name": "Columbus", "lat": 39.9612, "lon": -82.9988},
    {"name": "Memphis", "lat": 35.1495, "lon": -90.0490},
    {"name": "Louisville", "lat": 38.2527, "lon": -85.7585},
    {"name": "Birmingham", "lat": 33.5186, "lon": -86.8104},
    {"name": "Albuquerque", "lat": 35.0844, "lon": -106.6504},
    {"name": "Tucson", "lat": 32.2226, "lon": -110.9747},
    {"name": "Fresno", "lat": 36.7378, "lon": -119.7871},
    {"name": "Sacramento", "lat": 38.5816, "lon": -121.4944},
    {"name": "Mesa", "lat": 33.4152, "lon": -111.8315},
    {"name": "Omaha", "lat": 41.2565, "lon": -95.9345},
    {"name": "Colorado Springs", "lat": 38.8339, "lon": -104.8214},
    {"name": "Raleigh", "lat": 35.7796, "lon": -78.6382},
    {"name": "Boise", "lat": 43.6150, "lon": -116.2023},
    {"name": "Port Angeles", "lat": 48.1181, "lon": -123.4307},  # WA
    {"name": "Astoria", "lat": 46.1879, "lon": -123.8313},       # OR
    {"name": "Eureka", "lat": 40.8021, "lon": -124.1637},        # CA
    {"name": "McAllen", "lat": 26.2034, "lon": -98.2300},        # TX
    {"name": "Bangor", "lat": 44.8016, "lon": -68.7712},          # ME
    {"name": "Oakland", "lat": 37.8044, "lon": -122.2711},     # ← ADDED
]

api_key = "5b5018f6a2f88c720738cb591971059b"

def create_pressure_contour_overlay(pressure_data):
    """Create pressure contour overlay"""
    if len(pressure_data) < 4:
        print("Not enough pressure data for contour creation")
        return None, None, None, None, None
    
    # Extract coordinates and pressures
    lats = [d['lat'] for d in pressure_data]
    lons = [d['lon'] for d in pressure_data]
    pressures = [d['pressure'] for d in pressure_data]
    
    # Define continental US boundaries
    lat_min, lat_max = 24.0, 50.0  # From southern Texas to northern border
    lon_min, lon_max = -125.0, -66.0  # From west coast to east coast
    
    # Create interpolation grid that covers entire continental US
    grid_lat = np.linspace(lat_min, lat_max, 120)
    grid_lon = np.linspace(lon_min, lon_max, 160)
    grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
    
    # Interpolate pressure data with extrapolation to fill boundaries
    points = np.column_stack((lons, lats))
    
    # Use 'linear' interpolation with fill_value for extrapolation
    grid_pressure = griddata(points, pressures, (grid_lon_mesh, grid_lat_mesh), 
                           method='linear', fill_value=np.mean(pressures))
    
    # Apply additional smoothing using nearest neighbor for any remaining NaN values
    mask = np.isnan(grid_pressure)
    if np.any(mask):
        grid_pressure_nearest = griddata(points, pressures, (grid_lon_mesh, grid_lat_mesh), 
                                       method='nearest')
        grid_pressure[mask] = grid_pressure_nearest[mask]
    
    # Create contour plot
    fig, ax = plt.subplots(figsize=(14, 10))  # Larger figure for better coverage
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    
    # Define pressure levels - 5 hPa intervals
    min_pressure = min(pressures)
    max_pressure = max(pressures)
    
    # Extend the pressure range for better coverage
    start_pressure = int((min_pressure - 15) / 5) * 5
    end_pressure = int((max_pressure + 15) / 5 + 1) * 5
    levels = np.arange(start_pressure, end_pressure + 1, 5)  # Every 5 hPa
    
    # Create colormap for pressure (blue = low pressure, red = high pressure)
    colors_list = ['#000080', '#0040FF', '#0080FF', '#00BFFF', '#80DFFF', 
                   '#FFFFFF', '#FFE080', '#FFBF00', '#FF8000', '#FF4000', '#FF0000']
    cmap = colors.LinearSegmentedColormap.from_list('pressure', colors_list, N=len(levels)-1)
    
    # Create filled contours that extend to boundaries
    contourf = ax.contourf(grid_lon_mesh, grid_lat_mesh, grid_pressure, 
                          levels=levels, cmap=cmap, alpha=0.7, extend='both')
    
    # Create contour lines with 5 hPa intervals
    contour = ax.contour(grid_lon_mesh, grid_lat_mesh, grid_pressure, 
                        levels=levels, colors='black', alpha=0.8, linewidths=0.7)
    
    # Add labels to ALL contour lines (every 5 hPa)
    clabel = ax.clabel(contour, levels=levels, inline=True, fontsize=8, fmt='%d', 
                      inline_spacing=15, manual=False)
    
    # Make the labels more readable with white background
    for txt in clabel:
        txt.set_bbox(dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.9))
    
    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    
    # Save to memory
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, 
               transparent=True, dpi=150)
    buffer.seek(0)
    
    # Convert to base64 for web use
    img_str = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return img_str, lat_min, lat_max, lon_min, lon_max

def get_pressure_data():
    """Fetch atmospheric pressure data for all cities"""
    pressure_data = []
    print("Fetching atmospheric pressure data...")
    
    for i, city in enumerate(cities):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={city['lat']}&lon={city['lon']}&appid={api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            if data.get("main"):
                pressure_hpa = data["main"]["pressure"]
                pressure_data.append({
                    'lat': city['lat'],
                    'lon': city['lon'],
                    'pressure': pressure_hpa,
                    'name': city['name']
                })
                print(f"✓ {city['name']}: {pressure_hpa} hPa")
            else:
                print(f"✗ Failed to get data for {city['name']}")
                
        except Exception as e:
            print(f"✗ Error fetching data for {city['name']}: {e}")
            
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{len(cities)} cities")
    
    return pressure_data

def create_pressure_contour_map():
    """Create the main atmospheric pressure contour map"""
    # Get pressure data
    pressure_data = get_pressure_data()
    
    if not pressure_data:
        print("No pressure data available!")
        return None
    
    print(f"\nCreating atmospheric pressure contour map with {len(pressure_data)} data points...")
    
    # Create the base map focused on continental US
    m = folium.Map(
        location=[39.8283, -98.5795],  # Center of continental US
        zoom_start=4,
        tiles='OpenStreetMap'
    )
    
    # Create contour overlay
    contour_result = create_pressure_contour_overlay(pressure_data)
    
    if contour_result[0]:  # Check if contour_img exists
        contour_img, lat_min, lat_max, lon_min, lon_max = contour_result
        
        # Add contour overlay to map
        raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{contour_img}",
            bounds=[[lat_min, lon_min], [lat_max, lon_max]],
            opacity=0.6,
            name="Pressure Contours"
        ).add_to(m)
    
    # Add pressure legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 180px; height: 110px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Atmospheric Pressure (hPa)</b></p>
    <p><span style="color:blue">■</span> Low Pressure (< 1010 hPa)</p>
    <p><span style="color:white; background:gray">■</span> Normal (1010-1020 hPa)</p>
    <p><span style="color:red">■</span> High Pressure (> 1020 hPa)</p>
    <p><small>Blue = Stormy, Red = Fair</small></p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

if __name__ == "__main__":
    try:
        map_obj = create_pressure_contour_map()
        if map_obj:
            # Ensure the maps directory exists
            os.makedirs("D:/Documents/Python_work/maps", exist_ok=True)
            
            # Save the map
            map_obj.save("D:/Documents/Python_work/maps/pressure_contour_map.html")
            print("\n✓ Atmospheric pressure contour map saved as 'pressure_contour_map.html'")
            print("Open the file in your browser to view the pressure contours!")
        else:
            print("Failed to create map")
            
    except Exception as e:
        print(f"Error creating atmospheric pressure contour map: {e}")