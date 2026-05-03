import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineConfig:
    """Load and manage pipeline configuration."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        logger.info(f"Pipeline configuration loaded from {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.config.get(key, default)


class DataProcessor:
    """Handle data loading and preprocessing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data = None
        logger.info("DataProcessor initialized")
    
    def load_data(self, data_path: str):
        """Load data from file."""
        try:
            import pandas as pd
            self.data = pd.read_csv(data_path)
            logger.info(f"Data loaded successfully from {data_path}. Shape: {self.data.shape}")
            return self.data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def preprocess(self):
        """Apply preprocessing steps."""
        if self.data is None:
            logger.error("No data loaded")
            raise ValueError("Data not loaded. Call load_data() first")
        
        try:
            # Handle missing values
            self.data.fillna(method='ffill', inplace=True)
            logger.info("Missing values handled")
            
            # Remove duplicates
            initial_rows = len(self.data)
            self.data.drop_duplicates(inplace=True)
            logger.info(f"Duplicates removed: {initial_rows - len(self.data)} rows")
            
            return self.data
        except Exception as e:
            logger.error(f"Error during preprocessing: {e}")
            raise


class ModelTrainer:
    """Handle model training orchestration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self.metrics = {}
        logger.info("ModelTrainer initialized")
    
    def train_model(self, model_name: str, X_train, y_train, model_class, params: Dict = None):
        """Train a single model."""
        try:
            logger.info(f"Training model: {model_name}")
            
            if params is None:
                params = {}
            
            model = model_class(**params)
            model.fit(X_train, y_train)
            
            self.models[model_name] = model
            logger.info(f"Model {model_name} trained successfully")
            
            return model
        except Exception as e:
            logger.error(f"Error training model {model_name}: {e}")
            raise
    
    def evaluate_model(self, model_name: str, X_test, y_test):
        """Evaluate model performance."""
        try:
            if model_name not in self.models:
                logger.error(f"Model {model_name} not found in trained models")
                raise ValueError(f"Model {model_name} not trained")
            
            model = self.models[model_name]
            score = model.score(X_test, y_test)
            
            self.metrics[model_name] = {'accuracy': score}
            logger.info(f"Model {model_name} evaluation - Accuracy: {score:.4f}")
            
            return score
        except Exception as e:
            logger.error(f"Error evaluating model {model_name}: {e}")
            raise
    
    def get_best_model(self) -> Optional[str]:
        """Get the best performing model."""
        if not self.metrics:
            logger.warning("No metrics available")
            return None
        
        best_model = max(self.metrics, key=lambda x: self.metrics[x]['accuracy'])
        logger.info(f"Best model: {best_model} with accuracy {self.metrics[best_model]['accuracy']:.4f}")
        return best_model


class MLPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_manager = PipelineConfig(config_path)
        self.config = self.config_manager.config
        self.data_processor = DataProcessor(self.config)
        self.model_trainer = ModelTrainer(self.config)
        self.pipeline_start_time = datetime.now()
        logger.info("MLPipeline initialized")
    
    def run(self, data_path: str):
        """Execute the complete pipeline."""
        try:
            logger.info("Starting ML Pipeline execution")
            logger.info(f"Pipeline start time: {self.pipeline_start_time}")
            
            # Step 1: Load and preprocess data
            logger.info("=" * 50)
            logger.info("STEP 1: Data Loading and Preprocessing")
            logger.info("=" * 50)
            self.data_processor.load_data(data_path)
            self.data_processor.preprocess()
            
            # Step 2: Prepare training/test split
            logger.info("=" * 50)
            logger.info("STEP 2: Train-Test Split")
            logger.info("=" * 50)
            from sklearn.model_selection import train_test_split
            
            X = self.data_processor.data.drop('target', axis=1, errors='ignore')
            y = self.data_processor.data.get('target', None)
            
            if y is None:
                logger.warning("No target column found. Using first numeric column as target.")
                y = self.data_processor.data.iloc[:, -1]
            
            test_size = self.config.get('train_test_split', 0.2)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            logger.info(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
            
            # Step 3: Train models
            logger.info("=" * 50)
            logger.info("STEP 3: Model Training")
            logger.info("=" * 50)
            self._train_all_models(X_train, y_train)
            
            # Step 4: Evaluate models
            logger.info("=" * 50)
            logger.info("STEP 4: Model Evaluation")
            logger.info("=" * 50)
            self._evaluate_all_models(X_test, y_test)
            
            # Step 5: Summary
            logger.info("=" * 50)
            logger.info("STEP 5: Pipeline Summary")
            logger.info("=" * 50)
            self._print_summary()
            
            pipeline_end_time = datetime.now()
            duration = (pipeline_end_time - self.pipeline_start_time).total_seconds()
            logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
            
            return self.model_trainer.models, self.model_trainer.metrics
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            raise
    
    def _train_all_models(self, X_train, y_train):
        """Train all configured models."""
        models_config = self.config.get('models', {})
        
        for model_name, model_config in models_config.items():
            try:
                logger.info(f"Training {model_name}...")
                model_class_name = model_config.get('class', model_name)
                params = model_config.get('params', {})
                
                # Import and train model
                if model_class_name == 'LogisticRegression':
                    from sklearn.linear_model import LogisticRegression
                    self.model_trainer.train_model(model_name, X_train, y_train, LogisticRegression, params)
                elif model_class_name == 'RandomForest':
                    from sklearn.ensemble import RandomForestClassifier
                    self.model_trainer.train_model(model_name, X_train, y_train, RandomForestClassifier, params)
                elif model_class_name == 'SVM':
                    from sklearn.svm import SVC
                    self.model_trainer.train_model(model_name, X_train, y_train, SVC, params)
                elif model_class_name == 'GradientBoosting':
                    from sklearn.ensemble import GradientBoostingClassifier
                    self.model_trainer.train_model(model_name, X_train, y_train, GradientBoostingClassifier, params)
                else:
                    logger.warning(f"Unknown model class: {model_class_name}")
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
    
    def _evaluate_all_models(self, X_test, y_test):
        """Evaluate all trained models."""
        for model_name in self.model_trainer.models:
            try:
                self.model_trainer.evaluate_model(model_name, X_test, y_test)
            except Exception as e:
                logger.error(f"Failed to evaluate {model_name}: {e}")
    
    def _print_summary(self):
        """Print pipeline summary."""
        logger.info("Training Summary:")
        logger.info(f"  Total models trained: {len(self.model_trainer.models)}")
        logger.info("  Model Performance:")
        for model_name, metrics in self.model_trainer.metrics.items():
            logger.info(f"    {model_name}: {metrics}")
        
        best_model = self.model_trainer.get_best_model()
        if best_model:
            logger.info(f"  Best Model: {best_model}")


def main():
    """Main entry point."""
    try:
        pipeline = MLPipeline('config.yaml')
        
        # Check if data path is provided
        data_path = 'data.csv'  # Default path
        if len(sys.argv) > 1:
            data_path = sys.argv[1]
        
        if not os.path.exists(data_path):
            logger.error(f"Data file not found: {data_path}")
            sys.exit(1)
        
        models, metrics = pipeline.run(data_path)
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
