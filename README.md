# Live Weather Mapping Web Application

A real-time weather mapping system that displays live weather data from Maryland, Pennsylvania, and Virginia using multiple data sources including ASOS stations and mesonet networks.

## 🌟 Features

- 🌡️ **Real-time temperature data** with color-coded station markers
- 🌀 **Pressure contour lines** at 2 hPa intervals  
- 📍 **169 weather stations** across MD, PA, and VA
- 🔄 **Automatic map updates** every 2 hours
- 🌐 **Web interface** with manual update capability
- 📱 **Responsive design** for mobile and desktop

## 📊 Data Sources

- **Maryland**: ASOS stations via Iowa Environmental Mesonet API
- **Pennsylvania**: Keystone Mesonet via Penn State WFS API  
- **Virginia**: ASOS stations via Iowa Environmental Mesonet API
- **Additional**: Local ASOS station data from CSV

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the web application:**
```bash
python app.py
```

3. **Open your browser** to `http://localhost:5000`

### Generate Maps Only
```bash
python src/main.py
```

## 🌐 Deployment

This application is ready to deploy on:
- **Render** (recommended)
- Heroku
- Railway
- Any platform supporting Python Flask apps

### Deploy to Render:
1. Push code to GitHub
2. Connect GitHub repo to Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app.py`

## 📁 Project Structure

```
weather-mapping-project/
├── app.py                       # Flask web server
├── src/
│   ├── main.py                  # Weather map generator
│   ├── data/
│   │   ├── mesonet_fetcher.py   # Data fetching from multiple sources
│   │   └── asos.csv             # Local ASOS station data
│   ├── weather_maps/            # Map generation modules
│   ├── utils/                   # Utility functions
│   └── config/                  # Configuration settings
├── templates/
│   └── index.html              # Web interface
├── maps/                       # Generated map files
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Technical Details

- **Backend**: Python Flask with background scheduling
- **Maps**: Folium for interactive maps, Matplotlib for contours
- **Data Processing**: Pandas, NumPy, SciPy for interpolation
- **APIs**: Iowa Environmental Mesonet, Penn State WFS
- **Features**: Automatic deduplication, error handling, responsive UI

## 📱 API Endpoints

- `GET /` - Main web interface
- `GET /map` - Serve latest weather map
- `GET /api/status` - Check map generation status
- `GET /api/update` - Trigger manual map update

## 🤝 Contributing

Contributions welcome! Please feel free to submit pull requests or open issues.

## 📄 License

MIT License - feel free to use and modify as needed.