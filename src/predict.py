import os
import cv2
import json
import numpy as np
from datetime import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import VGG19
from tensorflow.keras.applications.vgg19 import preprocess_input

from .config import (
    UPLOAD_FOLDER,
    MODEL_PATH,
    IMAGE_SIZE,
    CLASS_INDICES
)

# Directories for review
TO_REVIEW_DIR = os.path.join("storage", "to_review")
os.makedirs(TO_REVIEW_DIR, exist_ok=True)

# Load models once on startup
print("Loading VGG19 for feature extraction...")
vgg19 = VGG19(include_top=False, weights="imagenet")

print("Loading trained model...")
model = load_model(MODEL_PATH)

print(f"Model input shape: {model.input_shape}")
print(f"Model output shape: {model.output_shape}")


def preprocess_image(img_path):
    """Resize → preprocess → extract VGG19 features."""
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Could not load image: {img_path}")
    
    img_resized = cv2.resize(img, IMAGE_SIZE)
    img_array = np.array([img_resized])  # add batch dimension

    img_preprocessed = preprocess_input(img_array)
    features = vgg19.predict(img_preprocessed, verbose=0)
    features_flattened = features.reshape(features.shape[0], -1)

    return features_flattened


def predict_image(img_path, save_for_review=False):
    """Run prediction and optionally store for admin review."""
    try:
        features = preprocess_image(img_path)
        preds = model.predict(features, verbose=0)

        predicted_class_idx = np.argmax(preds)
        predicted_class = CLASS_INDICES[predicted_class_idx]
        confidence = float(np.max(preds))

        # Probabilities per class
        probabilities = {
            CLASS_INDICES[idx]: float(prob) for idx, prob in enumerate(preds[0])
        }

        result = {
            "filename": os.path.basename(img_path),
            "prediction": predicted_class,
            "confidence": confidence,
            "probabilities": probabilities,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Save to "to_review" for admin (only if requested)
        if save_for_review:
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            review_img_path = os.path.join(TO_REVIEW_DIR, f"{base_name}.png")
            review_meta_path = os.path.join(TO_REVIEW_DIR, f"{base_name}.json")

            # Copy image instead of moving (since app.py needs it)
            import shutil
            shutil.copy2(img_path, review_img_path)
            
            # Save JSON metadata
            with open(review_meta_path, "w") as f:
                json.dump(result, f, indent=4)

        return result

    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    images = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    if not images:
        print("No images found in upload folder.")
        exit()

    print(f"Found {len(images)} images in upload folder")
    print("-" * 60)

    for img_name in images:
        img_path = os.path.join(UPLOAD_FOLDER, img_name)
        result = predict_image(img_path, save_for_review=True)

        print(f"\nProcessing: {result['filename']}")
        for cls, prob in result["probabilities"].items():
            print(f"  {cls}: {prob:.4f}")
        print(f"→ Prediction: {result['prediction']} (confidence: {result['confidence']:.4f})")

    print("\n" + "-" * 60)
    print("Prediction complete! Files copied to storage/to_review/")
