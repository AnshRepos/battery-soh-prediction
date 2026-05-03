import os
import json
from src.data_loader import download_and_load_data
from src.preprocessing import preprocess_data
from src.model import build_model
from src.train import train_model
from src.utils import generate_all_plots

# Define the activations to compare
ACTIVATIONS = [
    'tanh',
    'relu',
    'leaky_relu',
    'prelu',
    'elu',
    'swish',
    'mish',
    'gelu',
    'sigmoid'
]

def run_comparison():
    print("--- Starting Battery Activation Function Comparison ---")
    
    # 1. Load Data
    df = download_and_load_data('data/')
    
    # 2. Preprocess Data
    print("Preprocessing data...")
    X_train, X_val, X_test, y_train, y_val, y_test, scaler = preprocess_data(df)
    
    input_dim = X_train.shape[1]
    
    results = {}
    
    # 3. Train all models
    for act in ACTIVATIONS:
        print(f"\n--- Training model with {act} activation ---")
        
        # Build
        model = build_model(act, input_dim)
        
        # Train
        trained_model, history = train_model(
            model=model,
            X_train=X_train, y_train=y_train,
            X_val=X_val, y_val=y_val,
            epochs=50,
            batch_size=32
        )
        
        # Evaluate on Test Set
        print("Evaluating on test set...")
        loss, mae, rmse = trained_model.evaluate(X_test, y_test, verbose=0)
        history['test_metrics'] = {'test_loss': loss, 'test_mae': mae, 'test_rmse': rmse}
        print(f"Test RMSE: {rmse:.4f}")
        
        # Store results
        results[act] = history
        
        # Save model
        if not os.path.exists('models'):
            os.makedirs('models')
        trained_model.save(f'models/model_{act}.h5')
        
    # 4. Generate visual analysis
    print("\nGenerating visualizations...")
    generate_all_plots(results)
    
    # Save raw results dictionary
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)
            
    with open('results/metrics.json', 'w') as f:
        json.dump(results, f, indent=4, cls=NumpyEncoder)
        
    print("\nComparison complete. Check plots/ and results/ directories.")

if __name__ == "__main__":
    run_comparison()
