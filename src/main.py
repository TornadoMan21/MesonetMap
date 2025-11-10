import os
import sys
import time
import subprocess
import pandas as pd

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_and_install_requirements():
    """
    Check if required packages are installed and install them if missing
    """
    print("Checking required dependencies...")
    
    required_packages = {
        'folium': 'folium>=0.12.0',
        'requests': 'requests>=2.25.0',
        'numpy': 'numpy>=1.20.0',
        'scipy': 'scipy>=1.7.0',
        'matplotlib': 'matplotlib>=3.4.0',
        'pandas': 'pandas>=1.3.0'
    }
    
    missing_packages = []
    
    for package_name, package_spec in required_packages.items():
        try:
            __import__(package_name)
            print(f"✓ {package_name} is installed")
        except ImportError:
            print(f"✗ {package_name} is missing")
            missing_packages.append(package_spec)
    
    if missing_packages:
        print(f"\nInstalling {len(missing_packages)} missing packages...")
        
        for package in missing_packages:
            try:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install {package}: {e}")
                print("Please install manually using: pip install -r requirements.txt")
                return False
        
        print("\n✓ All dependencies installed successfully!")
    else:
        print("✓ All required packages are already installed")
    
    return True

def main():
    """Entry point of the multi-source weather mapping application."""
    print("Multi-Source Weather Mapping Application")
    print("Maryland + Pennsylvania + ASOS Data - Centered on Rockville, MD")
    print("=" * 65)
    
    # Check and install requirements first
    if not check_and_install_requirements():
        print("\n⚠ Some dependencies could not be installed automatically.")
        print("Please run: pip install -r requirements.txt")
        input("Press Enter to continue anyway (may cause errors)...")
    
    print()
    
    try:
        # Import only the mesonet data fetcher and config
        from data.mesonet_fetcher import fetch_all_mesonet_data, clean_temp_files
        from config.settings import MAPS_DIRECTORY
        
        print("✓ Mesonet modules imported successfully")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Available modules in current directory:")
        for item in os.listdir('.'):
            if os.path.isdir(item):
                print(f"  📁 {item}/")
        return
    
    # Create maps directory with better error handling
    try:
        if os.path.exists(MAPS_DIRECTORY) and not os.path.isdir(MAPS_DIRECTORY):
            # If 'maps' exists but is a file, rename it
            backup_name = f"{MAPS_DIRECTORY}_backup_{int(time.time())}"
            os.rename(MAPS_DIRECTORY, backup_name)
            print(f"⚠ Renamed existing file '{MAPS_DIRECTORY}' to '{backup_name}'")
        
        os.makedirs(MAPS_DIRECTORY, exist_ok=True)
        print(f"✓ Maps directory '{MAPS_DIRECTORY}' ready")
        
    except Exception as e:
        print(f"⚠ Warning: Could not create maps directory: {e}")
        # Use current directory as fallback
        MAPS_DIRECTORY = "."
        print(f"Using current directory for maps: {MAPS_DIRECTORY}")

    # Menu for user selection
    print("\nWeather Mapping Options:")
    print("1. Create combined weather map (temp colors + pressure contours)")
    print("2. Test data fetching only (MD Mesonet + PA Mesonet + ASOS)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == '2':
        # Test data fetching only with detailed debugging
        print("\n" + "="*50)
        print("TESTING WEATHER DATA FETCHING WITH DEBUG INFO")
        print("="*50)
        
        md_data, pa_file, va_data, asos_data = fetch_all_mesonet_data()
        
        print(f"\nResults:")
        
        # Handle different data types properly using hasattr check
        try:
            md_count = len(md_data) if hasattr(md_data, '__len__') and hasattr(md_data, 'empty') and not md_data.empty else 0
        except:
            md_count = "Processing error"
            
        try:
            va_count = len(va_data) if hasattr(va_data, '__len__') and hasattr(va_data, 'empty') and not va_data.empty else 0
        except:
            va_count = "Processing error"
        
        print(f"Maryland ASOS stations: {md_count}")
        print(f"Pennsylvania file: {pa_file}")
        print(f"Virginia ASOS stations: {va_count}")
        print(f"Additional ASOS stations: {len(asos_data) if asos_data else 0}")
        
        # Save Maryland data to file for inspection
        if hasattr(md_data, 'empty') and not md_data.empty:
            md_file = "temp_maryland_data.csv"
            md_data.to_csv(md_file, index=False)
            print(f"\n✓ Maryland data saved to: {md_file}")
            file_size = os.path.getsize(md_file) if os.path.exists(md_file) else 0
            print(f"File size: {file_size} bytes")
            print(f"Maryland data: {len(md_data)} records")
            print(f"Columns: {list(md_data.columns)}")
            if len(md_data) > 0:
                print("First few rows:")
                print(md_data.head(1))
        else:
            print("\n✗ No Maryland data retrieved")
        
        # Pennsylvania data is already saved as a file
        if pa_file:
            print(f"\n✓ Pennsylvania data saved to: {pa_file}")
            if os.path.exists(pa_file):
                file_size = os.path.getsize(pa_file)
                print(f"File size: {file_size} bytes")
                
                if file_size > 0:
                    try:
                        import pandas as pd
                        df = pd.read_csv(pa_file)
                        print(f"Pennsylvania CSV: {len(df)} records")
                        print(f"Columns: {list(df.columns)}")
                    except Exception as e:
                        print(f"Error reading Pennsylvania CSV: {e}")
                else:
                    print("File is empty!")
            else:
                print("File doesn't exist!")
        else:
            print("\n✗ No Pennsylvania data retrieved")
        
        # Save Virginia data to file for inspection
        if hasattr(va_data, 'empty') and not va_data.empty:
            va_file = "temp_virginia_data.csv"
            va_data.to_csv(va_file, index=False)
            print(f"\n✓ Virginia data saved to: {va_file}")
            file_size = os.path.getsize(va_file) if os.path.exists(va_file) else 0
            print(f"File size: {file_size} bytes")
            print(f"Virginia data: {len(va_data)} records")
            print(f"Columns: {list(va_data.columns)}")
            if len(va_data) > 0:
                print("First few rows:")
                print(va_data.head(1))
        else:
            print("\n✗ No Virginia data retrieved")
        
        # ASOS data debugging
        if asos_data:
            print(f"\n✓ ASOS data loaded: {len(asos_data)} stations")
            print("Sample ASOS stations:")
            for i, station in enumerate(asos_data[:3]):
                wind_info = ""
                if station.get('wind_speed') is not None:
                    wind_info = f", Wind: {station['wind_speed']:.1f} mph"
                    if station.get('wind_direction') is not None:
                        wind_info += f" from {station['wind_direction']:.0f}°"
                
                print(f"  {i+1}. {station['name']} ({station['state']}) - {station['temp_f']:.1f}°F, {station['pressure']:.1f} hPa{wind_info}")
        else:
            print("\n✗ No ASOS data retrieved")
            print("Check that asos.csv file exists in src/data/ directory")
        
        print("\nData files kept for inspection. Run choice 1 to create the combined map.")
        return
    
    try:
        # Fetch mesonet data and ASOS data
        print("\nFetching data from Maryland ASOS, Pennsylvania mesonet, Virginia ASOS, and additional ASOS stations...")
        md_data, pa_file, va_data, asos_data = fetch_all_mesonet_data()
        
        # Check data availability with proper type checking
        md_has_data = hasattr(md_data, 'empty') and not md_data.empty
        va_has_data = hasattr(va_data, 'empty') and not va_data.empty
        
        if not md_has_data and not pa_file and not va_has_data and not asos_data:
            print("✗ Failed to fetch any weather data!")
            print("\n💡 Suggestions:")
            print("   1. Check your internet connection")
            print("   2. The Iowa Environmental Mesonet might be temporarily down")
            print("   3. Ensure asos.csv file is present in src/data/ directory")
            print("   4. Try option 2 to see detailed error messages")
            return
        
        # Process Maryland data
        maryland_data = []
        if hasattr(md_data, 'empty') and not md_data.empty:
            maryland_data = convert_mesonet_to_weather_data(md_data)
            print(f"✓ Loaded {len(maryland_data)} Maryland ASOS stations")
        
        # Process Pennsylvania data  
        pennsylvania_data = []
        if pa_file:
            pennsylvania_data = load_pennsylvania_data_from_file(pa_file)
            print(f"✓ Loaded {len(pennsylvania_data)} Pennsylvania weather stations")
        
        # Process Virginia data
        virginia_data = []
        if hasattr(va_data, 'empty') and not va_data.empty:
            virginia_data = convert_mesonet_to_weather_data(va_data)
            print(f"✓ Loaded {len(virginia_data)} Virginia ASOS stations")
        
        # Process ASOS data (already processed by fetcher)
        asos_stations = []
        if asos_data:
            asos_stations = convert_asos_to_weather_data(asos_data)
            print(f"✓ Loaded {len(asos_stations)} ASOS weather stations")
        
        # Combine all weather data
        combined_data = maryland_data + pennsylvania_data + virginia_data + asos_stations
        
        if not combined_data:
            print("✗ No valid weather data found!")
            clean_temp_files()
            return
        
        # Remove duplicate stations based on coordinates (within 0.01 degrees)
        all_weather_data = []
        seen_locations = set()
        
        for station in combined_data:
            # Create a location key with rounded coordinates to detect duplicates
            lat_key = round(station['lat'], 2)  # Round to ~1km precision
            lon_key = round(station['lon'], 2)
            location_key = (lat_key, lon_key)
            
            if location_key not in seen_locations:
                seen_locations.add(location_key)
                all_weather_data.append(station)
            else:
                print(f"  Removed duplicate station near {lat_key}, {lon_key}")
        
        print(f"✓ Total weather stations (after deduplication): {len(all_weather_data)}")
        if len(all_weather_data) != len(combined_data):
            print(f"  Removed {len(combined_data) - len(all_weather_data)} duplicate stations")
        
        # Create the combined weather map
        print("\nCreating combined weather map...")
        print("  📊 Temperature-colored stations")
        print("  🌀 Pressure contours at 2 hPa intervals")
        
        combined_map = create_combined_weather_map_centered_rockville(all_weather_data)
        
        if combined_map:
            combined_filename = os.path.join(MAPS_DIRECTORY, "mesonet_combined_weather_map.html")
            combined_map.save(combined_filename)
            print("✓ Combined weather map created successfully!")
            print("  Features included:")
            print("    - Stations colored by temperature")
            print("    - Black pressure contour lines (2 hPa intervals)")
            print("    - Comprehensive legend with all information")
        else:
            print("✗ Failed to create combined weather map")
        
        # Clean up temporary files
        clean_temp_files()
        
        print(f"\n🎉 Multi-source weather mapping completed successfully!")
        print(f"📁 Map saved in: {os.path.abspath(MAPS_DIRECTORY)}")
        print("🌐 Open the HTML file in your browser to view the interactive map!")
        print("📍 Map is centered on Rockville, MD with MD + PA + ASOS data")
        
    except Exception as e:
        print(f"✗ Error during execution: {e}")
        print("Full error details:")
        import traceback
        traceback.print_exc()
        
        # Clean up on error
        clean_temp_files()

def create_combined_weather_map_centered_rockville(weather_data):
    """
    Create combined weather map with temperature-colored stations and pressure contours
    """
    import folium
    import numpy as np
    from scipy.interpolate import griddata
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.patches import FancyBboxPatch
    import io
    import base64
    
    if not weather_data:
        return None
    
    # Rockville, MD coordinates
    rockville_center = (39.0840, -77.1528)
    
    # Create base map centered on Rockville
    m = folium.Map(location=rockville_center, zoom_start=8)
    
    # Prepare data for contouring
    lats = []
    lons = []
    pressures = []
    temps = []
    
    for station in weather_data:
        lat = station['lat']
        lon = station['lon']
        pressure = station.get('pressure', 1013)
        temp_f = station.get('temp_f', station.get('temp', 70))
        
        lats.append(lat)
        lons.append(lon)
        pressures.append(pressure)
        temps.append(temp_f)
    
    # Convert to numpy arrays
    lats = np.array(lats)
    lons = np.array(lons)
    pressures = np.array(pressures)
    temps = np.array(temps)
    
    # Create pressure contours
    try:
        # Define grid for interpolation with better resolution
        lat_min, lat_max = lats.min() - 0.5, lats.max() + 0.5
        lon_min, lon_max = lons.min() - 0.5, lons.max() + 0.5
        
        # Create higher resolution grid for smoother contours
        grid_lat = np.linspace(lat_min, lat_max, 80)
        grid_lon = np.linspace(lon_min, lon_max, 80)
        grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
        
        # Interpolate pressure data using linear method for stability
        points = np.column_stack([lons, lats])
        grid_pressure = griddata(points, pressures, (grid_lon_mesh, grid_lat_mesh), 
                               method='linear', fill_value=np.nan)
        
        # Create pressure contour levels at 2 hPa intervals
        pressure_min = int(np.nanmin(pressures) / 2) * 2
        pressure_max = int(np.nanmax(pressures) / 2) * 2 + 2
        pressure_levels = np.arange(pressure_min, pressure_max + 1, 2)
        
        # Filter out NaN values from the grid for cleaner contours
        valid_mask = ~np.isnan(grid_pressure)
        if not valid_mask.any():
            print("Warning: No valid pressure data for contouring")
            raise ValueError("No valid pressure data")
        
        # Generate contour plot
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
        
        # Create contour lines with improved smoothing
        contour_lines = ax.contour(grid_lon_mesh, grid_lat_mesh, grid_pressure, 
                                 levels=pressure_levels, colors='black', 
                                 linewidths=1.2, alpha=0.9, linestyles='solid')
        
        # Add labels to contour lines (reduced frequency to avoid clutter)
        ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%d', 
                 inline_spacing=3, manual=False)
        
        # Remove axes and make transparent
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        fig.patch.set_alpha(0)
        ax.patch.set_alpha(0)
        
        # Save as image
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', transparent=True, bbox_inches='tight', 
                   dpi=150, facecolor='none', edgecolor='none')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        plt.close()
        
        # Add pressure contour overlay to map
        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{img_base64}",
            bounds=[[lat_min, lon_min], [lat_max, lon_max]],
            opacity=0.6,
            name="Pressure Contours (2 hPa intervals)"
        ).add_to(m)
        
    except Exception as e:
        print(f"Warning: Could not create pressure contours: {e}")
    
    # Add temperature-colored station markers
    for i, station in enumerate(weather_data):
        temp_f = station.get('temp_f', station.get('temp', 70))
        
        # Color based on temperature
        if temp_f < 32:
            color = '#0000FF'  # Blue - Freezing
            temp_category = "Freezing"
        elif temp_f < 40:
            color = '#4169E1'  # Royal Blue - Very Cold
            temp_category = "Very Cold"
        elif temp_f < 50:
            color = '#00BFFF'  # Deep Sky Blue - Cold
            temp_category = "Cold"
        elif temp_f < 60:
            color = '#00FF7F'  # Spring Green - Cool
            temp_category = "Cool"
        elif temp_f < 70:
            color = '#32CD32'  # Lime Green - Mild
            temp_category = "Mild"
        elif temp_f < 80:
            color = '#FFD700'  # Gold - Warm
            temp_category = "Warm"
        elif temp_f < 90:
            color = '#FF8C00'  # Dark Orange - Hot
            temp_category = "Hot"
        else:
            color = '#FF0000'  # Red - Very Hot
            temp_category = "Very Hot"
        
        # Create detailed popup with additional ASOS info if available
        popup_content = f"""
        <div style="font-family: Arial; min-width: 250px;">
        <b>{station['name']}</b><br>
        <b>State:</b> {station['state']}<br>
        """
        
        # Add station ID for ASOS stations
        if station.get('station_id'):
            popup_content += f"<b>Station ID:</b> {station['station_id']}<br>"
        
        popup_content += """<hr style="margin: 5px 0;">
        <b>🌡️ Temperature:</b> {:.1f}°F ({})<br>
        <b>🌀 Pressure:</b> {:.1f} hPa<br>
        """.format(temp_f, temp_category, station['pressure'])
        
        # Add wind information for ASOS stations
        if station.get('wind_direction') is not None and station.get('wind_speed') is not None:
            popup_content += f"<b>💨 Wind:</b> {station['wind_speed']:.1f} mph from {station['wind_direction']:.0f}°<br>"
        elif station.get('wind_speed') is not None:
            popup_content += f"<b>💨 Wind Speed:</b> {station['wind_speed']:.1f} mph<br>"
        
        # Add elevation for ASOS stations
        if station.get('elevation') is not None:
            popup_content += f"<b>⛰️ Elevation:</b> {station['elevation']:.0f} ft<br>"
        
        popup_content += """<hr style="margin: 5px 0;">
        <b>Source:</b> {}<br>
        """.format(station['source'])
        
        # Add timestamp for ASOS stations
        if station.get('timestamp') and station['timestamp'] != 'Unknown':
            popup_content += f"<b>Time:</b> {station['timestamp']}<br>"
        
        popup_content += "</div>"
        
        # Station marker with temperature color
        folium.CircleMarker(
            location=[station['lat'], station['lon']],
            radius=5,
            popup=popup_content,
            color='black',
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            tooltip=f"{station['name']}: {temp_f:.1f}°F ({temp_category})"
        ).add_to(m)
    
    # Add Rockville marker
    folium.Marker(
        location=rockville_center,
        popup="<b>Rockville, MD</b><br>Map Center",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)
    
    # Add comprehensive legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 320px; height: 380px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:11px; padding: 15px; border-radius: 10px;
                box-shadow: 3px 3px 10px rgba(0,0,0,0.3);">
    
    <h4 style="margin: 0 0 10px 0; color: #333;">Multi-Source Weather Map</h4>
    <p style="margin: 0 0 8px 0; font-weight: bold;">Centered on Rockville, MD</p>
    
    <hr style="margin: 8px 0;">
    
    <p style="margin: 5px 0; font-weight: bold;">🌡️ Temperature Colors:</p>
    <div style="line-height: 1.2; font-size: 10px;">
    <span style="color:#0000FF; font-weight: bold;">●</span> < 32°F (Freezing)<br>
    <span style="color:#4169E1; font-weight: bold;">●</span> 32-40°F (Very Cold)<br>
    <span style="color:#00BFFF; font-weight: bold;">●</span> 40-50°F (Cold)<br>
    <span style="color:#00FF7F; font-weight: bold;">●</span> 50-60°F (Cool)<br>
    <span style="color:#32CD32; font-weight: bold;">●</span> 60-70°F (Mild)<br>
    <span style="color:#FFD700; font-weight: bold;">●</span> 70-80°F (Warm)<br>
    <span style="color:#FF8C00; font-weight: bold;">●</span> 80-90°F (Hot)<br>
    <span style="color:#FF0000; font-weight: bold;">●</span> > 90°F (Very Hot)
    </div>
    
    <hr style="margin: 8px 0;">
    
    <p style="margin: 5px 0; font-weight: bold;">🌀 Pressure Contours:</p>
    <p style="margin: 2px 0; font-size: 10px;">Black lines at 2 hPa intervals</p>
    <p style="margin: 2px 0; font-size: 10px;">Numbers show pressure values</p>
    
    <hr style="margin: 8px 0;">
    
    <p style="margin: 2px 0; font-size: 10px;"><b>⭐ Red star:</b> Rockville, MD</p>
    <p style="margin: 2px 0; font-size: 9px; color: #666;">
    Data Sources: MD Mesonet, PA Keystone Mesonet, ASOS<br>
    Click on any station for detailed information
    </p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def find_column(df, possible_names):
    """Find the actual column name from a list of possible names"""
    for name in possible_names:
        if name in df.columns:
            return name
    return None

