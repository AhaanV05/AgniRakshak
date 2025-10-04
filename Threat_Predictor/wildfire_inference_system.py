#!/usr/bin/env python3
"""
Complete Wildfire Inference System
Fetches live data, performs ROS prediction, and calculates fire behavior metrics.
"""

import joblib
import numpy as np
import os
import sys

# Get the directory of this file to handle imports properly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add current directory to Python path for imports
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import dependencies with proper path handling
try:
    from live_data_fetcher import get_live_features
    print("✅ Live data fetcher loaded")
except ImportError as e:
    print(f"⚠️ Failed to import live_data_fetcher: {e}")
    # Provide a simple fallback
    def get_live_features(lat, lon):
        return {
            'temp_c': 25.0, 'rel_humidity_pct': 50.0, 'wind_speed_ms': 5.0,
            'precip_mm': 0.0, 'vpd_kpa': 1.5, 'fwi': 10.0, 'ndvi': 0.5,
            'ndmi': 0.3, 'lfmc_proxy_pct': 100.0, 'elevation_m': 500.0,
            'slope_pct': 10.0, 'aspect_deg': 180.0
        }

# Import physics formulas with proper path handling
try:
    physics_file = os.path.join(CURRENT_DIR, 'live_api-Inference-follow_data.py')
    if os.path.exists(physics_file):
        # Use exec with proper path
        with open(physics_file, 'r') as f:
            exec(f.read())
        print("✅ Physics formulas loaded")
    else:
        raise FileNotFoundError(f"Physics file not found at {physics_file}")
except Exception as e:
    print(f"⚠️ Failed to load physics formulas: {e}")
    raise

