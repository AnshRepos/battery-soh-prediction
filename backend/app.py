from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from services.prediction_service import predict_battery_health
from services.metrics_service import get_metrics

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        prediction = predict_battery_health(data)
        return jsonify({'prediction': prediction}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/metrics', methods=['GET'])
def metrics():
    try:
        metrics_data = get_metrics()
        return jsonify(metrics_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