def load_maryland_data_from_file(csv_file):
    """Load Maryland data from fetched file"""
    try:
        import pandas as pd
        
        # Try different encodings in order of preference
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
        
        df = None
        for encoding in encodings_to_try:
            try:
                print(f"Trying to read Maryland CSV with {encoding} encoding...")
                df = pd.read_csv(csv_file, encoding=encoding)
                print(f"✓ Successfully read with {encoding} encoding")
                break
            except (UnicodeDecodeError, UnicodeError) as e:
                print(f"✗ Failed with {encoding}: {str(e)[:100]}...")
                continue
        
        if df is None:
            print("✗ Could not read CSV with any standard encoding")
            return []
        
        print(f"Maryland CSV loaded with {len(df)} records")
        print(f"Columns found: {list(df.columns)}")
        
        # Column detection
        name_col = find_column(df, ['public_name', 'name', 'station_name', 'site_name'])
        temp_col = find_column(df, ['Air_Temperature_2m_Avg', 't', 'temp', 'temperature', 'air_temp'])
        pressure_col = find_column(df, ['MSLP_Avg', 'mslp', 'pressure', 'slp', 'press'])
        
        # Coordinate columns
        lat_col = find_column(df, ['latitude', 'lat', 'y'])
        lon_col = find_column(df, ['longitude', 'lon', 'lng', 'x'])
        
        if not name_col or not temp_col or not pressure_col:
            print(f"Could not find required columns in Maryland data")
            print(f"Available columns: {list(df.columns)}")
            return []
        
        print(f"Column mapping:")
        print(f"  Name: {name_col}")
        print(f"  Temperature: {temp_col}")
        print(f"  Pressure: {pressure_col}")
        print(f"  Latitude: {lat_col}")
        print(f"  Longitude: {lon_col}")
        
        weather_stations = []
        
        for idx, row in df.iterrows():
            try:
                station_name = row[name_col]
                
                # Get temperature (convert from Celsius to Fahrenheit if needed)
                temp_c = row[temp_col]
                if pd.notna(temp_c):
                    # Assume Celsius if temperature is reasonable (< 50)
                    if temp_c < 50:
                        temp_f = (temp_c * 9/5) + 32
                    else:
                        temp_f = temp_c  # Already in Fahrenheit
                else:
                    temp_f = 70.0  # Default
                
                # Get pressure
                pressure = row[pressure_col] if pd.notna(row[pressure_col]) else 1013.25
                
                # Get coordinates
                if lat_col and lon_col and pd.notna(row[lat_col]) and pd.notna(row[lon_col]):
                    lat = float(row[lat_col])
                    lon = float(row[lon_col])
                else:
                    # Use lookup coordinates
                    lat, lon = get_maryland_coordinates(station_name)
                
                weather_stations.append({
                    'name': station_name,
                    'lat': lat,
                    'lon': lon,
                    'temp_f': round(temp_f, 1),
                    'pressure': float(pressure),
                    'state': 'MD',
                    'source': 'Maryland Mesonet'
                })
                
            except Exception as e:
                print(f"Error processing station {idx}: {e}")
                continue
        
        print(f"✓ Successfully loaded {len(weather_stations)} Maryland weather stations")
        return weather_stations
        
    except Exception as e:
        print(f"Error loading Maryland data: {e}")
        import traceback
        traceback.print_exc()
        return []

