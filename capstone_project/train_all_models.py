import os
import sys
import logging
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
import joblib

# Import pipeline components
from pipeline import MLPipeline, PipelineConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('train_models.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelTrainingManager:
    """Manage training of all models in the pipeline."""
    
    def __init__(self, config_path: str = 'config.yaml', data_path: str = 'data.csv'):
        self.config_path = config_path
        self.data_path = data_path
        self.config_manager = PipelineConfig(config_path)
        self.config = self.config_manager.config
        self.pipeline = None
        self.models = {}
        self.metrics = {}
        self.training_history = {}
        logger.info("ModelTrainingManager initialized")
    
    def initialize_pipeline(self):
        """Initialize the ML pipeline."""
        try:
            self.pipeline = MLPipeline(self.config_path)
            logger.info("Pipeline initialized successfully")
            return self.pipeline
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise
    
    def validate_data(self) -> bool:
        """Validate data file exists and is accessible."""
        try:
            if not os.path.exists(self.data_path):
                logger.error(f"Data file not found: {self.data_path}")
                return False
            
            import pandas as pd
            df = pd.read_csv(self.data_path)
            logger.info(f"Data validation successful. Shape: {df.shape}")
            return True
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False
    
    def train(self) -> Tuple[Dict, Dict]:
        """Execute complete training pipeline."""
        try:
            logger.info("=" * 60)
            logger.info("STARTING MODEL TRAINING PROCESS")
            logger.info("=" * 60)
            
            start_time = datetime.now()
            
            # Validate data
            if not self.validate_data():
                raise FileNotFoundError(f"Data file not found: {self.data_path}")
            
            # Initialize pipeline
            self.initialize_pipeline()
            
            # Run pipeline
            logger.info("Running ML pipeline...")
            self.models, self.metrics = self.pipeline.run(self.data_path)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info(f"TRAINING COMPLETED SUCCESSFULLY")
            logger.info(f"Total Duration: {duration:.2f} seconds")
            logger.info("=" * 60)
            
            # Log summary
            self._log_training_summary()
            
            return self.models, self.metrics
        
        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            raise
    
    def save_models(self, save_path: str = './models') -> Dict[str, str]:
        """Save trained models to disk."""
        try:
            os.makedirs(save_path, exist_ok=True)
            logger.info(f"Saving models to {save_path}")
            
            saved_models = {}
            export_format = self.config.get('output', {}).get('export_format', 'joblib')
            
            for model_name, model in self.models.items():
                try:
                    if export_format == 'joblib':
                        model_path = os.path.join(save_path, f"{model_name}.joblib")
                        joblib.dump(model, model_path)
                    elif export_format == 'pickle':
                        model_path = os.path.join(save_path, f"{model_name}.pkl")
                        with open(model_path, 'wb') as f:
                            pickle.dump(model, f)
                    else:
                        model_path = os.path.join(save_path, f"{model_name}.joblib")
                        joblib.dump(model, model_path)
                    
                    saved_models[model_name] = model_path
                    logger.info(f"Model {model_name} saved to {model_path}")
                except Exception as e:
                    logger.error(f"Failed to save model {model_name}: {e}")
            
            return saved_models
        
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            raise
    
    def save_metrics(self, results_path: str = './results') -> str:
        """Save training metrics to file."""
        try:
            os.makedirs(results_path, exist_ok=True)
            logger.info(f"Saving metrics to {results_path}")
            
            metrics_file = os.path.join(results_path, 'metrics.json')
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            logger.info(f"Metrics saved to {metrics_file}")
            return metrics_file
        
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            raise
    
    def save_training_report(self, report_path: str = './results') -> str:
        """Generate and save training report."""
        try:
            os.makedirs(report_path, exist_ok=True)
            logger.info(f"Generating training report in {report_path}")
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'data_file': self.data_path,
                'config_file': self.config_path,
                'models_trained': list(self.models.keys()),
                'metrics': self.metrics,
                'best_model': max(self.metrics, key=lambda x: self.metrics[x]['accuracy']) 
                              if self.metrics else None
            }
            
            report_file = os.path.join(report_path, 'training_report.json')
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Training report saved to {report_file}")
            return report_file
        
        except Exception as e:
            logger.error(f"Error saving training report: {e}")
            raise
    
    def _log_training_summary(self):
        """Log training summary to console and file."""
        logger.info("TRAINING SUMMARY:")
        logger.info(f"  Total Models Trained: {len(self.models)}")
        logger.info("  Model Performance:")
        
        for model_name, metrics in self.metrics.items():
            logger.info(f"    {model_name}:")
            for metric_name, metric_value in metrics.items():
                logger.info(f"      {metric_name}: {metric_value:.4f}")
        
        if self.metrics:
            best_model = max(self.metrics, key=lambda x: self.metrics[x]['accuracy'])
            best_accuracy = self.metrics[best_model]['accuracy']
            logger.info(f"  Best Model: {best_model} (Accuracy: {best_accuracy:.4f})")


def main():
    """Main entry point for model training."""
    try:
        # Get configuration paths
        config_path = 'config.yaml'
        data_path = 'data.csv'
        
        if len(sys.argv) > 1:
            data_path = sys.argv[1]
        if len(sys.argv) > 2:
            config_path = sys.argv[2]
        
        logger.info(f"Data path: {data_path}")
        logger.info(f"Config path: {config_path}")
        
        # Initialize training manager
        trainer = ModelTrainingManager(config_path, data_path)
        
        # Train models
        models, metrics = trainer.train()
        
        # Save outputs
        logger.info("Saving training outputs...")
        trainer.save_models('./models')
        trainer.save_metrics('./results')
        trainer.save_training_report('./results')
        
        logger.info("Model training completed successfully!")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