class WildfireInferenceSystem:
    def __init__(self, model_path=None):
        """Initialize with trained XGBoost model."""
        print("🤖 Loading XGBoost model...")
        
        # Set default model path relative to current directory
        if model_path is None:
            model_path = os.path.join(CURRENT_DIR, "Ros_Pred", "wildfire_ros_xgboost_model_old.joblib")
            # Try alternative model names if the old one doesn't exist
            if not os.path.exists(model_path):
                alternatives = [
                    os.path.join(CURRENT_DIR, "Ros_Pred", "wildfire_ros_xgboost_model.joblib"),
                    os.path.join(CURRENT_DIR, "Ros_Pred", "wildfire_ros_xgboost_model_real.joblib")
                ]
                for alt_path in alternatives:
                    if os.path.exists(alt_path):
                        model_path = alt_path
                        break
        
        print(f"📁 Loading model from: {model_path}")
        
        # Load the model
        try:
            model_data = joblib.load(model_path)
        except Exception as e:
            print(f"❌ Failed to load model from {model_path}: {e}")
            raise
        
        # Handle different model storage formats
        if isinstance(model_data, dict):
            self.model = model_data.get('model', model_data)
            self.scaler = model_data.get('scaler', None)
            self.feature_columns = model_data.get('feature_columns', None)
        else:
            self.model = model_data
            self.scaler = None
            self.feature_columns = None
            
        print(f"✅ Model loaded successfully")
        if self.feature_columns:
            print(f"📊 Expected features: {self.feature_columns}")
    
    def predict_wildfire_threat(self, lat, lon):
        """
        Complete wildfire threat prediction for a location.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Complete wildfire threat assessment
        """
        print(f"🔥 WILDFIRE THREAT PREDICTION FOR ({lat}, {lon})")
        print("="*60)
        
        # Step 1: Get live features
        print("📡 STEP 1: Fetching live data...")
        features = get_live_features(lat, lon)
        
        # Step 2: Predict ROS
        print("\n🤖 STEP 2: Predicting Rate of Spread...")
        ros_prediction = self._predict_ros(features)
        
        # Step 3: Calculate fire behavior metrics
        print("\n⚗️ STEP 3: Calculating fire behavior metrics...")
        fire_metrics = self._calculate_fire_behavior(features, ros_prediction)
        
        # Step 4: Generate threat assessment
        print("\n🎯 STEP 4: Generating threat assessment...")
        threat_assessment = self._generate_threat_assessment(fire_metrics)
        
        # Compile complete results
        results = {
            'location': {'lat': lat, 'lon': lon},
            'live_features': features,
            'ros_prediction_m_per_min': ros_prediction,
            'fire_behavior': fire_metrics,
            'threat_assessment': threat_assessment
        }
        
        self._display_results(results)
        return results
    
    def _predict_ros(self, features):
        """Predict Rate of Spread using XGBoost model."""
        # Prepare feature array
        if self.feature_columns:
            # Use specific column order
            feature_array = np.array([[features[col] for col in self.feature_columns]])
        else:
            # Use all features in order
            feature_array = np.array([[
                features['temp_c'],
                features['rel_humidity_pct'],
                features['wind_speed_ms'],
                features['precip_mm'],
                features['vpd_kpa'],
                features['fwi'],
                features['ndvi'],
                features['ndmi'],
                features['lfmc_proxy_pct'],
                features['elevation_m'],
                features['slope_pct'],
                features['aspect_deg']
            ]])
        
        # Scale features if scaler available
        if self.scaler:
            feature_array = self.scaler.transform(feature_array)
        
        # Predict ROS
        ros_prediction = self.model.predict(feature_array)[0]
        ros_prediction = max(0.01, ros_prediction)  # Ensure positive
        
        print(f"🔥 Predicted ROS: {ros_prediction:.4f} m/min")
        return ros_prediction
    
    def _calculate_fire_behavior(self, features, ros_m_min):
        """Calculate comprehensive fire behavior using physics formulas."""
        
        # Extract key variables
        temp_c = features['temp_c']
        humidity_pct = features['rel_humidity_pct']
        wind_ms = features['wind_speed_ms']
        precip_mm = features['precip_mm']
        ndvi = features['ndvi']
        ndmi = features['ndmi']
        slope_pct = features['slope_pct']
        aspect_deg = features['aspect_deg']
        
        # Calculate all fire behavior metrics using your formulas
        print("   Calculating fuel properties...")
        fuel_load = fuel_load_from_ndvi(ndvi)
        fuel_moisture = fuel_moisture_from_ndvi_ndmi(ndvi, ndmi)
        
        print("   Calculating terrain effects...")
        slope_mult = slope_multiplier(slope_pct)
        aspect_fact = aspect_factor(aspect_deg)
        ros_effective = effective_ros(ros_m_min, slope_pct, aspect_deg)
        
        print("   Calculating fire intensity...")
        intensity = byram_intensity_kWm(ros_effective, fuel_load)
        flame_length = flame_length_m(intensity)
        severity_idx = severity_index(flame_length)
        severity_cls = severity_class(flame_length)
        
        print("   Calculating crown fire potential...")
        crown_score = crown_fire_score(intensity, wind_ms, ndvi)
        crown_cls = crown_fire_class(crown_score)
        
        print("   Calculating spotting and spread...")
        spotting_dist = spotting_distance_km(wind_ms, flame_length)
        
        print("   Calculating time and damage estimates...")
        burn_time_5km2 = time_to_burn_window_hours(ros_effective, 5.0)
        damage_estimate = damage_in_window_rs(ros_effective, 50000, 5.0)  # 50k Rs per hectare
        
        print("   Calculating containment difficulty...")
        containment = containment_difficulty(flame_length, slope_pct, 2.0)  # 2km to road
        
        # Expected threat calculation
        occurrence_prob = min(1.0, severity_idx * (crown_score / 100.0))  # Simple occurrence model
        expected_threat_score = expected_threat(occurrence_prob, severity_idx)
        
        fire_metrics = {
            # Basic fire behavior
            'ros_base_m_per_min': ros_m_min,
            'ros_effective_m_per_min': ros_effective,
            'slope_multiplier': slope_mult,
            'aspect_factor': aspect_fact,
            
            # Fuel properties
            'fuel_load_kg_m2': fuel_load,
            'fuel_moisture_pct': fuel_moisture,
            
            # Fire intensity and severity
            'intensity_kW_per_m': intensity,
            'flame_length_m': flame_length,
            'severity_index': severity_idx,
            'severity_class': severity_cls,
            
            # Crown fire
            'crown_fire_score': crown_score,
            'crown_fire_class': crown_cls,
            
            # Spread characteristics
            'spotting_distance_km': spotting_dist,
            
            # Time and impact estimates
            'time_to_burn_5km2_hours': burn_time_5km2,
            'damage_estimate_rs': damage_estimate,
            'containment_difficulty': containment,
            
            # Threat metrics
            'occurrence_probability': occurrence_prob,
            'expected_threat': expected_threat_score
        }
        
        return fire_metrics
    
    def _generate_threat_assessment(self, fire_metrics):
        """Generate overall threat assessment."""
        severity_class = fire_metrics['severity_class']
        crown_class = fire_metrics['crown_fire_class']
        containment = fire_metrics['containment_difficulty']
        expected_threat = fire_metrics['expected_threat']
        
        # Overall threat level
        if expected_threat > 0.7 or severity_class == "Extreme":
            threat_level = "EXTREME"
            threat_color = "🔴"
        elif expected_threat > 0.5 or severity_class == "High":
            threat_level = "HIGH"
            threat_color = "🟠"
        elif expected_threat > 0.3 or severity_class == "Moderate":
            threat_level = "MODERATE"
            threat_color = "🟡"
        else:
            threat_level = "LOW"
            threat_color = "🟢"
        
        # Key concerns
        concerns = []
        if fire_metrics['crown_fire_score'] > 60:
            concerns.append("High crown fire potential")
        if fire_metrics['spotting_distance_km'] > 2:
            concerns.append("Long-range spotting risk")
        if fire_metrics['time_to_burn_5km2_hours'] < 2:
            concerns.append("Rapid fire spread")
        if containment in ["Hard", "Very difficult"]:
            concerns.append("Difficult suppression conditions")
        
        assessment = {
            'threat_level': threat_level,
            'threat_color': threat_color,
            'expected_threat_score': expected_threat,
            'key_concerns': concerns,
            'summary': f"{threat_color} {threat_level} wildfire threat with {severity_class.lower()} severity and {crown_class.lower()} crown fire potential"
        }
        
        return assessment
    
    def _display_results(self, results):
        """Display comprehensive results."""
        print("\n" + "="*60)
        print("🔥 WILDFIRE THREAT ASSESSMENT RESULTS")
        print("="*60)
        
        loc = results['location']
        features = results['live_features']
        ros = results['ros_prediction_m_per_min']
        fire = results['fire_behavior']
        threat = results['threat_assessment']
        
        print(f"📍 Location: {loc['lat']:.4f}, {loc['lon']:.4f}")
        print(f"{threat['threat_color']} Overall Threat: {threat['threat_level']}")
        print(f"📊 Expected Threat Score: {threat['expected_threat_score']:.3f}")
        print()
        
        print("🌡️ ENVIRONMENTAL CONDITIONS:")
        print(f"   Temperature: {features['temp_c']:.1f}°C")
        print(f"   Humidity: {features['rel_humidity_pct']:.1f}%")
        print(f"   Wind Speed: {features['wind_speed_ms']:.1f} m/s")
        print(f"   VPD: {features['vpd_kpa']:.3f} kPa")
        print(f"   Fire Weather Index: {features['fwi']:.2f}")
        print()
        
        print("🌿 VEGETATION & TERRAIN:")
        print(f"   NDVI: {features['ndvi']:.3f}")
        print(f"   Elevation: {features['elevation_m']:.0f}m")
        print(f"   Slope: {features['slope_pct']:.1f}%")
        print(f"   Aspect: {features['aspect_deg']:.1f}°")
        print()
        
        print("🔥 FIRE BEHAVIOR PREDICTION:")
        print(f"   Rate of Spread: {ros:.3f} m/min")
        print(f"   Effective ROS: {fire['ros_effective_m_per_min']:.3f} m/min")
        print(f"   Flame Length: {fire['flame_length_m']:.2f} m")
        print(f"   Fire Intensity: {fire['intensity_kW_per_m']:.0f} kW/m")
        print(f"   Severity: {fire['severity_class']}")
        print()
        
        print("👑 CROWN FIRE ASSESSMENT:")
        print(f"   Crown Fire Score: {fire['crown_fire_score']}/100")
        print(f"   Crown Fire Class: {fire['crown_fire_class']}")
        print()
        
        print("⚡ SPREAD CHARACTERISTICS:")
        print(f"   Spotting Distance: {fire['spotting_distance_km']:.2f} km")
        print(f"   Time to burn 5km²: {fire['time_to_burn_5km2_hours']:.1f} hours")
        print(f"   Containment: {fire['containment_difficulty']}")
        print()
        
        print("💰 IMPACT ESTIMATES:")
        print(f"   Damage (5km²): ₹{fire['damage_estimate_rs']:,.0f}")
        print()
        
        if threat['key_concerns']:
            print("⚠️ KEY CONCERNS:")
            for concern in threat['key_concerns']:
                print(f"   • {concern}")
            print()
        
        print(f"📋 SUMMARY: {threat['summary']}")
        print("="*60)

# Main execution
if __name__ == "__main__":
    # Initialize the system
    predictor = WildfireInferenceSystem()
    
    # Test with Mumbai coordinates (from the file)
    mumbai_lat = 19.05822
    mumbai_lon = 72.87781
    
    # Perform complete wildfire threat prediction
    results = predictor.predict_wildfire_threat(mumbai_lat, mumbai_lon)