# dependency_container.py - Dependency Injection Container
import os
from .services.prediction_service import PredictionService
from .services.location_service import LocationService
from .services.file_manager import FileManager
from .repositories.mongo_repository import MongoRepository
from .predict import predict_image  # Your existing prediction function
from .interfaces import IPredictor
from .config import PENDING_FOLDER

class PredictorAdapter(IPredictor):
    """Adapter to make existing predict_image function conform to interface"""
    
    def predict(self, image_path: str):
        return predict_image(image_path)

class DependencyContainer:
    """Container for dependency injection"""
    
    def __init__(self):
        self._instances = {}
    
    def get_location_service(self):
        if 'location_service' not in self._instances:
            self._instances['location_service'] = LocationService()
        return self._instances['location_service']
    
    def get_file_manager(self):
        if 'file_manager' not in self._instances:
            self._instances['file_manager'] = FileManager(PENDING_FOLDER)
        return self._instances['file_manager']
    
    def get_repository(self):
        if 'repository' not in self._instances:
            mongo_uri = os.getenv("MONGO_URI")
            db_name = os.getenv("DB_NAME")
            location_service = self.get_location_service()
            self._instances['repository'] = MongoRepository(mongo_uri, db_name, location_service)
        return self._instances['repository']
    
    def get_predictor(self):
        if 'predictor' not in self._instances:
            self._instances['predictor'] = PredictorAdapter()
        return self._instances['predictor']
    
    def get_prediction_service(self):
        if 'prediction_service' not in self._instances:
            predictor = self.get_predictor()
            file_manager = self.get_file_manager()
            repository = self.get_repository()
            self._instances['prediction_service'] = PredictionService(predictor, file_manager, repository)
        return self._instances['prediction_service']

# Global container instance
container = DependencyContainer()
