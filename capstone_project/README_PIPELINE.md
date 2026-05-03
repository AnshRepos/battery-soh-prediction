# ML Pipeline Documentation

## Overview

The ML Pipeline is a comprehensive machine learning framework designed for the Battery Dashboard project. It provides end-to-end orchestration for data preprocessing, model training, evaluation, and deployment.

## Architecture

### Core Components

1. **pipeline.py** - Main pipeline orchestrator
   - PipelineConfig: Configuration management
   - DataProcessor: Data loading and preprocessing
   - ModelTrainer: Model training and evaluation
   - MLPipeline: Main pipeline execution

2. **train_all_models.py** - Training management
   - ModelTrainingManager: Handles the complete training workflow
   - Model persistence
   - Metrics tracking
   - Report generation

3. **export_models.py** - Model export and deployment
   - Model discovery and loading
   - Multi-format export (joblib, pickle)
   - Deployment package creation
   - Export verification

4. **config.yaml** - Pipeline configuration
   - Model configurations
   - Training parameters
   - Data processing settings
   - Logging configuration

## Quick Start

### Installation

`ash
# Install required dependencies
pip install scikit-learn pandas joblib pyyaml

# Navigate to capstone_project directory
cd capstone_project
`

### Basic Usage

#### 1. Configure the Pipeline

Edit config.yaml to customize:
- Model parameters
- Training settings
- Data preprocessing options
- Export formats

`yaml
models:
  RandomForest:
    enabled: true
    params:
      n_estimators: 100
      max_depth: 10
`

#### 2. Train Models

`ash
# Train models with default configuration
python train_all_models.py data.csv config.yaml
`

#### 3. Export Models

`ash
# Export trained models to deployment format
python export_models.py ./models ./exported_models
`

## Detailed Usage

### Pipeline Execution

`python
from pipeline import MLPipeline

# Initialize and run pipeline
pipeline = MLPipeline('config.yaml')
models, metrics = pipeline.run('data.csv')

# Access results
print(f"Trained models: {models.keys()}")
print(f"Model metrics: {metrics}")
`

### Training Management

`python
from train_all_models import ModelTrainingManager

# Create trainer
trainer = ModelTrainingManager('config.yaml', 'data.csv')

# Train models
models, metrics = trainer.train()

# Save outputs
trainer.save_models('./models')
trainer.save_metrics('./results')
trainer.save_training_report('./results')
`

### Model Export

`python
from export_models import ModelExporter

# Create exporter
exporter = ModelExporter('./models', './exported_models')

# Load and export
exporter.load_models()
exporter.create_deployment_package()
exporter.verify_exports('./exported_models/models_deployment')
`

## Configuration Guide

### data Section
`yaml
data:
  train_test_split: 0.2          # Test set percentage
  random_state: 42               # Random seed for reproducibility
  preprocessing:
    handle_missing_values: true  # Fill missing values
    fill_method: 'ffill'         # Forward fill method
    remove_duplicates: true      # Remove duplicate rows
    normalize: false             # Normalize features
    scaler_type: 'standard'      # Scaler type: standard, minmax, robust
`

### models Section
`yaml
models:
  ModelName:
    enabled: true                # Enable/disable model
    class: ModelClassName        # Model class name
    params:                       # Model-specific parameters
      param1: value1
      param2: value2
    description: "Description"   # Model description
`

Supported Models:
- LogisticRegression: Linear classification
- RandomForest: Ensemble tree-based model
- SVM: Support Vector Machine
- GradientBoosting: Gradient boosting classifier

### training Section
`yaml
training:
  epochs: 10                     # Number of training epochs
  batch_size: 32                 # Batch size
  validation_split: 0.1          # Validation split ratio
  early_stopping: true           # Use early stopping
  early_stopping_patience: 5     # Patience for early stopping
`

### evaluation Section
`yaml
evaluation:
  metrics:                       # Metrics to compute
    - accuracy
    - precision
    - recall
    - f1_score
    - roc_auc
  cross_validation_folds: 5      # Cross-validation folds
`

### output Section
`yaml
output:
  model_save_path: ./models      # Model save directory
  results_path: ./results        # Results directory
  log_path: ./logs               # Log directory
  export_format: 'joblib'        # Export format: joblib, pickle, onnx
`

## Data Format

### Expected Input Format
The pipeline expects data in CSV format with the following structure:

`csv
feature1,feature2,feature3,...,target
value1,value2,value3,...,target_value
...
`

### Data Requirements
- All features should be numeric
- Target column should be named 'target' or be the last column
- No missing values (unless preprocessing is enabled)
- Consistent data types across rows

## Logging

### Log Files
- pipeline.log - Main pipeline execution logs
- 	rain_models.log - Training process logs
- xport_models.log - Model export logs

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Configuration
`yaml
logging:
  level: INFO                    # Log level
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  console_output: true           # Output to console
  max_file_size: 10485760        # Max log file size (10MB)
  backup_count: 5                # Number of backup logs
`

