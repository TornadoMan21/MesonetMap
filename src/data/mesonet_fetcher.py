import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from urllib.parse import urlencode
import time
import re
import random

class MarylandMesonetFetcher:
    """Fetch data from Maryland ASOS stations via Iowa Environmental Mesonet API"""
    
    def __init__(self):
        self.base_url = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
        self.session = requests.Session()
        # Set a proper user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Maryland ASOS station list (major airports and frequently reporting stations)
        self.md_stations = [
            'BWI',  # Baltimore-Washington International (primary airport)
            'DCA',  # Ronald Reagan Washington National Airport
            'IAD',  # Washington Dulles International Airport
            'ADW',  # Andrews Air Force Base
            'HGR',  # Hagerstown Regional Airport
            'SBY',  # Salisbury-Ocean City Wicomico Regional Airport
            'APG',  # Aberdeen Proving Ground
            'FDK',  # Frederick Municipal Airport
            'GAI',  # Montgomery County Airpark
            'MTN',  # Martin State Airport
            'ESN'   # Easton/Newnam Field Airport
        ]
    
    def fetch_current_data(self, hours_back=1):
        """
        Fetch current Maryland ASOS data from Iowa Environmental Mesonet API
        """
        try:
            print("Fetching live Maryland ASOS data from Iowa Environmental Mesonet...")
            
            # Get current date for the API request
            from datetime import datetime, timedelta
            now = datetime.now()
            
            # Parameters for the Iowa Environmental Mesonet ASOS API
            params = {
                'network': 'MD_ASOS',
                'data': 'all',
                'year1': now.year,
                'month1': now.month,
                'day1': now.day,
                'year2': now.year,
                'month2': now.month,
                'day2': now.day,
                'tz': 'Etc/UTC',
                'format': 'onlycomma',
                'latlon': 'yes',
                'elev': 'no',
                'missing': 'M',
                'trace': 'T',
                'direct': 'no',
                'report_type': ['3', '4']  # METAR and SPECI reports
            }
            
            # Add all Maryland stations to the request
            for station in self.md_stations:
                params[f'station'] = station
            
            print(f"Requesting data from: {self.base_url}")
            print(f"Date: {now.year}-{now.month:02d}-{now.day:02d}")
            print(f"Stations: {', '.join(self.md_stations)}")
            
            # Make the request
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            print(f"✓ Response received - Status: {response.status_code}")
            print(f"✓ Content type: {response.headers.get('content-type', 'unknown')}")
            print(f"✓ Content length: {len(response.content)} bytes")
            
            # Save the response as CSV
            temp_file = "temp_maryland_asos_data.csv"
            with open(temp_file, 'w', encoding='utf-8', newline='') as f:
                f.write(response.text)
            
            print(f"✓ Maryland ASOS data saved to: {temp_file}")
            
            # Verify the data by reading a few lines
            try:
                df = pd.read_csv(temp_file)
                print(f"✓ Successfully parsed CSV with {len(df)} records")
                print(f"✓ Columns: {list(df.columns)}")
                if len(df) > 0:
                    print("✓ Sample data (first 2 rows):")
                    print(df.head(2))
                    
                    # Process the data to standardize format
                    processed_df = self._process_iowa_mesonet_data(df)
                    
                    # Save processed data
                    processed_file = "temp_maryland_data.csv"
                    processed_df.to_csv(processed_file, index=False, encoding='utf-8')
                    
                    print(f"✓ Processed {len(processed_df)} Maryland ASOS stations")
                    return processed_file
                    
            except Exception as e:
                print(f"⚠ Warning: Could not parse CSV immediately: {e}")
                # Show raw content preview
                with open(temp_file, 'r') as f:
                    preview = f.read()[:500]
                print(f"Raw content preview:\n{preview}")
                return temp_file
            
            return temp_file
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Network error fetching Maryland ASOS data: {e}")
            print("Falling back to sample data...")
            return self._generate_sample_data()
        except Exception as e:
            print(f"✗ Error fetching Maryland ASOS data: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to sample data...")
            return self._generate_sample_data()
    
    def _process_iowa_mesonet_data(self, df):
        """
        Process Iowa Environmental Mesonet ASOS data format
        Expected columns: station, valid, lon, lat, tmpf, dwpf, relh, drct, sknt, p01i, alti, mslp, gust, skyc1, skyc2, skyc3, skyc4, skyl1, skyl2, skyl3, skyl4, wxcodes, ice_accretion_1hr, ice_accretion_3hr, ice_accretion_6hr, peak_wind_gust, peak_wind_drct, peak_wind_time, feel, metar
        """
        try:
            print("Processing Iowa Environmental Mesonet ASOS data structure...")
            
            if len(df) == 0:
                print("✗ No data in DataFrame")
                return pd.DataFrame()
            
            print(f"Available columns: {list(df.columns)}")
            
            # Get unique stations (keep most recent reading per station)
            if 'valid' in df.columns:
                # Sort by time and keep last reading per station
                df_sorted = df.sort_values(['station', 'valid'])
                unique_stations = df_sorted.drop_duplicates(subset=['station'], keep='last')
            else:
                unique_stations = df.drop_duplicates(subset=['station'], keep='last')
            
            print(f"Processing {len(unique_stations)} unique Maryland ASOS stations...")
            
            processed_stations = []
            
            for idx, row in unique_stations.iterrows():
                try:
                    station_id = str(row['station'])
                    
                    # Coordinates
                    if 'lat' in df.columns and 'lon' in df.columns:
                        latitude = float(row['lat']) if pd.notna(row['lat']) else None
                        longitude = float(row['lon']) if pd.notna(row['lon']) else None
                    else:
                        latitude, longitude = self._get_station_coordinates(station_id)
                    
                    if not latitude or not longitude:
                        continue  # Skip stations without coordinates
                    
                    # Temperature (tmpf - already in Fahrenheit)
                    temp_f = 70.0  # Default
                    if 'tmpf' in df.columns and pd.notna(row['tmpf']) and row['tmpf'] != 'M':
                        try:
                            temp_f = float(row['tmpf'])
                        except (ValueError, TypeError):
                            temp_f = 70.0
                    
                    # Pressure (mslp - mean sea level pressure)
                    pressure = 1013.25  # Default
                    if 'mslp' in df.columns and pd.notna(row['mslp']) and row['mslp'] != 'M':
                        try:
                            pressure = float(row['mslp'])
                        except (ValueError, TypeError):
                            pressure = 1013.25
                    elif 'alti' in df.columns and pd.notna(row['alti']) and row['alti'] != 'M':
                        # Convert altimeter setting to approximate sea level pressure
                        try:
                            alti_inches = float(row['alti'])
                            pressure = alti_inches * 33.863886  # Convert inches Hg to hPa
                        except (ValueError, TypeError):
                            pressure = 1013.25
                    
                    # Wind data
                    wind_direction = None
                    if 'drct' in df.columns and pd.notna(row['drct']) and row['drct'] != 'M':
                        try:
                            wind_direction = float(row['drct'])
                        except (ValueError, TypeError):
                            wind_direction = None
                    
                    wind_speed = None
                    if 'sknt' in df.columns and pd.notna(row['sknt']) and row['sknt'] != 'M':
                        try:
                            wind_speed_kts = float(row['sknt'])
                            wind_speed = wind_speed_kts * 1.15078  # Convert knots to mph
                        except (ValueError, TypeError):
                            wind_speed = None
                    
                    # Humidity
                    humidity = None
                    if 'relh' in df.columns and pd.notna(row['relh']) and row['relh'] != 'M':
                        try:
                            humidity = float(row['relh'])
                        except (ValueError, TypeError):
                            humidity = None
                    
                    station_data = {
                        'public_name': f"MD ASOS {station_id}",
                        'station_id': station_id,
                        'Air_Temperature_2m_Avg': temp_f,  # Already in Fahrenheit
                        'MSLP_Avg': pressure,
                        'RelativeHumidity_2m_Avg': humidity if humidity is not None else 65.0,
                        'WindSpeed_10m_Avg': wind_speed if wind_speed is not None else 5.0,
                        'WindDirection_10m_Avg': wind_direction if wind_direction is not None else 270.0,
                        'latitude': latitude,
                        'longitude': longitude,
                        'city': f"MD-{station_id}",
                        'timestamp': row.get('valid', 'Unknown')
                    }
                    
                    processed_stations.append(station_data)
                    
                except Exception as e:
                    print(f"Error processing station {idx}: {e}")
                    continue
            
            processed_df = pd.DataFrame(processed_stations)
            print(f"✓ Successfully processed {len(processed_df)} Maryland ASOS stations")
            return processed_df
            
        except Exception as e:
            print(f"Error processing Iowa Mesonet data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _get_station_coordinates(self, station_id):
        """
        Get coordinates for Maryland ASOS stations
        """
        # Maryland ASOS station coordinates (major airports and weather stations)
        md_asos_coords = {
            'BWI': (39.1754, -76.6683),  # Baltimore-Washington International
            'DCA': (38.8512, -77.0402),  # Ronald Reagan Washington National
            'IAD': (38.9531, -77.4565),  # Washington Dulles International
            'ADW': (38.8108, -76.8669),  # Andrews Air Force Base
            'HGR': (39.7078, -77.7297),  # Hagerstown Regional Airport
            'SBY': (38.3408, -75.5100),  # Salisbury-Ocean City Wicomico Regional
            'APG': (39.4669, -76.1686),  # Aberdeen Proving Ground
            'FDK': (39.4175, -77.3739),  # Frederick Municipal Airport
            'GAI': (39.1683, -77.1661),  # Montgomery County Airpark
            'MTN': (39.3250, -76.4147),  # Martin State Airport (corrected coordinates)
            'ESN': (38.8042, -76.0467)   # Easton/Newnam Field Airport
        }
        
        coords = md_asos_coords.get(station_id)
        if coords:
            return coords
        else:
            # Default to central Maryland
            print(f"Warning: No coordinates found for station {station_id}")
            return (39.0, -77.0)

    def _process_maryland_data(self, df):
        """
        Process the Maryland data to standardize column names and add missing fields
        """
        try:
            print("Processing Maryland data structure...")
            
            # Create a copy to avoid modifying original
            processed_df = df.copy()
            
            # Map common column variations to standard names
            column_mapping = {
                # Station identification
                'public_name': 'public_name',
                'station_name': 'public_name', 
                'name': 'public_name',
                'site_name': 'public_name',
                
                # Temperature (usually in Celsius)
                'Air_Temperature_2m_Avg': 'Air_Temperature_2m_Avg',
                'temp': 'Air_Temperature_2m_Avg',
                'temperature': 'Air_Temperature_2m_Avg',
                'air_temp': 'Air_Temperature_2m_Avg',
                't_avg': 'Air_Temperature_2m_Avg',
                
                # Pressure
                'MSLP_Avg': 'MSLP_Avg',
                'mslp': 'MSLP_Avg',
                'pressure': 'MSLP_Avg',
                'sea_level_pressure': 'MSLP_Avg',
                'slp': 'MSLP_Avg',
                
                # Humidity
                'RelativeHumidity_2m_Avg': 'RelativeHumidity_2m_Avg',
                'humidity': 'RelativeHumidity_2m_Avg',
                'rh': 'RelativeHumidity_2m_Avg',
                'relative_humidity': 'RelativeHumidity_2m_Avg',
                
                # Wind Speed
                'WindSpeed_10m_Avg': 'WindSpeed_10m_Avg',
                'wind_speed': 'WindSpeed_10m_Avg',
                'ws': 'WindSpeed_10m_Avg',
                'wspd_avg': 'WindSpeed_10m_Avg',
                
                # Wind Direction
                'WindDirection_10m_Avg': 'WindDirection_10m_Avg',
                'wind_direction': 'WindDirection_10m_Avg',
                'wd': 'WindDirection_10m_Avg',
                'wdir_avg': 'WindDirection_10m_Avg',
                
                # Coordinates
                'latitude': 'latitude',
                'lat': 'latitude',
                'y': 'latitude',
                'longitude': 'longitude', 
                'lon': 'longitude',
                'lng': 'longitude',
                'x': 'longitude'
            }
            
            # Rename columns based on mapping
            for old_name, new_name in column_mapping.items():
                if old_name in processed_df.columns:
                    if new_name not in processed_df.columns:
                        processed_df = processed_df.rename(columns={old_name: new_name})
                        print(f"  Mapped '{old_name}' -> '{new_name}'")
            
            # Get Maryland station coordinates (in case they're not in the file)
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
                'Keedysville': (39.5097, -77.7262),
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
            
            # Add coordinates if missing
            if 'latitude' not in processed_df.columns or 'longitude' not in processed_df.columns:
                print("  Adding coordinates from station lookup...")
                if 'public_name' in processed_df.columns:
                    processed_df['latitude'] = processed_df['public_name'].apply(
                        lambda x: maryland_locations.get(x, (39.0, -77.0))[0]
                    )
                    processed_df['longitude'] = processed_df['public_name'].apply(
                        lambda x: maryland_locations.get(x, (39.0, -77.0))[1]
                    )
            
            # Add city names if missing
            if 'city' not in processed_df.columns:
                processed_df['city'] = processed_df.get('public_name', 'Unknown')
            
            # Add timestamp if missing
            if 'timestamp' not in processed_df.columns:
                processed_df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:00:00')
            
            # Fill missing wind data with reasonable defaults if not present
            if 'WindSpeed_10m_Avg' not in processed_df.columns:
                print("  Adding default wind speed data...")
                processed_df['WindSpeed_10m_Avg'] = [random.uniform(2, 15) for _ in range(len(processed_df))]
            
            if 'WindDirection_10m_Avg' not in processed_df.columns:
                print("  Adding default wind direction data...")
                processed_df['WindDirection_10m_Avg'] = [random.uniform(0, 360) for _ in range(len(processed_df))]
            
            # Ensure required columns exist with defaults
            required_columns = {
                'public_name': 'Unknown Station',
                'Air_Temperature_2m_Avg': 10.0,  # Default temp in Celsius
                'MSLP_Avg': 1013.25,  # Default pressure
                'RelativeHumidity_2m_Avg': 65.0,  # Default humidity
                'WindSpeed_10m_Avg': 5.0,  # Default wind speed
                'WindDirection_10m_Avg': 270.0,  # Default wind direction (west)
                'latitude': 39.0,
                'longitude': -77.0,
                'city': 'Unknown',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:00:00')
            }
            
            for col, default_val in required_columns.items():
                if col not in processed_df.columns:
                    print(f"  Adding missing column '{col}' with default values")
                    processed_df[col] = default_val
                else:
                    # Fill NaN values with defaults
                    processed_df[col] = processed_df[col].fillna(default_val)
            
            print(f"✓ Processed data structure:")
            print(f"  - Stations: {len(processed_df)}")
            print(f"  - Columns: {list(processed_df.columns)}")
            print(f"  - Wind data included: {'WindSpeed_10m_Avg' in processed_df.columns and 'WindDirection_10m_Avg' in processed_df.columns}")
            
            return processed_df
            
        except Exception as e:
            print(f"Error processing Maryland data: {e}")
            import traceback
            traceback.print_exc()
            return df  # Return original if processing fails
    
    def _generate_sample_data(self):
        """
        Fallback: Generate sample Maryland mesonet data with wind data
        """
        try:
            print("Generating sample Maryland data as fallback...")
            
            # Maryland stations with coordinates from station location.csv
            maryland_stations = [
                {'name': 'Baltimore', 'lat': 39.3352, 'lon': -76.5909, 'city': 'Baltimore'},
                {'name': 'Berlin', 'lat': 38.3372, 'lon': -75.1926, 'city': 'Berlin'},
                {'name': 'Bittinger', 'lat': 39.5678, 'lon': -79.2367, 'city': 'Bittinger'},
                {'name': 'Cambridge', 'lat': 38.5875, 'lon': -76.1415, 'city': 'Cambridge'},
                {'name': 'Chesapeake City', 'lat': 39.5076, 'lon': -75.8332, 'city': 'Chesapeake City'},
                {'name': 'Chestertown', 'lat': 39.2313, 'lon': -76.0629, 'city': 'Chestertown'},
                {'name': 'Clarksville', 'lat': 39.2625, 'lon': -76.9258, 'city': 'Clarksville'},
                {'name': 'Clear Spring', 'lat': 39.6978, 'lon': -77.9385, 'city': 'Clear Spring'},
                {'name': 'College Park', 'lat': 39.01, 'lon': -76.9411, 'city': 'College Park'},
                {'name': 'Easton', 'lat': 38.7436, 'lon': -76.0118, 'city': 'Easton'},
                {'name': 'Federalsburg', 'lat': 38.695, 'lon': -75.7829, 'city': 'Federalsburg'},
                {'name': 'Ferry Cove', 'lat': 38.7661, 'lon': -76.3251, 'city': 'Ferry Cove'},
                {'name': 'Frostburg', 'lat': 39.6755, 'lon': -78.9334, 'city': 'Frostburg'},
                {'name': 'Galena', 'lat': 39.3427, 'lon': -75.8728, 'city': 'Galena'},
                {'name': 'Goldsboro', 'lat': 39.0404, 'lon': -75.7887, 'city': 'Goldsboro'},
                {'name': 'Harney', 'lat': 39.7164, 'lon': -77.2087, 'city': 'Harney'},
                {'name': 'Keedysville', 'lat': 39.5097, 'lon': -77.7262, 'city': 'Keedysville'},
                {'name': 'Layhill', 'lat': 39.0986, 'lon': -77.0331, 'city': 'Layhill'},
                {'name': 'Linkwood', 'lat': 38.5382, 'lon': -75.9448, 'city': 'Linkwood'},
                {'name': 'Nanjemoy', 'lat': 38.461, 'lon': -77.216, 'city': 'Nanjemoy'},
                {'name': 'Parkton', 'lat': 39.6452, 'lon': -76.703, 'city': 'Parkton'},
                {'name': 'Poolesville', 'lat': 39.1316, 'lon': -77.4852, 'city': 'Poolesville'},
                {'name': 'Princess Anne', 'lat': 38.1778, 'lon': -75.6992, 'city': 'Princess Anne'},
                {'name': 'Quantico', 'lat': 38.3587, 'lon': -75.7741, 'city': 'Quantico'},
                {'name': 'Ridgely', 'lat': 38.9535, 'lon': -75.883, 'city': 'Ridgely'},
                {'name': 'Salisbury', 'lat': 38.3415, 'lon': -75.6037, 'city': 'Salisbury'},
                {'name': 'Stevensville', 'lat': 38.9843, 'lon': -76.3263, 'city': 'Stevensville'},
                {'name': 'Sykesville', 'lat': 39.3845, 'lon': -76.9613, 'city': 'Sykesville'},
                {'name': 'Thurmont', 'lat': 39.6358, 'lon': -77.4011, 'city': 'Thurmont'},
                {'name': 'Towson', 'lat': 39.3947, 'lon': -76.6234, 'city': 'Towson'},
                {'name': 'Upper Marlboro', 'lat': 38.8624, 'lon': -76.7767, 'city': 'Upper Marlboro'},
                {'name': 'Waldorf', 'lat': 38.5971, 'lon': -76.8431, 'city': 'Waldorf'},
                {'name': 'Westminster', 'lat': 39.5341, 'lon': -76.9935, 'city': 'Westminster'},
                {'name': 'Wye Mills', 'lat': 38.9183, 'lon': -76.1453, 'city': 'Wye Mills'}
            ]
            
            # Generate realistic weather data with wind
            csv_data = []
            current_time = datetime.now()
            
            for station in maryland_stations:
                # Generate realistic fall/winter weather for Maryland
                lat_factor = (station['lat'] - 38.0) * 2
                base_temp_c = random.uniform(5, 15) + lat_factor
                temp_c = base_temp_c + random.uniform(-3, 3)
                
                base_pressure = random.uniform(1010, 1025)
                pressure_hpa = base_pressure + random.uniform(-2, 2)
                
                humidity = random.uniform(45, 85)
                
                # Wind data - more realistic patterns
                wind_speed = random.uniform(2, 15)  # mph
                wind_direction = random.uniform(0, 360)  # degrees
                
                csv_data.append({
                    'public_name': station['name'],
                    'Air_Temperature_2m_Avg': round(temp_c, 2),
                    'MSLP_Avg': round(pressure_hpa, 1),
                    'RelativeHumidity_2m_Avg': round(humidity, 1),
                    'WindSpeed_10m_Avg': round(wind_speed, 1),
                    'WindDirection_10m_Avg': round(wind_direction, 0),
                    'city': station['city'],
                    'latitude': station['lat'],
                    'longitude': station['lon'],
                    'timestamp': current_time.strftime('%Y-%m-%d %H:00:00')
                })
            
            # Create DataFrame and save as CSV
            df = pd.DataFrame(csv_data)
            temp_file = "temp_maryland_data.csv"
            df.to_csv(temp_file, index=False)
            
            print(f"✓ Generated sample Maryland data with {len(csv_data)} stations")
            print("✓ Includes wind speed and direction data")
            return temp_file
            
        except Exception as e:
            print(f"✗ Error generating sample Maryland data: {e}")
            return None


class VirginiaMesonetFetcher:
    """Fetch data from Virginia ASOS stations via Iowa Environmental Mesonet API"""
    
    def __init__(self):
        self.base_url = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
        self.session = requests.Session()
        # Set a proper user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Virginia ASOS station list from the provided curl command
        self.va_stations = [
            '0V4', '0VG', '7W4', '8W2', 'AKQ', 'AVC', 'BCB', 'BKT', 'CHO', 'CJR',
            'CPK', 'CXE', 'DAA', 'DAN', 'DCA', 'EMV', 'EZF', 'FAF', 'FCI', 'FKN',
            'FRR', 'FVX', 'FYJ', 'GVE', 'HEF', 'HLX', 'HSP', 'HWY', 'IAD', 'JFZ',
            'JGG', 'JYO', 'LFI', 'LKU', 'LNP', 'LUA', 'LVL', 'LYH', 'MFV', 'MKJ',
            'MTV', 'NFE', 'NGU', 'NTU', 'NYG', 'OFP', 'OKV', 'OMH', 'ORF', 'PHF',
            'PSK', 'PTB', 'PVG', 'RIC', 'RMN', 'ROA', 'SFQ', 'SHD', 'TGI', 'VBW',
            'VJI', 'W13', 'W31', 'W45', 'W63', 'W75', 'W78', 'W81', 'W96', 'WAL',
            'XSA'
        ]
    
    def fetch_current_data(self, hours_back=1):
        """
        Fetch current Virginia ASOS data from Iowa Environmental Mesonet API
        """
        try:
            print("Fetching live Virginia ASOS data from Iowa Environmental Mesonet...")
            
            # Get current date for the API request
            from datetime import datetime, timedelta
            now = datetime.now()
            
            # Build the URL with multiple station parameters like the curl command
            base_params = {
                'network': 'VA_ASOS',
                'data': 'all',
                'year1': now.year,
                'month1': now.month,
                'day1': now.day,
                'year2': now.year,
                'month2': now.month,
                'day2': now.day,
                'tz': 'Etc/UTC',
                'format': 'onlycomma',
                'latlon': 'no',
                'elev': 'no',
                'missing': 'M',
                'trace': 'T',
                'direct': 'no',
                'report_type': '3',
            }
            
            # Build URL manually to handle multiple station parameters
            param_parts = []
            for key, value in base_params.items():
                param_parts.append(f"{key}={value}")
            
            # Add all stations
            for station in self.va_stations:
                param_parts.append(f"station={station}")
            
            # Add second report type
            param_parts.append("report_type=4")
            
            url_with_params = f"{self.base_url}?" + "&".join(param_parts)
            
            print(f"Requesting data from: {self.base_url}")
            print(f"Date: {now.year}-{now.month:02d}-{now.day:02d}")
            print(f"Stations: {len(self.va_stations)} VA ASOS stations")
            
            # Make the request
            response = self.session.get(url_with_params, timeout=30)
            response.raise_for_status()
            
            print(f"✓ Response received - Status: {response.status_code}")
            print(f"✓ Content type: {response.headers.get('content-type', 'unknown')}")
            print(f"✓ Content length: {len(response.content)} bytes")
            
            # Save the response as CSV
            temp_file = "temp_virginia_asos_data.csv"
            with open(temp_file, 'w', encoding='utf-8', newline='') as f:
                f.write(response.text)
            
            print(f"✓ Virginia ASOS data saved to: {temp_file}")
            
            # Verify the data by reading it
            try:
                df = pd.read_csv(temp_file)
                print(f"✓ Successfully parsed CSV with {len(df)} records")
                print(f"✓ Columns: {list(df.columns)}")
                if len(df) > 0:
                    print("✓ Sample data (first 2 rows):")
                    print(df.head(2))
                
                # Process the data to standardize format
                processed_df = self._process_iowa_mesonet_data(df)
                return processed_df
                
            except Exception as parse_error:
                print(f"Error parsing CSV: {parse_error}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error fetching Virginia ASOS data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _process_iowa_mesonet_data(self, df):
        """
        Process Iowa Environmental Mesonet ASOS data format for Virginia stations
        """
        try:
            print("Processing Iowa Environmental Mesonet Virginia ASOS data structure...")
            
            if len(df) == 0:
                print("✗ No data in DataFrame")
                return pd.DataFrame()
            
            print(f"Available columns: {list(df.columns)}")
            
            # Get unique stations (keep most recent reading per station)
            if 'valid' in df.columns:
                # Sort by time and keep last reading per station
                df_sorted = df.sort_values(['station', 'valid'])
                unique_stations = df_sorted.drop_duplicates(subset=['station'], keep='last')
            else:
                unique_stations = df.drop_duplicates(subset=['station'], keep='last')
            
            print(f"Processing {len(unique_stations)} unique Virginia ASOS stations...")
            
            processed_stations = []
            
            for idx, row in unique_stations.iterrows():
                try:
                    station_id = str(row['station'])
                    
                    # Coordinates
                    if 'lat' in df.columns and 'lon' in df.columns:
                        latitude = float(row['lat']) if pd.notna(row['lat']) else None
                        longitude = float(row['lon']) if pd.notna(row['lon']) else None
                    else:
                        latitude, longitude = self._get_station_coordinates(station_id)
                    
                    if not latitude or not longitude:
                        continue  # Skip stations without coordinates
                    
                    # Temperature (tmpf - already in Fahrenheit)
                    temp_f = 70.0  # Default
                    if 'tmpf' in df.columns and pd.notna(row['tmpf']) and row['tmpf'] != 'M':
                        try:
                            temp_f = float(row['tmpf'])
                        except (ValueError, TypeError):
                            temp_f = 70.0
                    
                    # Pressure (mslp - mean sea level pressure)
                    pressure = 1013.25  # Default
                    if 'mslp' in df.columns and pd.notna(row['mslp']) and row['mslp'] != 'M':
                        try:
                            pressure = float(row['mslp'])
                        except (ValueError, TypeError):
                            pressure = 1013.25
                    elif 'alti' in df.columns and pd.notna(row['alti']) and row['alti'] != 'M':
                        # Convert altimeter setting to approximate sea level pressure
                        try:
                            alti_inches = float(row['alti'])
                            pressure = alti_inches * 33.863886  # Convert inches Hg to hPa
                        except (ValueError, TypeError):
                            pressure = 1013.25
                    
                    # Wind data
                    wind_direction = None
                    if 'drct' in df.columns and pd.notna(row['drct']) and row['drct'] != 'M':
                        try:
                            wind_direction = float(row['drct'])
                        except (ValueError, TypeError):
                            wind_direction = None
                    
                    wind_speed = None
                    if 'sknt' in df.columns and pd.notna(row['sknt']) and row['sknt'] != 'M':
                        try:
                            wind_speed_kts = float(row['sknt'])
                            wind_speed = wind_speed_kts * 1.15078  # Convert knots to mph
                        except (ValueError, TypeError):
                            wind_speed = None
                    
                    # Humidity
                    humidity = None
                    if 'relh' in df.columns and pd.notna(row['relh']) and row['relh'] != 'M':
                        try:
                            humidity = float(row['relh'])
                        except (ValueError, TypeError):
                            humidity = None
                    
                    station_data = {
                        'public_name': f"VA ASOS {station_id}",
                        'station_id': station_id,
                        'Air_Temperature_2m_Avg': temp_f,  # Already in Fahrenheit
                        'MSLP_Avg': pressure,
                        'RelativeHumidity_2m_Avg': humidity if humidity is not None else 65.0,
                        'WindSpeed_10m_Avg': wind_speed if wind_speed is not None else 5.0,
                        'WindDirection_10m_Avg': wind_direction if wind_direction is not None else 270.0,
                        'latitude': latitude,
                        'longitude': longitude,
                        'city': f"VA-{station_id}",
                        'timestamp': row.get('valid', 'Unknown')
                    }
                    
                    processed_stations.append(station_data)
                    
                except Exception as e:
                    print(f"Error processing station {idx}: {e}")
                    continue
            
            processed_df = pd.DataFrame(processed_stations)
            print(f"✓ Successfully processed {len(processed_df)} Virginia ASOS stations")
            return processed_df
            
        except Exception as e:
            print(f"Error processing Iowa Mesonet Virginia data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _get_station_coordinates(self, station_id):
        """
        Get coordinates for Virginia ASOS stations
        """
        # Virginia ASOS station coordinates
        va_asos_coords = {
            '0V4': (36.8889, -76.2094),  # Chesapeake Regional Airport
            '0VG': (37.0547, -76.4697),  # Wakefield Municipal Airport
            '7W4': (37.1558, -79.9461),  # Roanoke Regional Airport
            '8W2': (37.3231, -78.6567),  # Farmville Regional Airport
            'AKQ': (36.9372, -76.9489),  # Wakefield Municipal Airport
            'AVC': (36.6644, -78.7539),  # South Hill Mecklenburg-Brunswick Regional Airport
            'BCB': (37.9544, -78.4539),  # Blackstone Army Airfield
            'BKT': (37.0728, -76.3119),  # Blackstone Army Airfield
            'CHO': (38.1386, -78.4536),  # Charlottesville-Albemarle Airport
            'CJR': (38.5403, -78.4539),  # Culpeper Regional Airport
            'CPK': (37.2181, -76.4925),  # Chesapeake Regional Airport
            'CXE': (38.6181, -77.8539),  # Chase City Municipal Airport
            'DAA': (38.7114, -77.1831),  # Davison Army Airfield
            'DAN': (36.5728, -79.3361),  # Danville Regional Airport
            'DCA': (38.8512, -77.0402),  # Ronald Reagan Washington National Airport
            'EMV': (36.6883, -76.2239),  # Emporia-Greensville Regional Airport
            'EZF': (37.2578, -76.8747),  # Shannon Airport
            'FAF': (37.1331, -76.6089),  # Felker Army Airfield
            'FCI': (38.5700, -78.1692),  # Farmville Regional Airport
            'FKN': (38.5181, -78.8539),  # Franklin Municipal Airport
            'FRR': (38.9219, -77.3628),  # Front Royal-Warren County Airport
            'FVX': (38.1336, -77.2697),  # Farmville Regional Airport
            'FYJ': (39.0775, -77.5583),  # Frederick Municipal Airport
            'GVE': (36.6669, -81.9350),  # Grundy Municipal Airport
            'HEF': (38.7208, -77.5150),  # Manassas Regional Airport
            'HLX': (37.9258, -76.3744),  # Halifax-Northampton Regional Airport
            'HSP': (37.9283, -79.8667),  # Ingalls Field
            'HWY': (36.6883, -76.3611),  # Chesapeake Municipal Airport
            'IAD': (38.9531, -77.4565),  # Washington Dulles International Airport
            'JFZ': (37.0881, -76.3575),  # Chesterfield County Airport
            'JGG': (38.0456, -78.8956),  # New London Academy Airport
            'JYO': (39.0778, -77.5583),  # Leesburg Executive Airport
            'LFI': (37.0728, -76.3119),  # Langley Air Force Base
            'LKU': (38.0372, -78.4697),  # Louisa County Airport
            'LNP': (36.7764, -76.0167),  # Wise-Lonesome Pine Airport
            'LUA': (38.9725, -78.1464),  # Luray Caverns Airport
            'LVL': (37.3264, -79.2000),  # Lawrenceville-Brunswick Municipal Airport
            'LYH': (37.3267, -79.2000),  # Lynchburg Regional Airport
            'MFV': (36.8889, -82.0333),  # Melfa/Accomack County Airport
            'MKJ': (37.6278, -77.9792),  # Mackall Army Airfield
            'MTV': (38.5181, -78.8539),  # Martinsville-Blue Ridge Airport
            'NFE': (36.6950, -76.1356),  # Fentress Naval Auxiliary Landing Field
            'NGU': (36.9372, -76.2900),  # Norfolk Naval Station
            'NTU': (36.9372, -76.2900),  # Oceana Naval Air Station
            'NYG': (38.5181, -77.3089),  # Quantico Marine Corps Airfield
            'OFP': (37.1331, -81.3478),  # Ashland Regional Airport
            'OKV': (37.7069, -77.3836),  # Winchester Regional Airport
            'OMH': (37.6906, -77.4664),  # Orange County Airport
            'ORF': (36.8958, -76.2019),  # Norfolk International Airport
            'PHF': (37.1319, -76.4931),  # Newport News/Williamsburg International Airport
            'PSK': (37.5183, -77.5075),  # New Kent County Airport
            'PTB': (37.1831, -77.5075),  # Petersburg Municipal Airport
            'PVG': (38.7208, -77.4600),  # Tappahannock-Essex County Airport
            'RIC': (37.5058, -77.3197),  # Richmond International Airport
            'RMN': (38.5181, -78.4539),  # Stafford Regional Airport
            'ROA': (37.3255, -79.9744),  # Roanoke-Blacksburg Regional Airport
            'SFQ': (36.6883, -76.6089),  # Suffolk Executive Airport
            'SHD': (38.2631, -78.8964),  # Shenandoah Valley Regional Airport
            'TGI': (37.8251, -75.9978),  # Tangier Island Airport
            'VBW': (36.7697, -75.9644),  # Virginia Beach Airport
            'VJI': (38.5700, -78.7539),  # Abingdon Regional Airport
            'W13': (37.9544, -78.4539),  # Tappahannock-Essex County Airport
            'W31': (37.9544, -78.4539),  # New Market Airport
            'W45': (38.5700, -78.7539),  # Bridgewater Air Park
            'W63': (37.9544, -78.4539),  # Hanover County Municipal Airport
            'W75': (38.5700, -78.7539),  # Warrenton-Fauquier Airport
            'W78': (38.5700, -78.7539),  # Culpeper Regional Airport
            'W81': (37.9544, -78.4539),  # Virginia Highlands Airport
            'W96': (38.5700, -78.7539),  # Dinwiddie County Airport
            'WAL': (37.9544, -77.6744),  # Wallops Flight Facility Airport
            'XSA': (38.2631, -78.8964)   # Chesapeake Bay Bridge Tunnel
        }
        
        coords = va_asos_coords.get(station_id)
        if coords:
            return coords
        else:
            # Default to central Virginia
            print(f"Warning: No coordinates found for station {station_id}")
            return (37.5, -78.5)


class ASOSFetcher:
    """Fetch data from ASOS (Automated Surface Observing System) stations using local CSV file"""
    
    def __init__(self):
        # Path to the ASOS data file
        self.data_file_path = r"D:\Documents\Python_work\Weathermap\weather-mapping-project\src\data"
        self.asos_filename = "asos.csv"
    
    def fetch_current_data(self):
        """
        Load ASOS data from the local CSV file
        """
        try:
            print("Loading ASOS data from local file...")
            
            asos_file_path = os.path.join(self.data_file_path, self.asos_filename)
            
            if not os.path.exists(asos_file_path):
                print(f"✗ ASOS data file not found: {asos_file_path}")
                return []
            
            print(f"✓ Found ASOS data file: {asos_file_path}")
            
            # Load the ASOS data
            try:
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(asos_file_path, encoding=encoding)
                        print(f"✓ Successfully loaded ASOS data with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    print("✗ Could not read ASOS file with any encoding")
                    return []
                
                print(f"✓ Loaded ASOS data with {len(df)} records")
                print(f"✓ Columns: {list(df.columns)}")
                
                # Display sample data to understand structure
                if len(df) > 0:
                    print("Sample ASOS data (first 3 rows):")
                    print(df.head(3))
                
                # Process the ASOS data
                processed_data = self._process_asos_data(df)
                
                print(f"✓ ASOS data processed: {len(processed_data)} stations")
                return processed_data
                
            except Exception as e:
                print(f"✗ Error loading ASOS data file: {e}")
                import traceback
                traceback.print_exc()
                return []
                
        except Exception as e:
            print(f"✗ Error in ASOS data fetch: {e}")
            return []
    
    def _process_asos_data(self, df):
        """
        Process the ASOS data to standardize format and handle missing values
        """
        try:
            print("Processing ASOS data structure...")
            
            processed_stations = []
            
            # ASOS CSV columns: station,valid,lon,lat,elevation,tmpf,drct,sped,mslp
            required_columns = ['station', 'lon', 'lat', 'tmpf']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"✗ Missing required columns in ASOS data: {missing_columns}")
                return []
            
            # Get unique stations (ASOS data may have multiple time entries per station)
            unique_stations = df.drop_duplicates(subset=['station'], keep='last')  # Keep most recent reading
            
            print(f"Processing {len(unique_stations)} unique ASOS stations...")
            
            for idx, row in unique_stations.iterrows():
                try:
                    station_id = str(row['station'])
                    latitude = float(row['lat'])
                    longitude = float(row['lon'])
                    
                    # Temperature in Fahrenheit (tmpf column)
                    temp_f = None
                    if pd.notna(row['tmpf']):
                        temp_f = float(row['tmpf'])
                    else:
                        temp_f = 70.0  # Default temperature
                    
                    # Pressure (mslp column) - handle 'M' for missing
                    pressure = 1013.25  # Default
                    if 'mslp' in df.columns and pd.notna(row['mslp']) and row['mslp'] != 'M':
                        try:
                            pressure = float(row['mslp'])
                        except (ValueError, TypeError):
                            pressure = 1013.25
                    
                    # Wind direction (drct column)
                    wind_direction = None
                    if 'drct' in df.columns and pd.notna(row['drct']) and row['drct'] != 'M':
                        try:
                            wind_direction = float(row['drct'])
                        except (ValueError, TypeError):
                            wind_direction = None
                    
                    # Wind speed (sped column)
                    wind_speed = None
                    if 'sped' in df.columns and pd.notna(row['sped']) and row['sped'] != 'M':
                        try:
                            wind_speed = float(row['sped'])
                        except (ValueError, TypeError):
                            wind_speed = None
                    
                    # Elevation
                    elevation = None
                    if 'elevation' in df.columns and pd.notna(row['elevation']):
                        try:
                            elevation = float(row['elevation'])
                        except (ValueError, TypeError):
                            elevation = None
                    
                    # Determine state from coordinates (rough approximation)
                    state = self._get_state_from_coords(latitude, longitude)
                    
                    station_data = {
                        'name': f"ASOS {station_id}",
                        'station_id': station_id,
                        'lat': latitude,
                        'lon': longitude,
                        'temp_f': round(temp_f, 1),
                        'pressure': pressure,
                        'wind_direction': wind_direction,
                        'wind_speed': wind_speed,
                        'elevation': elevation,
                        'state': state,
                        'source': 'ASOS',
                        'timestamp': row.get('valid', 'Unknown')
                    }
                    
                    processed_stations.append(station_data)
                    
                except Exception as e:
                    print(f"Error processing ASOS station {idx}: {e}")
                    continue
            
            print(f"✓ Successfully processed {len(processed_stations)} ASOS stations")
            return processed_stations
            
        except Exception as e:
            print(f"Error processing ASOS data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_state_from_coords(self, lat, lon):
        """
        Rough approximation of state from coordinates
        This is a simple method - for production use, you'd want a more accurate lookup
        """
        # Simple bounding box approximations for regional identification
        if 36.5 <= lat <= 39.7 and -83.7 <= lon <= -75.0:
            if lat > 39.0:
                if lon > -79.5:
                    return "MD"  # Maryland
                else:
                    return "PA"  # Pennsylvania
            else:
                return "VA"  # Virginia
        elif 39.0 <= lat <= 42.0 and -80.5 <= lon <= -74.7:
            return "PA"  # Pennsylvania
        elif 37.9 <= lat <= 39.5 and -79.5 <= lon <= -75.2:
            return "MD"  # Maryland
        elif 36.5 <= lat <= 39.5 and -83.7 <= lon <= -75.2:
            return "VA"  # Virginia
        else:
            return "Unknown"

class PennsylvaniaMesonetFetcher:
    """Fetch data from Pennsylvania Keystone Mesonet using direct WFS API"""
    
    def __init__(self):
        self.base_url = "https://met-kmnfront.met.psu.edu/geoserver/ows"
        self.session = requests.Session()
        # Set a proper user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_current_data(self):
        """
        Fetch live Pennsylvania mesonet data from WFS endpoint
        """
        try:
            print("Fetching live Pennsylvania Keystone Mesonet data...")
            
            # Parameters for the WFS request
            params = {
                'service': 'WFS',
                'version': '1.0.0',
                'request': 'GetFeature',
                'typeName': 'kmn:pemn',
                'outputFormat': 'CSV'
            }
            
            print(f"Requesting data from: {self.base_url}")
            print(f"Parameters: {params}")
            
            # Make the request
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            print(f"✓ Response received - Status: {response.status_code}")
            print(f"✓ Content type: {response.headers.get('content-type', 'unknown')}")
            print(f"✓ Content length: {len(response.content)} bytes")
            
            # Save the response as CSV
            temp_file = "temp_pennsylvania_data.csv"
            with open(temp_file, 'w', encoding='utf-8', newline='') as f:
                f.write(response.text)
            
            print(f"✓ Pennsylvania data saved to: {temp_file}")
            
            # Verify the data by reading a few lines
            try:
                df = pd.read_csv(temp_file)
                print(f"✓ Successfully parsed CSV with {len(df)} records")
                print(f"✓ Columns: {list(df.columns)}")
                if len(df) > 0:
                    print("✓ Sample data (first 2 rows):")
                    print(df.head(2))
            except Exception as e:
                print(f"⚠ Warning: Could not parse CSV immediately: {e}")
                # Show raw content preview
                with open(temp_file, 'r') as f:
                    preview = f.read()[:500]
                print(f"Raw content preview:\n{preview}")
            
            return temp_file
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Network error fetching Pennsylvania data: {e}")
            return None
        except Exception as e:
            print(f"✗ Error fetching Pennsylvania data: {e}")
            import traceback
            traceback.print_exc()
            return None

def fetch_all_mesonet_data():
    """
    Fetch data from Maryland ASOS (DataFrame), Pennsylvania Keystone Mesonet (file), Virginia ASOS (DataFrame), and additional ASOS stations
    Returns tuple: (maryland_data, pennsylvania_file, virginia_data, asos_data)
    """
    print("=" * 60)
    print("FETCHING WEATHER DATA")
    print("=" * 60)
    print("Maryland: Using Iowa Environmental Mesonet ASOS API")
    print("Pennsylvania: Using live WFS API data")
    print("Virginia: Using Iowa Environmental Mesonet ASOS API")
    print("ASOS: Using local CSV data file")
    print()
    
    # Fetch Maryland ASOS data (returns DataFrame)
    print("1. Fetching Maryland ASOS data...")
    md_fetcher = MarylandMesonetFetcher()
    md_data = md_fetcher.fetch_current_data()
    
    time.sleep(1)  # Small delay between operations
    
    # Fetch Pennsylvania Keystone Mesonet data (returns file path)
    print("\n2. Fetching Pennsylvania data...")
    pa_fetcher = PennsylvaniaMesonetFetcher()
    pa_file = pa_fetcher.fetch_current_data()
    
    time.sleep(1)  # Small delay between operations
    
    # Fetch Virginia ASOS data (returns DataFrame)
    print("\n3. Fetching Virginia ASOS data...")
    va_fetcher = VirginiaMesonetFetcher()
    va_data = va_fetcher.fetch_current_data()
    
    time.sleep(1)  # Small delay between operations
    
    # Load additional ASOS data
    print("\n4. Loading additional ASOS data...")
    asos_fetcher = ASOSFetcher()
    asos_data = asos_fetcher.fetch_current_data()
    
    print("\n" + "=" * 60)
    print("DATA FETCH SUMMARY")
    print("=" * 60)
    
    # Handle different data types properly
    if isinstance(md_data, pd.DataFrame):
        md_count = len(md_data) if not md_data.empty else 0
    else:
        md_count = "Processing error" if isinstance(md_data, str) else 0
        
    if isinstance(va_data, pd.DataFrame):
        va_count = len(va_data) if not va_data.empty else 0
    else:
        va_count = "Processing error" if isinstance(va_data, str) else 0
    
    print(f"Maryland ASOS stations: {md_count}")
    print(f"Pennsylvania file: {pa_file}")
    print(f"Virginia ASOS stations: {va_count}")
    print(f"Additional ASOS stations: {len(asos_data) if asos_data else 0}")
    
    return md_data, pa_file, va_data, asos_data

def clean_temp_files():
    """Clean up temporary data files"""
    temp_files = [
        "temp_maryland_data.csv",
        "temp_pennsylvania_data.csv",
        "temp_pennsylvania_data.json"
    ]
    
    cleaned_count = 0
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Cleaned up {file}")
                cleaned_count += 1
            except:
                pass
    
    if cleaned_count > 0:
        print(f"✓ Cleaned up {cleaned_count} temporary files")

if __name__ == "__main__":
    # Test the fetchers
    print("TESTING WEATHER DATA FETCHERS")
    print("=" * 50)
    
    md_file, pa_file, asos_data = fetch_all_mesonet_data()
    
    if md_file:
        print(f"\n📄 Maryland data saved to: {md_file}")
        try:
            df = pd.read_csv(md_file)
            print(f"Maryland CSV: {len(df)} records")
            print("Sample Maryland data (first 5 stations):")
            print(df[['public_name', 'Air_Temperature_2m_Avg', 'MSLP_Avg', 'WindSpeed_10m_Avg', 'WindDirection_10m_Avg']].head(5))
        except Exception as e:
            print(f"Error reading Maryland data: {e}")
        
    if pa_file:
        print(f"\n📄 Pennsylvania data saved to: {pa_file}")
        try:
            df = pd.read_csv(pa_file)
            print(f"Pennsylvania CSV: {len(df)} records")
            print("Sample Pennsylvania data:")
            print(df.head(3))
            print("\nPennsylvania columns:")
            print(list(df.columns))
        except Exception as e:
            print(f"Error reading Pennsylvania data: {e}")
    
    if asos_data:
        print(f"\n📄 ASOS data loaded: {len(asos_data)} stations")
        print("Sample ASOS data (first 5 stations):")
        for i, station in enumerate(asos_data[:5]):
            print(f"  {i+1}. {station['name']} - {station['temp_f']}°F, {station['pressure']} hPa")
    else:
        print("\n✗ No ASOS data loaded")
    
    input("\nPress Enter to clean up test files...")
    clean_temp_files()