def load_pennsylvania_data_from_file(data_file):
    """Load Pennsylvania data from fetched CSV file"""
    try:
        import pandas as pd
        
        weather_stations = []
        
        # Try different encodings for the CSV
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        df = None
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(data_file, encoding=encoding)
                print(f"✓ Successfully read PA CSV with {encoding} encoding")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if df is None:
            print("✗ Could not read Pennsylvania CSV with any encoding")
            return []
        
        print(f"Pennsylvania CSV loaded with {len(df)} records")
        print(f"Available columns: {list(df.columns)}")
        
        # Look for common column names in Pennsylvania mesonet data
        name_col = find_column(df, ['name', 'station_name', 'site_name', 'public_name', 'stid', 'station'])
        lat_col = find_column(df, ['latitude', 'lat', 'y', 'the_geom_y'])
        lon_col = find_column(df, ['longitude', 'lon', 'long', 'x', 'the_geom_x'])
        
        # Temperature could be in various units and names
        temp_col = find_column(df, ['t', 'temp', 'temperature', 'air_temp', 'temp_c', 'temp_f', 'air_temperature'])
        
        # Pressure columns
        pressure_col = find_column(df, ['mslp', 'pressure', 'slp', 'press', 'sea_level_pressure', 'pres'])
        
        print(f"Column mapping:")
        print(f"  Name: {name_col}")
        print(f"  Latitude: {lat_col}")
        print(f"  Longitude: {lon_col}")
        print(f"  Temperature: {temp_col}")
        print(f"  Pressure: {pressure_col}")
        
        if not all([lat_col, lon_col]):
            print(f"✗ Could not find required location columns in Pennsylvania data")
            print(f"Available columns: {list(df.columns)}")
            return []
        
        if not temp_col and not pressure_col:
            print(f"✗ Could not find any weather data columns in Pennsylvania data")
            return []
        
        for idx, row in df.iterrows():
            try:
                # Get station name
                station_name = f"PA Station {idx+1}"
                if name_col:
                    station_name = str(row[name_col])
                
                # Get coordinates
                lat = float(row[lat_col])
                lon = float(row[lon_col])
                
                # Get temperature (handle different units)
                temp_f = None
                if temp_col and pd.notna(row[temp_col]):
                    temp_value = float(row[temp_col])
                    # If temperature is likely in Celsius (< 40), convert to Fahrenheit
                    if temp_value < 40:
                        temp_f = (temp_value * 9/5) + 32
                    else:
                        temp_f = temp_value
                
                # Get pressure
                pressure = None
                if pressure_col and pd.notna(row[pressure_col]):
                    pressure = float(row[pressure_col])
                
                # Only add stations with valid coordinates and at least one weather parameter
                if lat and lon and (temp_f is not None or pressure is not None):
                    weather_stations.append({
                        'name': station_name,
                        'lat': lat,
                        'lon': lon,
                        'temp_f': temp_f if temp_f is not None else 50.0,  # Default temp if missing
                        'pressure': pressure if pressure is not None else 1013.25,  # Default pressure if missing
                        'state': 'PA',
                        'source': 'Pennsylvania Keystone Mesonet'
                    })
                    
            except Exception as e:
                print(f"Error processing PA station {idx}: {e}")
                continue
        
        print(f"✓ Successfully loaded {len(weather_stations)} Pennsylvania weather stations")
        return weather_stations
        
    except Exception as e:
        print(f"Error loading Pennsylvania data: {e}")
        import traceback
        traceback.print_exc()
        return []

