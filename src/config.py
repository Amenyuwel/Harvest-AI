import os

# -------------------------
# Paths
# -------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PENDING_FOLDER = os.path.join(UPLOAD_FOLDER, "pending")
APPROVED_FOLDER = os.path.join(UPLOAD_FOLDER, "approved")
REJECTED_FOLDER = os.path.join(UPLOAD_FOLDER, "rejected")

MODEL_PATH = os.path.join(BASE_DIR, "vgg", "harvest_model.keras")

# -------------------------
# Image size used in training
# -------------------------
IMAGE_SIZE = (100, 100)

# -------------------------
# Classes
# -------------------------
CLASS_NAMES = ["fall_armyworm", "snail", "stem_borer", "unknown"]

# Map indices to class names
CLASS_INDICES = {
    0: "fall_armyworm",
    1: "snail",
    2: "stem_borer",
    3: "unknown"
}

# Allowed file types
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Ensure folders exist
for folder in [UPLOAD_FOLDER, PENDING_FOLDER, APPROVED_FOLDER, REJECTED_FOLDER]:
    os.makedirs(folder, exist_ok=True)
