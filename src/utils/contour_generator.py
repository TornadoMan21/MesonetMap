def generate_contour_data(weather_data, variable='temperature'):
    """Generate contour data for the specified variable (temperature or pressure)."""
    if len(weather_data) < 4:
        print("Not enough weather data for contour creation")
        return None
    
    # Extract coordinates and variable data
    lats = [d['lat'] for d in weather_data]
    lons = [d['lon'] for d in weather_data]
    values = [d[variable] for d in weather_data]
    
    # Create grid for interpolation
    lat_min, lat_max = min(lats) - 2, max(lats) + 2
    lon_min, lon_max = min(lons) - 2, max(lons) + 2
    
    # Create interpolation grid
    grid_lat = np.linspace(lat_min, lat_max, 100)
    grid_lon = np.linspace(lon_min, lon_max, 100)
    grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
    
    # Interpolate variable data
    points = np.column_stack((lons, lats))
    grid_values = griddata(points, values, (grid_lon_mesh, grid_lat_mesh), method='cubic')
    
    return grid_lon_mesh, grid_lat_mesh, grid_values

def create_pressure_contour_map(weather_data):
    """Create a contour map for atmospheric pressure."""
    print(f"\nCreating pressure contour map with {len(weather_data)} data points...")
    
    # Generate contour data for pressure
    grid_lon_mesh, grid_lat_mesh, grid_values = generate_contour_data(weather_data, variable='pressure')
    
    if grid_values is None:
        print("Failed to generate pressure contour data.")
        return None
    
    # Create the contour plot
    fig, ax = plt.subplots(figsize=(12, 8))
    levels = np.arange(int(min(grid_values.flatten())), int(max(grid_values.flatten())), 1)
    
    # Create filled contours
    contourf = ax.contourf(grid_lon_mesh, grid_lat_mesh, grid_values, levels=levels, cmap='viridis', alpha=0.6)
    
    # Create contour lines
    contour = ax.contour(grid_lon_mesh, grid_lat_mesh, grid_values, levels=levels, colors='black', alpha=0.4, linewidths=0.5)
    
    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')
    
    # Save to memory
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, transparent=True, dpi=300)
    buffer.seek(0)
    
    # Convert to base64 for web use
    img_str = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return img_str

def get_pressure_color(pressure_hPa):
    """Get color based on atmospheric pressure."""
    if pressure_hPa < 1000:
        return 'blue'
    elif pressure_hPa < 1020:
        return 'green'
    elif pressure_hPa < 1030:
        return 'orange'
    else:
        return 'red'