def convert_asos_to_weather_data(asos_data):
    """
    Convert ASOS data format to the standard weather data format used by the mapping system
    """
    weather_stations = []
    
    for station in asos_data:
        try:
            # Convert ASOS format to standard format
            weather_station = {
                'name': station['name'],
                'lat': station['lat'],
                'lon': station['lon'],
                'temp_f': station['temp_f'],
                'pressure': station['pressure'],
                'state': station['state'],
                'source': station['source'],
                # Additional ASOS-specific data
                'station_id': station.get('station_id', ''),
                'wind_direction': station.get('wind_direction'),
                'wind_speed': station.get('wind_speed'),
                'elevation': station.get('elevation'),
                'timestamp': station.get('timestamp', '')
            }
            weather_stations.append(weather_station)
            
        except Exception as e:
            print(f"Error converting ASOS station data: {e}")
            continue
    
    return weather_stations

def convert_mesonet_to_weather_data(mesonet_df):
    """
    Convert mesonet DataFrame format to the standard weather data format used by the mapping system
    """
    weather_stations = []
    
    if mesonet_df.empty:
        return weather_stations
    
    for idx, row in mesonet_df.iterrows():
        try:
            # Convert mesonet DataFrame format to standard format
            weather_station = {
                'name': row.get('public_name', 'Unknown Station'),
                'lat': row.get('latitude', 0.0),
                'lon': row.get('longitude', 0.0),
                'temp_f': row.get('Air_Temperature_2m_Avg', 70.0),
                'pressure': row.get('MSLP_Avg', 1013.25),
                'state': 'MD' if 'MD ASOS' in str(row.get('public_name', '')) else ('VA' if 'VA ASOS' in str(row.get('public_name', '')) else 'PA'),
                'source': 'Iowa Environmental Mesonet',
                # Additional mesonet-specific data
                'station_id': row.get('station_id', ''),
                'wind_direction': row.get('WindDirection_10m_Avg'),
                'wind_speed': row.get('WindSpeed_10m_Avg'),
                'humidity': row.get('RelativeHumidity_2m_Avg'),
                'city': row.get('city', ''),
                'timestamp': row.get('timestamp', '')
            }
            weather_stations.append(weather_station)
            
        except Exception as e:
            print(f"Error converting mesonet station data: {e}")
            continue
    
    return weather_stations

