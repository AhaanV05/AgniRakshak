import xgboost as xgb
import requests
import json
from datetime import datetime
import numpy as np
import os

class WildfirePredictor:
    def __init__(self, xweather_client_id, xweather_client_secret, model_path):
        self.xweather_client_id = xweather_client_id
        self.xweather_client_secret = xweather_client_secret
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)
    
    def get_weather_data(self, lat, lon):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation',
            'timezone': 'auto'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            current = data.get('current', {})
            
            temp_c = current.get('temperature_2m', 25)
            rh_pct = current.get('relative_humidity_2m', 50)

            # Open-Meteo returns wind_speed_10m in km/h by default in the current_units
            # Convert km/h to m/s (1 km/h = 1/3.6 m/s)
            ws_kmh = current.get('wind_speed_10m', 5)
            try:
                ws_mean_mps = float(ws_kmh) / 3.6
            except Exception:
                ws_mean_mps = float(5) / 3.6

            svp = 0.6108 * np.exp(17.27 * temp_c / (temp_c + 237.3))
            vpd = svp * (1 - rh_pct / 100)

            return {
                'tmax_c': temp_c,
                'rh_pct': rh_pct,
                'ws_mean_mps': round(ws_mean_mps, 2),
                'precip_mm_24h': current.get('precipitation', 0),
                'vpd_kpa': round(vpd, 2)
            }, None
        except Exception as e:
            return None, f"Error: {e}"
    
    def get_lightning_data(self, lat, lon):
        endpoint = "https://api.aerisapi.com/lightning/closest"
        params = {
            'client_id': self.xweather_client_id,
            'client_secret': self.xweather_client_secret,
            'p': f'{lat},{lon}',
            'radius': '50mi',
            'limit': 100,
            'from': '-24hours'
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('response') and len(data['response']) > 0:
                return 1, len(data['response'])
            return 0, 0
        except:
            return 0, 0
    
    def predict(self, lat, lon):
        weather_data, error = self.get_weather_data(lat, lon)
        if error:
            return json.dumps({'error': error, 'timestamp': datetime.now().isoformat()}, indent=2)
        
        lightning, strike_count = self.get_lightning_data(lat, lon)
        
        features = np.array([[
            weather_data['tmax_c'],
            weather_data['rh_pct'],
            weather_data['ws_mean_mps'],
            weather_data['precip_mm_24h'],
            weather_data['vpd_kpa'],
            lightning
        ]])
        
        probability = float(self.model.predict_proba(features)[0][1])
        prediction = int(self.model.predict(features)[0])
        
        risk_levels = ['Low', 'Moderate', 'High', 'Very High', 'Extreme']
        risk_index = min(int(probability * 5), 4)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'location': {'latitude': float(lat), 'longitude': float(lon)},
            'weather_conditions': {
                'temperature_celsius': float(weather_data['tmax_c']),
                'relative_humidity_percent': float(weather_data['rh_pct']),
                'wind_speed_mps': float(weather_data['ws_mean_mps']),
                'precipitation_mm_24h': float(weather_data['precip_mm_24h']),
                'vapor_pressure_deficit_kpa': float(weather_data['vpd_kpa'])
            },
            'lightning_activity': {
                'detected': bool(lightning),
                'strike_count_24h': int(strike_count)
            },
            'wildfire_prediction': {
                'fire_risk_percentage': round(probability * 100, 2),
                'risk_level': risk_levels[risk_index],
                'fire_expected': bool(prediction)
            }
        }
        
        return json.dumps(result, indent=2)

    def predict_dict(self, lat, lon):
        """Return the prediction result as a Python dict (useful for HTTP responses)."""
        weather_data, error = self.get_weather_data(lat, lon)
        if error:
            return {'error': error, 'timestamp': datetime.now().isoformat()}

        lightning, strike_count = self.get_lightning_data(lat, lon)

        features = np.array([[
            weather_data['tmax_c'],
            weather_data['rh_pct'],
            weather_data['ws_mean_mps'],
            weather_data['precip_mm_24h'],
            weather_data['vpd_kpa'],
            lightning
        ]])

        try:
            probability = float(self.model.predict_proba(features)[0][1])
            prediction = int(self.model.predict(features)[0])
        except Exception as e:
            return {'error': f'Model prediction failed: {e}', 'timestamp': datetime.now().isoformat()}

        risk_levels = ['Low', 'Moderate', 'High', 'Very High', 'Extreme']
        risk_index = min(int(probability * 5), 4)

        result = {
            'timestamp': datetime.now().isoformat(),
            'location': {'latitude': float(lat), 'longitude': float(lon)},
            'weather_conditions': {
                'temperature_celsius': float(weather_data['tmax_c']),
                'relative_humidity_percent': float(weather_data['rh_pct']),
                'wind_speed_mps': float(weather_data['ws_mean_mps']),
                'precipitation_mm_24h': float(weather_data['precip_mm_24h']),
                'vapor_pressure_deficit_kpa': float(weather_data['vpd_kpa'])
            },
            'lightning_activity': {
                'detected': bool(lightning),
                'strike_count_24h': int(strike_count)
            },
            'wildfire_prediction': {
                'fire_risk_percentage': round(probability * 100, 2),
                'risk_level': risk_levels[risk_index],
                'fire_expected': bool(prediction)
            }
        }

        return result


# Usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    predictor = WildfirePredictor(
        xweather_client_id=os.getenv('AERIS_CLIENT_ID', 'demo'),
        xweather_client_secret=os.getenv('AERIS_CLIENT_SECRET', 'demo'),
        model_path=os.getenv('WILDFIRE_MODEL_PATH', 'wildfire_xgboost_model.json')
    )
    
    lat = 9.13364
    lon = -72.21142
    
    print("\nFetching data and predicting...")
    print(predictor.predict(lat, lon))