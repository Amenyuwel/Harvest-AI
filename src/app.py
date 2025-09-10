# refactored_app.py - Following SOLID principles
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from .dependency_container import container
from .logger import logger
from .notifier import Notifier

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# -------------------------
# App Setup
# -------------------------
app = Flask(__name__)

CORS(app, 
     origins=["http://localhost:3000", "http://192.168.1.5:3000", "http://localhost:5173"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"]
)

notifier = Notifier()

# -------------------------
# Error Handlers
# -------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({"error": "File too large"}), 413

# -------------------------
# Routes - Single Responsibility: Handle HTTP concerns only
# -------------------------
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Harvest Assistant Model Service is running"})

@app.route("/predict", methods=["POST"])
def predict():
    # Validate request
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Extract user data
    user_data = {
        "rsbsaNumber": request.form.get("rsbsaNumber", "anonymous"),
        "fullName": request.form.get("fullName", "Unknown"),
        "barangay": request.form.get("barangay", "Unknown"),
        "crop": request.form.get("crop", "Unknown"),
        "area": request.form.get("area", "0"),
        "contact": request.form.get("contact", "Unknown")
    }

    try:
        # Use dependency injection - no direct dependencies
        prediction_service = container.get_prediction_service()
        result = prediction_service.process_prediction(file, user_data)
        
        # Log and notify
        logger.info(f"Prediction made by {user_data['fullName']} ({user_data['rsbsaNumber']}) from {user_data['barangay']}")
        notifier.notify_admin(f"New prediction from {user_data['fullName']}: {result['prediction']}")
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/approve/<filename>/<label>", methods=["POST"])
def approve(filename, label):
    """Admin approval endpoint"""
    try:
        repository = container.get_repository()
        file_manager = container.get_file_manager()
        
        # Update status in repository
        repository.update_status_by_filename(filename, "approved", label)
        
        # Move file (this could be extracted to a separate service)
        # file_manager.move_to_approved(filename, label)
        
        logger.info(f"File {filename} approved under class {label}")
        return jsonify({"status": "approved", "file": filename, "class": label})
        
    except Exception as e:
        logger.error(f"Approval error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
