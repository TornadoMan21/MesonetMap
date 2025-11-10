from flask import Flask, render_template, send_file, jsonify
import os
import threading
import schedule
import time
from datetime import datetime
from src.main import main as generate_weather_map

app = Flask(__name__)

# Ensure maps directory exists
MAPS_DIR = "maps"
if not os.path.exists(MAPS_DIR):
    os.makedirs(MAPS_DIR)

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
    print(f"Generating weather map at {datetime.now()}")
    try:
        generate_weather_map()
        print("Weather map generated successfully")
    except Exception as e:
        print(f"Error generating weather map: {e}")

# Schedule map updates every 2 hours
schedule.every(2).hours.do(generate_map_wrapper)

if __name__ == '__main__':
    # Generate initial map
    print("Generating initial weather map...")
    try:
        generate_weather_map()
    except Exception as e:
        print(f"Warning: Could not generate initial map: {e}")
    
    # Start background scheduler
    threading.Thread(target=update_maps_scheduled, daemon=True).start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)