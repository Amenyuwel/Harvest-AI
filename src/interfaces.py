# interfaces.py - Interface Segregation: Define clear contracts
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IPredictionRepository(ABC):
    """Interface for prediction data storage"""
    
    @abstractmethod
    def save_prediction(self, file_bytes: bytes, filename: str, 
                       prediction: str, confidence: float, 
                       user_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def update_status(self, report_id: str, status: str, reviewer: str = None):
        pass
    
    @abstractmethod
    def fetch_pending(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def fetch_by_location(self, city: str = None, country: str = None) -> List[Dict[str, Any]]:
        pass

class IPredictor(ABC):
    """Interface for prediction models"""
    
    @abstractmethod
    def predict(self, image_path: str) -> Dict[str, Any]:
        pass

class ILocationService(ABC):
    """Interface for location detection"""
    
    @abstractmethod
    def get_location(self) -> Dict[str, Any]:
        pass

class IFileManager(ABC):
    """Interface for file operations"""
    
    @abstractmethod
    def save_temp_file(self, file, filename: str) -> str:
        pass
    
    @abstractmethod
    def read_file_bytes(self, file_path: str) -> bytes:
        pass

class INotificationService(ABC):
    """Interface for notifications"""
    
    @abstractmethod
    def notify_admin(self, message: str):
        pass