def get_maryland_coordinates(station_name):
    """Get coordinates for Maryland stations using official locations"""
    maryland_locations = {
        'Baltimore': (39.3352, -76.5909),
        'Berlin': (38.3372, -75.1926),
        'Bittinger': (39.5678, -79.2367),
        'Cambridge': (38.5875, -76.1415),
        'Chesapeake City': (39.5076, -75.8332),
        'Chestertown': (39.2313, -76.0629),
        'Clarksville': (39.2625, -76.9258),
        'Clear Spring': (39.6978, -77.9385),
        'College Park': (39.01, -76.9411),
        'Easton': (38.7436, -76.0118),
        'Federalsburg': (38.695, -75.7829),
        'Ferry Cove': (38.7661, -76.3251),
        'Frostburg': (39.6755, -78.9334),
        'Galena': (39.3427, -75.8728),
        'Goldsboro': (39.0404, -75.7887),
        'Harney': (39.7164, -77.2087),
        'Keedysville': (39.5097, -77.7762),
        'Layhill': (39.0986, -77.0331),
        'Linkwood': (38.5382, -75.9448),
        'Nanjemoy': (38.461, -77.216),
        'Parkton': (39.6452, -76.703),
        'Poolesville': (39.1316, -77.4852),
        'Princess Anne': (38.1778, -75.6992),
        'Quantico': (38.3587, -75.7741),
        'Ridgely': (38.9535, -75.883),
        'Salisbury': (38.3415, -75.6037),
        'Stevensville': (38.9843, -76.3263),
        'Sykesville': (39.3845, -76.9613),
        'Thurmont': (39.6358, -77.4011),
        'Towson': (39.3947, -76.6234),
        'Upper Marlboro': (38.8624, -76.7767),
        'Waldorf': (38.5971, -76.8431),
        'Westminster': (39.5341, -76.9935),
        'Wye Mills': (38.9183, -76.1453)
    }
    
    return maryland_locations.get(station_name, (39.0, -77.0))  # Default to central MD

if __name__ == "__main__":
    main()