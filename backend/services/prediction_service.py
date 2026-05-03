from models.model_loader import ModelLoader
from utils.preprocessor import preprocess_data
import numpy as np

def predict_battery_health(data):
    '''
    Predict battery health based on input data.
    
    Args:
        data: Dictionary containing battery metrics
        
    Returns:
        Dictionary with prediction results
    '''
    try:
        # Preprocess the input data
        processed_data = preprocess_data(data)
        
        # Load the model
        model = ModelLoader.load_model()
        
        # Make prediction
        prediction = model.predict(processed_data)
        
        # Return results
        return {
            'health_score': float(prediction[0]),
            'status': 'healthy' if prediction[0] > 0.7 else 'degraded' if prediction[0] > 0.4 else 'critical'
        }
    except Exception as e:
        raise Exception(f'Prediction error: {str(e)}')
