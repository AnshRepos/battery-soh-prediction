import pickle
import os
from config import Config

class ModelLoader:
    _model = None
    
    @staticmethod
    def load_model():
        '''Load the battery health prediction model from disk.'''
        if ModelLoader._model is None:
            model_path = Config.MODEL_PATH
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    ModelLoader._model = pickle.load(f)
            else:
                raise FileNotFoundError(f'Model not found at {model_path}')
        return ModelLoader._model
    
    @staticmethod
    def reload_model():
        '''Reload the model from disk.'''
        ModelLoader._model = None
        return ModelLoader.load_model()
