import numpy as np
from sklearn.preprocessing import StandardScaler

def preprocess_data(data):
    '''
    Preprocess input data for model prediction.
    
    Args:
        data: Dictionary or array of raw battery metrics
        
    Returns:
        Processed numpy array ready for model prediction
    '''
    try:
        # Convert dictionary to feature vector if needed
        if isinstance(data, dict):
            features = [
                data.get('voltage', 0),
                data.get('current', 0),
                data.get('temperature', 20),
                data.get('charge_percent', 50),
                data.get('charge_cycles', 0),
                data.get('capacity', 100)
            ]
        else:
            features = list(data)
        
        # Convert to numpy array
        features = np.array(features, dtype=np.float32).reshape(1, -1)
        
        # Optional: Apply scaling if needed
        # scaler = StandardScaler()
        # features = scaler.fit_transform(features)
        
        return features
    except Exception as e:
        raise Exception(f'Preprocessing error: {str(e)}')

def validate_input(data):
    '''
    Validate input data for required fields.
    
    Args:
        data: Dictionary containing battery metrics
        
    Returns:
        Boolean indicating if data is valid
    '''
    required_fields = ['voltage', 'current', 'temperature']
    
    if isinstance(data, dict):
        return all(field in data for field in required_fields)
    
    return False

def normalize_features(features, min_val=0, max_val=100):
    '''
    Normalize features to a specified range.
    
    Args:
        features: Input features as numpy array
        min_val: Minimum value for normalization
        max_val: Maximum value for normalization
        
    Returns:
        Normalized features
    '''
    return (features - min_val) / (max_val - min_val)
