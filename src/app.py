import os
import uuid
import shutil
from datetime import datetime
from flask import Flask, request, jsonify
from predict import predict_image
from config import UPLOAD_FOLDER, CLASS_NAMES
from logger import logger
from notifier import Notifier

# ✅ Load environment variables from parent directory
from dotenv import load_dotenv
# Load .env from the parent directory (root of project)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ✅ MongoDB
from pymongo import MongoClient
from bson import ObjectId

# -------------------------
# DB Setup
# -------------------------
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise ValueError("Missing environment variables. Please check your .env file.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
images_collection = db["images"]

# -------------------------
# Folders
# -------------------------
PENDING_FOLDER = os.path.join(UPLOAD_FOLDER, "pending")
APPROVED_FOLDER = os.path.join(UPLOAD_FOLDER, "approved")
REJECTED_FOLDER = os.path.join(UPLOAD_FOLDER, "rejected")

for folder in [PENDING_FOLDER, APPROVED_FOLDER, REJECTED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Make sure each class folder exists under "approved"
for cls in CLASS_NAMES + ["unknown"]:
    os.makedirs(os.path.join(APPROVED_FOLDER, cls), exist_ok=True)

# -------------------------
# App + Notifier
# -------------------------
app = Flask(__name__)
notifier = Notifier()

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Harvest Assistant Model Service is running"})

@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Get RSBSA number from form data (optional)
    rsbsa_number = request.form.get("rsbsaNumber", "anonymous")

    try:
        # Save uploaded file
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(PENDING_FOLDER, unique_filename)
        file.save(file_path)

        # Run prediction
        result = predict_image(file_path)

        # Save record to MongoDB with RSBSA number
        doc = {
            "filename": unique_filename,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "rsbsaNumber": rsbsa_number,  # Store the user's RSBSA
            "status": "pending",   # waiting for admin review
            "timestamp": datetime.utcnow()
        }
        inserted = images_collection.insert_one(doc)

        # Log + notify (include RSBSA in logs)
        logger.info(f"Prediction made by {rsbsa_number}: {result} (stored in MongoDB with _id={inserted.inserted_id})")
        notifier.notify_admin(
            f"New image pending review from {rsbsa_number}: {unique_filename}, Prediction: {result['prediction']}, Confidence: {result['confidence']:.2f}"
        )

        return jsonify({**result, "id": str(inserted.inserted_id)})

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/approve/<filename>/<label>", methods=["POST"])
def approve(filename, label):
    """Admin approves dataset and moves it to correct folder + MongoDB update"""
    pending_path = os.path.join(PENDING_FOLDER, filename)
    if not os.path.exists(pending_path):
        return jsonify({"error": "File not found"}), 404

    target_dir = os.path.join(APPROVED_FOLDER, label if label in CLASS_NAMES else "unknown")
    os.makedirs(target_dir, exist_ok=True)

    shutil.move(pending_path, os.path.join(target_dir, filename))

    # Update MongoDB
    images_collection.update_one(
        {"filename": filename},
        {"$set": {"status": "approved", "approved_class": label, "reviewed_at": datetime.utcnow()}}
    )

    logger.info(f"File {filename} approved under class {label}")
    return jsonify({"status": "approved", "file": filename, "class": label})


@app.route("/admin/reject/<filename>", methods=["POST"])
def reject(filename):
    """Admin rejects dataset and moves it to rejected folder + MongoDB update"""
    pending_path = os.path.join(PENDING_FOLDER, filename)
    if not os.path.exists(pending_path):
        return jsonify({"error": "File not found"}), 404

    shutil.move(pending_path, os.path.join(REJECTED_FOLDER, filename))

    # Update MongoDB
    images_collection.update_one(
        {"filename": filename},
        {"$set": {"status": "rejected", "reviewed_at": datetime.utcnow()}}
    )

    logger.info(f"File {filename} rejected")
    return jsonify({"status": "rejected", "file": filename})


@app.route("/api/user/<rsbsa_number>/history", methods=["GET"])
def get_user_history(rsbsa_number):
    """Get classification history for a specific user"""
    try:
        # Query all classifications for this RSBSA number
        user_classifications = list(images_collection.find(
            {"rsbsaNumber": rsbsa_number},
            {"_id": 1, "filename": 1, "prediction": 1, "confidence": 1, "timestamp": 1, "status": 1}
        ).sort("timestamp", -1))  # Most recent first
        
        # Convert ObjectId to string for JSON serialization
        for item in user_classifications:
            item["_id"] = str(item["_id"])
            
        return jsonify({
            "success": True, 
            "rsbsaNumber": rsbsa_number,
            "totalClassifications": len(user_classifications),
            "history": user_classifications
        })
        
    except Exception as e:
        logger.error(f"Error fetching history for {rsbsa_number}: {e}")
        return jsonify({"error": "Failed to fetch user history"}), 500


@app.route("/api/stats", methods=["GET"])
def get_general_stats():
    """Get general statistics (for admin dashboard)"""
    try:
        total_predictions = images_collection.count_documents({})
        pending_predictions = images_collection.count_documents({"status": "pending"})
        approved_predictions = images_collection.count_documents({"status": "approved"})
        rejected_predictions = images_collection.count_documents({"status": "rejected"})
        
        # Get unique users count
        unique_users = len(images_collection.distinct("rsbsaNumber"))
        
        return jsonify({
            "success": True,
            "stats": {
                "totalPredictions": total_predictions,
                "pendingPredictions": pending_predictions,
                "approvedPredictions": approved_predictions,
                "rejectedPredictions": rejected_predictions,
                "uniqueUsers": unique_users
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500


@app.route("/api/classification/<classification_id>", methods=["DELETE"])
def delete_classification(classification_id):
    """Delete a classification by ID"""
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(classification_id)
        except Exception:
            return jsonify({"error": "Invalid classification ID format"}), 400
        
        # Find the classification to delete
        classification = images_collection.find_one({"_id": object_id})
        
        if not classification:
            return jsonify({"error": "Classification not found"}), 404
        
        # Delete the classification from MongoDB
        result = images_collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Failed to delete classification"}), 500
        
        # Optional: Delete the associated image file if it exists
        filename = classification.get("filename")
        if filename:
            file_paths_to_check = [
                os.path.join(PENDING_FOLDER, filename),
                os.path.join(APPROVED_FOLDER, filename),
                os.path.join(REJECTED_FOLDER, filename)
            ]
            
            # Check in class-specific approved folders
            for cls in CLASS_NAMES + ["unknown"]:
                file_paths_to_check.append(os.path.join(APPROVED_FOLDER, cls, filename))
            
            for file_path in file_paths_to_check:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted image file: {file_path}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to delete image file {file_path}: {e}")
        
        logger.info(f"Classification {classification_id} deleted successfully")
        
        return jsonify({
            "success": True,
            "message": "Classification deleted successfully",
            "deletedId": classification_id
        })
        
    except Exception as e:
        logger.error(f"Error deleting classification {classification_id}: {e}")
        return jsonify({"error": "Failed to delete classification"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
