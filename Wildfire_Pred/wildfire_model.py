import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import json
import requests
from datetime import datetime

# Load the dataset
df = pd.read_csv('wildfire_weather_dataset_3000_records.csv')

# Step 1: Generate lightning strike column with specified correlation
np.random.seed(42)

def generate_lightning_column(df):
    """
    Generate lightning strike column where 90-95% of lightning strikes 
    correlate with wildfires
    """
    lightning = np.zeros(len(df), dtype=int)
    
    # Get indices of fire and no-fire cases
    fire_indices = df[df['fire'] == 1].index
    no_fire_indices = df[df['fire'] == 0].index
    
    # Determine how many lightning strikes to generate
    # Target: ~15-20% of total observations have lightning
    total_lightning = int(len(df) * 0.17)
    
    # 92.5% of lightning strikes should correlate with fires (midpoint of 90-95%)
    lightning_with_fire = int(total_lightning * 0.925)
    lightning_without_fire = total_lightning - lightning_with_fire
    
    # Randomly assign lightning strikes to fire cases
    if len(fire_indices) >= lightning_with_fire:
        selected_fire_indices = np.random.choice(
            fire_indices, 
            size=lightning_with_fire, 
            replace=False
        )
        lightning[selected_fire_indices] = 1
    
    # Randomly assign remaining lightning strikes to no-fire cases
    if len(no_fire_indices) >= lightning_without_fire:
        selected_no_fire_indices = np.random.choice(
            no_fire_indices, 
            size=lightning_without_fire, 
            replace=False
        )
        lightning[selected_no_fire_indices] = 1
    
    return lightning

df['lightning_strike_24h'] = generate_lightning_column(df)

# Verify the correlation
lightning_fire_corr = df[df['lightning_strike_24h'] == 1]['fire'].mean()
print(f"Percentage of lightning strikes that result in fires: {lightning_fire_corr*100:.2f}%")
print(f"Total lightning strikes: {df['lightning_strike_24h'].sum()}")
print(f"Total fires: {df['fire'].sum()}")

# Save updated dataset
df.to_csv('wildfire_weather_dataset_with_lightning.csv', index=False)

# Step 2: Prepare data for XGBoost
feature_columns = ['tmax_c', 'rh_pct', 'ws_mean_mps', 'precip_mm_24h', 
                   'vpd_kpa', 'lightning_strike_24h']
X = df[feature_columns]
y = df['fire']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Step 3: Train XGBoost model
model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='logloss'
)

model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

print("\n=== Model Performance ===")
print(classification_report(y_test, y_pred))
print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print("\n=== Feature Importance ===")
print(feature_importance)

# Save model
model.save_model('wildfire_xgboost_model.json')

# Step 4: Lightning API Integration and Prediction Function
class WildfirePredictionAPI:
    def __init__(self, xweather_client_id, xweather_client_secret, model):
        """
        Initialize the API with Xweather credentials
        Get credentials from: https://www.xweather.com/account/
        """
        self.client_id = xweather_client_id
        self.client_secret = xweather_client_secret
        self.model = model
        self.base_url = "https://api.aerisapi.com"
    
    def get_lightning_data(self, lat, lon, hours_back=24):
        """
        Fetch lightning strike data from Xweather API
        """
        endpoint = f"{self.base_url}/lightning/closest"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'p': f'{lat},{lon}',
            'radius': '50mi',
            'limit': 100,
            'from': f'-{hours_back}hours'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check if lightning strikes occurred
            if data.get('response') and len(data['response']) > 0:
                return 1  # Lightning detected
            return 0  # No lightning
        except Exception as e:
            print(f"Error fetching lightning data: {e}")
            return 0  # Default to no lightning if API fails
    
    def predict_wildfire_risk(self, weather_data, use_api=False, lat=None, lon=None):
        """
        Predict wildfire risk based on weather conditions
        
        Parameters:
        - weather_data: dict with keys: tmax_c, rh_pct, ws_mean_mps, 
                        precip_mm_24h, vpd_kpa
        - use_api: bool, whether to fetch real lightning data from API
        - lat, lon: coordinates for lightning API call
        
        Returns: JSON with prediction results
        """
        # Get lightning data
        if use_api and lat and lon:
            lightning = self.get_lightning_data(lat, lon)
        else:
            lightning = weather_data.get('lightning_strike_24h', 0)
        
        # Prepare features
        features = np.array([[
            weather_data['tmax_c'],
            weather_data['rh_pct'],
            weather_data['ws_mean_mps'],
            weather_data['precip_mm_24h'],
            weather_data['vpd_kpa'],
            lightning
        ]])
        
        # Make prediction
        probability = self.model.predict_proba(features)[0][1]
        prediction = self.model.predict(features)[0]
        
        # Create response (convert numpy types to Python native types)
        result = {
            'timestamp': datetime.now().isoformat(),
            'location': {
                'latitude': float(lat) if lat else None,
                'longitude': float(lon) if lon else None
            } if lat and lon else None,
            'input_conditions': {
                'max_temperature_c': float(weather_data['tmax_c']),
                'relative_humidity_pct': float(weather_data['rh_pct']),
                'wind_speed_mps': float(weather_data['ws_mean_mps']),
                'precipitation_mm_24h': float(weather_data['precip_mm_24h']),
                'vapor_pressure_deficit_kpa': float(weather_data['vpd_kpa']),
                'lightning_strike_24h': bool(lightning)
            },
            'prediction': {
                'wildfire_risk_percentage': round(float(probability) * 100, 2),
                'risk_level': self._get_risk_level(probability),
                'fire_predicted': bool(int(prediction))
            }
        }
        
        return json.dumps(result, indent=2)
    
    def _get_risk_level(self, probability):
        """Convert probability to risk level"""
        if probability < 0.2:
            return 'Low'
        elif probability < 0.4:
            return 'Moderate'
        elif probability < 0.6:
            return 'High'
        elif probability < 0.8:
            return 'Very High'
        else:
            return 'Extreme'

# Example usage
print("\n=== Example Predictions ===")

# Initialize API with your actual credentials
predictor = WildfirePredictionAPI(
    xweather_client_id='vys7jtGpEpR9Z5jRWxNxt',
    xweather_client_secret='vqY2xMbLvuIQZCAefvQ8jBUQcxWaQFiT1ZGNhM51',
    model=model
)

# Example 1: High risk conditions
high_risk_data = {
    'tmax_c': 38.0,
    'rh_pct': 15,
    'ws_mean_mps': 12.0,
    'precip_mm_24h': 0.0,
    'vpd_kpa': 5.5,
    'lightning_strike_24h': 1
}

print("\nHigh Risk Scenario:")
print(predictor.predict_wildfire_risk(high_risk_data))

# Example 2: Low risk conditions
low_risk_data = {
    'tmax_c': 20.0,
    'rh_pct': 65,
    'ws_mean_mps': 5.0,
    'precip_mm_24h': 15.0,
    'vpd_kpa': 0.8,
    'lightning_strike_24h': 0
}

print("\nLow Risk Scenario:")
print(predictor.predict_wildfire_risk(low_risk_data))

# Example 3: With API call (commented out - requires valid credentials)
# print("\nWith Lightning API:")
# print(predictor.predict_wildfire_risk(
#     high_risk_data, 
#     use_api=True, 
#     lat=37.7749, 
#     lon=-122.4194
# ))