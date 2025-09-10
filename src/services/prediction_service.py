# prediction_service.py - Single Responsibility: Handle prediction logic
from abc import ABC, abstractmethod
from typing import Dict, Any
import uuid
import os

class PredictionService:
    """Service responsible for handling prediction workflow"""
    
    def __init__(self, predictor, file_manager, repository):
        self.predictor = predictor
        self.file_manager = file_manager
        self.repository = repository
    
    def process_prediction(self, file, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a prediction request"""
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        # Save file temporarily
        temp_path = self.file_manager.save_temp_file(file, unique_filename)
        
        try:
            # Run prediction
            prediction_result = self.predictor.predict(temp_path)
            
            # Read file bytes for storage
            file_bytes = self.file_manager.read_file_bytes(temp_path)
            
            # Save to repository
            save_result = self.repository.save_prediction(
                file_bytes=file_bytes,
                filename=unique_filename,
                prediction=prediction_result["prediction"],
                confidence=prediction_result["confidence"],
                user_data=user_data
            )
            
            return {
                **prediction_result,
                "id": str(save_result["inserted_id"]),
                "location_info": save_result["location_info"]
            }
            
        finally:
            # Clean up temp file if needed
            pass
