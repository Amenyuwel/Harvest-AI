# mongo_repository.py - Dependency Inversion: Implement interface
from datetime import datetime
from pymongo import MongoClient
from gridfs import GridFS
import os
from typing import Dict, Any, List
from ..interfaces import IPredictionRepository, ILocationService

class MongoRepository(IPredictionRepository):
    """MongoDB implementation of prediction repository"""
    
    def __init__(self, connection_string: str, database_name: str, location_service: ILocationService):
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db["reports"]
        self.fs = GridFS(self.db)
        self.location_service = location_service
    
    def save_prediction(self, file_bytes: bytes, filename: str, 
                       prediction: str, confidence: float, 
                       user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save prediction with metadata"""
        # Store file in GridFS
        file_id = self.fs.put(file_bytes, filename=filename)
        
        # Get location metadata
        location_info = self.location_service.get_location()
        
        # Build document
        doc = {
            "file_id": file_id,
            "filename": filename,
            "prediction": prediction,
            "confidence": float(confidence),
            "status": "pending",
            "reviewed_by": None,
            "timestamp": datetime.utcnow(),
            "location_info": location_info
        }
        
        if user_data:
            doc.update(user_data)
        
        result = self.collection.insert_one(doc)
        
        return {
            "inserted_id": result.inserted_id,
            "location_info": location_info
        }
    
    def update_status(self, report_id: str, status: str, reviewer: str = None):
        """Update prediction status"""
        self.collection.update_one(
            {"_id": report_id},
            {"$set": {"status": status, "reviewed_by": reviewer}}
        )
    
    def fetch_pending(self) -> List[Dict[str, Any]]:
        """Fetch pending predictions"""
        return list(self.collection.find({"status": "pending"}))
    
    def fetch_by_location(self, city: str = None, country: str = None) -> List[Dict[str, Any]]:
        """Fetch predictions by location"""
        query = {}
        if city:
            query['location_info.city'] = city
        if country:
            query['location_info.country'] = country
        
        return list(self.collection.find(query))
    
    def update_status_by_filename(self, filename: str, status: str, label: str = None):
        """Update status by filename (for admin approval)"""
        update_data = {"status": status, "reviewed_at": datetime.utcnow()}
        if label:
            update_data["approved_class"] = label
            
        self.collection.update_one(
            {"filename": filename},
            {"$set": update_data}
        )