## Directory Structure

`
capstone_project/
├── pipeline.py                 # Main pipeline orchestrator
├── train_all_models.py         # Training script
├── export_models.py            # Export script
├── config.yaml                 # Configuration file
├── README_PIPELINE.md          # This file
├── models/                     # Trained models directory
│   ├── LogisticRegression.joblib
│   ├── RandomForest.joblib
│   ├── SVM.joblib
│   └── GradientBoosting.joblib
├── results/                    # Results and metrics
│   ├── metrics.json
│   └── training_report.json
├── exported_models/            # Exported models for deployment
│   └── models_deployment/
│       ├── joblib/
│       ├── pickle/
│       ├── EXPORT_MANIFEST.json
│       └── README.md
└── logs/                       # Log files
    ├── pipeline.log
    ├── train_models.log
    └── export_models.log
`

## Error Handling

The pipeline includes comprehensive error handling:

### Data Validation
- File existence checks
- Data format validation
- Shape and type consistency

### Model Training
- Exception handling for failed models
- Graceful fallback mechanisms
- Detailed error logging

### Export Process
- File I/O error handling
- Verification of exported files
- Integrity checks

## Performance Optimization

### Strategies
1. **Parallel Processing**: Use 
_jobs=-1 for multi-core processing
2. **Early Stopping**: Stop training when validation metrics plateau
3. **Feature Selection**: Reduce dimensionality
4. **Model Caching**: Cache trained models to disk

### Configuration
`yaml
advanced:
  use_gpu: false                 # Enable GPU acceleration
  distributed_training: false    # Distributed training
  model_versioning: true         # Version models
  experiment_tracking: true      # Track experiments
`

## Troubleshooting

### Common Issues

#### 1. FileNotFoundError: Data file not found
`
Solution: Ensure data.csv exists in the same directory or provide full path
`

#### 2. ImportError: No module named 'pipeline'
`
Solution: Ensure you're running from the capstone_project directory
`

#### 3. YAML parsing error
`
Solution: Check config.yaml syntax and indentation
`

#### 4. Memory error during training
`
Solution: Reduce batch_size or n_estimators in config.yaml
`

### Debug Mode
`python
import logging
logging.basicConfig(level=logging.DEBUG)
`

## Advanced Features

### Hyperparameter Tuning
`yaml
hyperparameter_tuning:
  enabled: true
  method: 'grid'      # grid, random, bayesian
  cv_folds: 5
  n_trials: 100
`

### Model Versioning
Models are automatically versioned with timestamps:
`
model_name_YYYYMMDD_HHMMSS.joblib
`

### Experiment Tracking
Enable tracking to log all experiments:
`yaml
advanced:
  experiment_tracking: true
`

## Integration Examples

### Flask Web Application
`python
import joblib
from flask import Flask, request

app = Flask(__name__)
model = joblib.load('./models/RandomForest.joblib')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    prediction = model.predict([data['features']])
    return {'prediction': prediction[0]}
`

### FastAPI
`python
from fastapi import FastAPI
import joblib

app = FastAPI()
model = joblib.load('./models/RandomForest.joblib')

@app.post('/predict')
async def predict(data: dict):
    return {'prediction': model.predict([data['features']])[0]}
`

## Best Practices

1. **Version Control**: Keep config.yaml in version control
2. **Data Validation**: Always validate data before training
3. **Monitoring**: Monitor model performance over time
4. **Documentation**: Update config.yaml comments
5. **Testing**: Test with sample data before production
6. **Logging**: Enable logging for debugging
7. **Backups**: Backup trained models regularly

## API Reference

### MLPipeline

`python
class MLPipeline:
    def __init__(self, config_path: str = 'config.yaml')
    def run(self, data_path: str) -> Tuple[Dict, Dict]
`

### ModelTrainingManager

`python
class ModelTrainingManager:
    def __init__(self, config_path: str, data_path: str)
    def train(self) -> Tuple[Dict, Dict]
    def save_models(self, save_path: str) -> Dict[str, str]
    def save_metrics(self, results_path: str) -> str
    def save_training_report(self, report_path: str) -> str
`

### ModelExporter

`python
class ModelExporter:
    def __init__(self, models_path: str, export_path: str)
    def load_models(self) -> Dict[str, Any]
    def export_to_joblib(self, output_path: str = None) -> Dict[str, str]
    def export_to_pickle(self, output_path: str = None) -> Dict[str, str]
    def create_deployment_package(self, package_name: str) -> str
    def verify_exports(self, package_path: str) -> Dict[str, bool]
`

## Support and Contribution

For issues or contributions, please:
1. Check the troubleshooting section
2. Review log files for error details
3. Consult the API reference
4. Contact the development team

## License

This pipeline is part of the Battery Dashboard project.

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready
