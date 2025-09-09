# mongo.py
from pymongo import MongoClient
from gridfs import GridFS
import os

# Load from environment variables for security
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
images_collection = db["images"]       # stores metadata (prediction, status, etc.)
fs = GridFS(db)                        # stores the actual image files

def save_prediction(file_bytes, filename, prediction, confidence):
    """
    Save image and prediction result to MongoDB.
    :param file_bytes: Raw image bytes
    :param filename: Original filename
    :param prediction: Model predicted label
    :param confidence: Confidence score
    """
    # Store the actual file in GridFS
    file_id = fs.put(file_bytes, filename=filename)

    # Insert metadata into images_collection
    result = images_collection.insert_one({
        "file_id": file_id,
        "filename": filename,
        "prediction": prediction,
        "confidence": float(confidence),
        "status": "pending",   # default until admin review
        "reviewed_by": None,
        "timestamp": db.client.server_info()["localTime"]
    })

    return result.inserted_id


def update_status(image_id, status, reviewer=None):
    """
    Update the review status of an image.
    :param image_id: MongoDB document ID
    :param status: "approved" | "rejected" | "archived"
    :param reviewer: Admin username/email
    """
    images_collection.update_one(
        {"_id": image_id},
        {"$set": {"status": status, "reviewed_by": reviewer}}
    )


def fetch_pending():
    """
    Fetch all pending images for admin review.
    """
    return list(images_collection.find({"status": "pending"}))
