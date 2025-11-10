def add_pressure_contour_layer(map_obj, pressure_data):
    """Add pressure contour lines to the map."""
    if len(pressure_data) < 4:
        print("Not enough pressure data for contour creation")
        return None
    
    # Extract coordinates and pressures
    lats = [d['lat'] for d in pressure_data]
    lons = [d['lon'] for d in pressure_data]
    pressures = [d['pressure'] for d in pressure_data]
    
    # Create grid for interpolation
    lat_min, lat_max = min(lats) - 2, max(lats) + 2
    lon_min, lon_max = min(lons) - 2, max(lons) + 2
    
    # Create interpolation grid
    grid_lat = np.linspace(lat_min, lat_max, 100)
    grid_lon = np.linspace(lon_min, lon_max, 100)
    grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
    
    # Interpolate pressure data
    points = np.column_stack((lons, lats))
    grid_pressure = griddata(points, pressures, (grid_lon_mesh, grid_lat_mesh), method='cubic')
    
    # Create contour lines
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    
    # Define pressure levels and colors
    levels = np.arange(int(min(pressures)) - 5, int(max(pressures)) + 10, 5)
    
    # Create filled contours
    contourf = ax.contourf(grid_lon_mesh, grid_lat_mesh, grid_pressure, levels=levels, cmap='Blues', alpha=0.6)
    
    # Create contour lines
    contour = ax.contour(grid_lon_mesh, grid_lat_mesh, grid_pressure, levels=levels, colors='black', alpha=0.4, linewidths=0.5)
    
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