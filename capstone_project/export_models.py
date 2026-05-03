import os
import sys
import logging
import json
import joblib
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('export_models.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelExporter:
    """Export and manage trained models."""
    
    def __init__(self, models_path: str = './models', export_path: str = './exported_models'):
        self.models_path = models_path
        self.export_path = export_path
        self.models = {}
        self.export_manifest = {}
        logger.info("ModelExporter initialized")
    
    def discover_models(self) -> List[str]:
        """Discover trained models in models directory."""
        try:
            if not os.path.exists(self.models_path):
                logger.warning(f"Models directory not found: {self.models_path}")
                return []
            
            model_files = []
            for file in os.listdir(self.models_path):
                if file.endswith(('.joblib', '.pkl', '.pickle')):
                    model_files.append(file)
            
            logger.info(f"Discovered {len(model_files)} models: {model_files}")
            return model_files
        
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return []
    
    def load_models(self) -> Dict[str, Any]:
        """Load all trained models from disk."""
        try:
            model_files = self.discover_models()
            
            for model_file in model_files:
                try:
                    model_path = os.path.join(self.models_path, model_file)
                    model_name = model_file.rsplit('.', 1)[0]
                    
                    if model_file.endswith('.joblib'):
                        model = joblib.load(model_path)
                    else:
                        with open(model_path, 'rb') as f:
                            model = pickle.load(f)
                    
                    self.models[model_name] = model
                    logger.info(f"Loaded model: {model_name} from {model_path}")
                
                except Exception as e:
                    logger.error(f"Failed to load model {model_file}: {e}")
            
            logger.info(f"Total models loaded: {len(self.models)}")
            return self.models
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def export_to_joblib(self, output_path: str = None) -> Dict[str, str]:
        """Export models in joblib format."""
        try:
            output_path = output_path or os.path.join(self.export_path, 'joblib')
            os.makedirs(output_path, exist_ok=True)
            
            logger.info(f"Exporting models to joblib format in {output_path}")
            exported = {}
            
            for model_name, model in self.models.items():
                try:
                    export_file = os.path.join(output_path, f"{model_name}.joblib")
                    joblib.dump(model, export_file)
                    exported[model_name] = export_file
                    logger.info(f"Exported {model_name} to {export_file}")
                except Exception as e:
                    logger.error(f"Failed to export {model_name}: {e}")
            
            return exported
        
        except Exception as e:
            logger.error(f"Error exporting to joblib: {e}")
            raise
    
    def export_to_pickle(self, output_path: str = None) -> Dict[str, str]:
        """Export models in pickle format."""
        try:
            output_path = output_path or os.path.join(self.export_path, 'pickle')
            os.makedirs(output_path, exist_ok=True)
            
            logger.info(f"Exporting models to pickle format in {output_path}")
            exported = {}
            
            for model_name, model in self.models.items():
                try:
                    export_file = os.path.join(output_path, f"{model_name}.pkl")
                    with open(export_file, 'wb') as f:
                        pickle.dump(model, f)
                    exported[model_name] = export_file
                    logger.info(f"Exported {model_name} to {export_file}")
                except Exception as e:
                    logger.error(f"Failed to export {model_name}: {e}")
            
            return exported
        
        except Exception as e:
            logger.error(f"Error exporting to pickle: {e}")
            raise
    
    def generate_model_metadata(self) -> Dict[str, Any]:
        """Generate metadata for exported models."""
        try:
            metadata = {
                'export_timestamp': datetime.now().isoformat(),
                'total_models': len(self.models),
                'models': {}
            }
            
            for model_name, model in self.models.items():
                metadata['models'][model_name] = {
                    'type': type(model).__name__,
                    'class': f"{type(model).__module__}.{type(model).__name__}",
                    'size_bytes': 0  # Can be calculated from saved file
                }
            
            logger.info("Model metadata generated")
            return metadata
        
        except Exception as e:
            logger.error(f"Error generating metadata: {e}")
            raise
    
    def save_export_manifest(self, output_path: str = None) -> str:
        """Save export manifest with model information."""
        try:
            output_path = output_path or self.export_path
            os.makedirs(output_path, exist_ok=True)
            
            manifest = {
                'timestamp': datetime.now().isoformat(),
                'models_directory': self.models_path,
                'export_directory': self.export_path,
                'total_models_exported': len(self.models),
                'model_metadata': self.generate_model_metadata(),
                'export_formats': ['joblib', 'pickle']
            }
            
            manifest_file = os.path.join(output_path, 'EXPORT_MANIFEST.json')
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Export manifest saved to {manifest_file}")
            return manifest_file
        
        except Exception as e:
            logger.error(f"Error saving export manifest: {e}")
            raise
    
    def create_deployment_package(self, package_name: str = 'models_deployment') -> str:
        """Create a deployment package with all exported models."""
        try:
            package_path = os.path.join(self.export_path, package_name)
            os.makedirs(package_path, exist_ok=True)
            
            logger.info(f"Creating deployment package at {package_path}")
            
            # Export models in multiple formats
            joblib_exports = self.export_to_joblib(os.path.join(package_path, 'joblib'))
            pickle_exports = self.export_to_pickle(os.path.join(package_path, 'pickle'))
            
            # Save metadata
            self.save_export_manifest(package_path)
            
            # Create README
            readme_content = self._generate_deployment_readme()
            readme_path = os.path.join(package_path, 'README.md')
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            
            logger.info(f"Deployment package created successfully at {package_path}")
            return package_path
        
        except Exception as e:
            logger.error(f"Error creating deployment package: {e}")
            raise
    
    def _generate_deployment_readme(self) -> str:
        """Generate README for deployment package."""
        return f"""# Model Deployment Package

## Overview
This package contains trained ML models ready for deployment.

## Models Included
{chr(10).join([f"- {name} ({type(model).__name__})" for name, model in self.models.items()])}

## Directory Structure
`
models_deployment/
├── joblib/          # Models in joblib format
├── pickle/          # Models in pickle format
├── EXPORT_MANIFEST.json
└── README.md
`

## Usage

### Loading Models (Python)
`python
import joblib

# Load a model
model = joblib.load('joblib/model_name.joblib')

# Make predictions
predictions = model.predict(X_test)
`

### Model Information
- **Export Date**: {datetime.now().isoformat()}
- **Total Models**: {len(self.models)}
- **Supported Formats**: joblib, pickle

## Integration Guide
1. Load the model using joblib or pickle
2. Ensure input data matches the training data format
3. Use the model for predictions

## Troubleshooting
- Ensure all dependencies are installed (scikit-learn, joblib)
- Check that input features match the model's expected shape
- Verify the model file is not corrupted

For more information, see EXPORT_MANIFEST.json
"""
    
    def verify_exports(self, package_path: str) -> Dict[str, bool]:
        """Verify that all exports are valid."""
        try:
            logger.info(f"Verifying exports in {package_path}")
            verification_results = {}
            
            for format_dir in ['joblib', 'pickle']:
                format_path = os.path.join(package_path, format_dir)
                if os.path.exists(format_path):
                    for model_file in os.listdir(format_path):
                        try:
                            model_path = os.path.join(format_path, model_file)
                            if format_dir == 'joblib':
                                _ = joblib.load(model_path)
                            else:
                                with open(model_path, 'rb') as f:
                                    _ = pickle.load(f)
                            verification_results[f"{format_dir}/{model_file}"] = True
                            logger.info(f"Verified {format_dir}/{model_file}")
                        except Exception as e:
                            logger.error(f"Verification failed for {model_file}: {e}")
                            verification_results[f"{format_dir}/{model_file}"] = False
            
            return verification_results
        
        except Exception as e:
            logger.error(f"Error verifying exports: {e}")
            raise


def main():
    """Main entry point for model export."""
    try:
        models_path = './models'
        export_path = './exported_models'
        
        if len(sys.argv) > 1:
            models_path = sys.argv[1]
        if len(sys.argv) > 2:
            export_path = sys.argv[2]
        
        logger.info("=" * 60)
        logger.info("STARTING MODEL EXPORT PROCESS")
        logger.info("=" * 60)
        logger.info(f"Models directory: {models_path}")
        logger.info(f"Export directory: {export_path}")
        
        # Initialize exporter
        exporter = ModelExporter(models_path, export_path)
        
        # Load models
        models = exporter.load_models()
        if not models:
            logger.warning("No models found to export")
            sys.exit(0)
        
        # Create deployment package
        package_path = exporter.create_deployment_package()
        
        # Verify exports
        logger.info("Verifying exports...")
        verification = exporter.verify_exports(package_path)
        
        # Log summary
        logger.info("=" * 60)
        logger.info("EXPORT COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Deployment package location: {package_path}")
        logger.info(f"Total models exported: {len(models)}")
        logger.info(f"Verification results: {sum(1 for v in verification.values() if v)}/{len(verification)} passed")
        
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
