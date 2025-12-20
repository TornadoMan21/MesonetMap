from flask import Flask, render_template, send_file, jsonify
import os
import threading
import schedule
import time
from datetime import datetime

app = Flask(__name__)

# Get port from environment variable (Render.com requirement)
PORT = int(os.environ.get('PORT', 5000))

# Ensure maps directory exists
MAPS_DIR = "maps"
if not os.path.exists(MAPS_DIR):
    os.makedirs(MAPS_DIR)

def generate_weather_map():
    """Generate weather map without user interaction - Memory optimized"""
    import sys
    import gc  # Garbage collection for memory optimization
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import and run the weather mapping function
    from src.data.mesonet_fetcher import fetch_all_mesonet_data
    from src.main import create_combined_weather_map_centered_rockville, convert_mesonet_to_weather_data, convert_asos_to_weather_data
    import pandas as pd
    
    try:
        print(f"Generating weather map at {datetime.now()}")
        
        # Fetch data from all sources (already optimized for memory)
        md_data, pa_file, va_data, ny_data, asos_data = fetch_all_mesonet_data()
        
        # Process Maryland data
        maryland_data = []
        if hasattr(md_data, 'empty') and not md_data.empty:
            maryland_data = convert_mesonet_to_weather_data(md_data)
        del md_data  # Free memory immediately
        gc.collect()
        
        # Process Pennsylvania data  
        pennsylvania_data = []
        if pa_file and os.path.exists(pa_file):
            import pandas as pd
            pa_df = pd.read_csv(pa_file, encoding='utf-8')
            # Convert PA data to weather format (limit to first 20 for memory)
            for i, (_, row) in enumerate(pa_df.iterrows()):
                if i >= 20:  # Limit to 20 stations for memory optimization
                    break
                if pd.notna(row.get('t')) and pd.notna(row.get('mslp')):
                    try:
                        pennsylvania_data.append({
                            'name': row.get('name', 'Unknown'),
                            'lat': float(row.get('latitude')),
                            'lon': float(row.get('longitude')),
                            'temp_f': float(row.get('t')),
                            'pressure': float(row.get('mslp')),
                            'source': 'PA Keystone'
                        })
                    except (ValueError, TypeError):
                        continue
            del pa_df  # Free pandas dataframe memory
            gc.collect()
        
        # Process Virginia data
        virginia_data = []
        if hasattr(va_data, 'empty') and not va_data.empty:
            virginia_data = convert_mesonet_to_weather_data(va_data)
        del va_data  # Free memory
        gc.collect()
        
        # Process New York data
        newyork_data = []
        if hasattr(ny_data, 'empty') and not ny_data.empty:
            newyork_data = convert_mesonet_to_weather_data(ny_data)
        del ny_data  # Free memory
        gc.collect()
        
        # Process ASOS data (limited for memory)
        asos_stations = []
        if asos_data:
            # Limit ASOS data for memory optimization
            limited_asos = asos_data[:15] if len(asos_data) > 15 else asos_data
            asos_stations = convert_asos_to_weather_data(limited_asos)
        del asos_data  # Free memory
        gc.collect()
        
        # Combine all data with deduplication
        combined_data = maryland_data + pennsylvania_data + virginia_data + newyork_data + asos_stations
        
        # Free individual data arrays
        del maryland_data, pennsylvania_data, virginia_data, newyork_data, asos_stations
        gc.collect()
        
        all_weather_data = []
        seen_locations = set()
        
        for station in combined_data:
            lat_key = round(station['lat'], 2)
            lon_key = round(station['lon'], 2)
            location_key = (lat_key, lon_key)
            
            if location_key not in seen_locations:
                seen_locations.add(location_key)
                all_weather_data.append(station)
        
        del combined_data, seen_locations  # Free memory
        gc.collect()
        
        print(f"Processing {len(all_weather_data)} unique weather stations")
        
        # Create the map
        if all_weather_data:
            combined_map = create_combined_weather_map_centered_rockville(all_weather_data)
            if combined_map:
                map_file = os.path.join(MAPS_DIR, "mesonet_combined_weather_map.html")
                combined_map.save(map_file)
                print(f"Weather map saved to: {map_file}")
                return True
        
        print("No weather data available")
        return False
        
    except Exception as e:
        print(f"Error generating weather map: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')
def index():
    """Serve the main weather map page"""
    return render_template('index.html')

@app.route('/map')
def serve_map():
    """Serve the latest weather map"""
    map_file = os.path.join(MAPS_DIR, "mesonet_combined_weather_map.html")
    if os.path.exists(map_file):
        return send_file(map_file)
    else:
        return "Weather map not available. Please wait for generation.", 503

@app.route('/api/status')
def api_status():
    """API endpoint to check map status"""
    map_file = os.path.join(MAPS_DIR, "mesonet_combined_weather_map.html")
    if os.path.exists(map_file):
        modified_time = os.path.getmtime(map_file)
        return jsonify({
            "status": "available",
            "last_updated": datetime.fromtimestamp(modified_time).isoformat(),
            "file_exists": True
        })
    else:
        return jsonify({
            "status": "generating",
            "last_updated": None,
            "file_exists": False
        })

@app.route('/api/update')
def api_update():
    """Manually trigger map update"""
    try:
        # Run map generation in background
        threading.Thread(target=generate_weather_map, daemon=True).start()
        return jsonify({"status": "update_started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def update_maps_scheduled():
    """Background task to update maps every hour"""
    while True:
        schedule.run_pending()
        time.sleep(60)

def generate_map_wrapper():
    """Wrapper function for scheduled map generation"""
    generate_weather_map()

if __name__ == '__main__':
    # Generate initial map
    print("Generating initial weather map...")
    generate_weather_map()
    
    # Schedule map updates every 2 hours
    schedule.every(2).hours.do(generate_map_wrapper)
    
    # Start background scheduler
    def update_maps_scheduled():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    threading.Thread(target=update_maps_scheduled, daemon=True).start()
    
    # Run Flask app
    print(f"Starting Flask app on port {PORT}")
    print(f"Visit: http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)