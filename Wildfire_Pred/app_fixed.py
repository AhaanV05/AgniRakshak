from flask import Flask, request, jsonify, send_from_directory
from simple_predict import WildfirePredictor
import os
import numpy as np

# Serve static files from parent directory (Wildfire_Frontend)
app = Flask(__name__, static_folder='..', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('..', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('..', filename)

# Read Aeris credentials and model path from environment variables
AERIS_CLIENT_ID = os.getenv('AERIS_CLIENT_ID')
AERIS_CLIENT_SECRET = os.getenv('AERIS_CLIENT_SECRET')
MODEL_PATH = os.getenv('WILDFIRE_MODEL_PATH', 'wildfire_xgboost_model.json')

predictor = WildfirePredictor(AERIS_CLIENT_ID, AERIS_CLIENT_SECRET, MODEL_PATH)

def convert_numpy_types(obj):
    """
    Recursively convert NumPy types to Python native types for JSON serialization
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

@app.route('/predict', methods=['GET'])
def predict_route():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if lat is None or lon is None:
        return jsonify({'error': 'Missing lat or lon parameters'}), 400
    try:
        latf = float(lat)
        lonf = float(lon)
    except ValueError:
        return jsonify({'error': 'Invalid lat or lon values'}), 400

    result = predictor.predict_dict(latf, lonf)
    return jsonify(result)

@app.route('/analyze-threat', methods=['GET'])
def analyze_threat_route():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if lat is None or lon is None:
        return jsonify({'error': 'Missing lat or lon parameters'}), 400
    try:
        latf = float(lat)
        lonf = float(lon)
    except ValueError:
        return jsonify({'error': 'Invalid lat or lon values'}), 400

    # Import and use the real comprehensive wildfire inference system
    try:
        import sys
        import os
        from datetime import datetime
        
        # Add the Threat_Predictor directory to the Python path
        threat_predictor_path = os.path.join(os.path.dirname(__file__), '..', 'Threat_Predictor')
        if threat_predictor_path not in sys.path:
            sys.path.insert(0, threat_predictor_path)
        
        # Import the real wildfire inference system
        from wildfire_inference_system import WildfireInferenceSystem
        
        print(f"🔥 Initializing comprehensive threat analysis for ({latf}, {lonf})")
        
        # Initialize the comprehensive threat analysis system
        threat_system = WildfireInferenceSystem()
        
        # Run comprehensive threat prediction
        result = threat_system.predict_wildfire_threat(latf, lonf)
        
        # Convert NumPy types to Python native types for JSON serialization
        result = convert_numpy_types(result)
        
        print(f"✅ Threat analysis completed successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Threat analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Get basic prediction as fallback
        basic_prediction = predictor.predict_dict(latf, lonf)
        
        return jsonify({
            'error': f'Comprehensive threat analysis failed: {str(e)}',
            'timestamp': basic_prediction.get('timestamp', datetime.now().isoformat()),
            'fallback_data': basic_prediction
        }), 500

if __name__ == '__main__':
    # For local dev only. In production, run behind a proper WSGI server.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=True)