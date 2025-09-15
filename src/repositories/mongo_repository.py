# mongo_repository.py - Dependency Inversion: Implement interface
from datetime import datetime
from pymongo import MongoClient
import os
import uuid
import shutil
from typing import Dict, Any, List
from ..interfaces import IPredictionRepository, ILocationService

class MongoRepository(IPredictionRepository):
    """MongoDB implementation of prediction repository with file system storage"""
    
    def __init__(self, connection_string: str, database_name: str, location_service: ILocationService):
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db["reports"]
        self.location_service = location_service
        
        # Create file storage directories
        self.storage_dir = os.path.join("storage", "images")
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_prediction(self, file_bytes: bytes, filename: str, 
                       prediction: str, confidence: float, 
                       user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save prediction with file system storage"""
        # Generate unique filename to avoid conflicts
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        # Save file to disk
        file_path = os.path.join(self.storage_dir, unique_filename)
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        # Get location metadata
        location_info = self.location_service.get_location()
        
        # Generate unique classification ID
        classification_id = str(uuid.uuid4())
        
        # Build document (store file path instead of GridFS file_id)
        doc = {
            "classificationId": classification_id,  # Add missing classificationId
            "filename": filename,
            "stored_filename": unique_filename,
            "file_path": file_path,
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
            "location_info": location_info,
            "file_path": file_path
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
            {"stored_filename": filename},  # Use stored_filename instead of filename
            {"$set": update_data}
        )
    
    def get_file_by_id(self, prediction_id: str) -> bytes:
        """Retrieve file from disk by prediction ID"""
        from bson import ObjectId
        doc = self.collection.find_one({"_id": ObjectId(prediction_id)})
        if doc and 'file_path' in doc and os.path.exists(doc['file_path']):
            with open(doc['file_path'], 'rb') as f:
                return f.read()
        return None
    
    def get_file_by_stored_filename(self, stored_filename: str) -> bytes:
        """Retrieve file from disk by stored filename"""
        doc = self.collection.find_one({"stored_filename": stored_filename})
        if doc and 'file_path' in doc and os.path.exists(doc['file_path']):
            with open(doc['file_path'], 'rb') as f:
                return f.read()
        return None
    
    def delete_file(self, prediction_id: str) -> bool:
        """Delete file from disk and remove document"""
        from bson import ObjectId
        doc = self.collection.find_one({"_id": ObjectId(prediction_id)})
        if doc:
            # Delete file from disk
            if 'file_path' in doc and os.path.exists(doc['file_path']):
                try:
                    os.remove(doc['file_path'])
                except OSError:
                    pass  # File might already be deleted
            
            # Delete document from MongoDB
            result = self.collection.delete_one({"_id": ObjectId(prediction_id)})
            return result.deleted_count > 0
        return False
