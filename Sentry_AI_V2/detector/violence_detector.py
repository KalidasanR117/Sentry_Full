# violence_detector.py
import os
from ultralytics import YOLO
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "violence_yolo.pt")  # your YOLOv11 model

# Load YOLOv11 model
print("[INFO] Loading YOLOv11 Violence model...")
violence_model = YOLO(MODEL_PATH)
print("[INFO] YOLOv11 Violence model loaded.")

VIOLENCE_CLASSES = {0: "non-violence", 1: "violence"}

def run_violence_detection(frame, threshold=0.5):
    """
    Run YOLOv11 violence detection on a single frame.
    Returns:
        detections: list of dicts with bbox, class, confidence, type
    """
    results = violence_model(frame)
    detections = []

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf < threshold:
                continue

            cls_id = int(box.cls[0])
            cls_name = violence_model.names[cls_id]

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "class": cls_name,
                "confidence": conf,
                "bbox": [x1, y1, x2, y2],
                "type": "violence"
            })

    # If nothing detected, return non-violence with fake bbox covering whole frame
    if not detections:
        h, w = frame.shape[:2]
        detections.append({
            "class": "non-violence",
            "confidence": 0.0,
            "bbox": [0, 0, w, h],
            "type": "violence"
        })

    return detections
