from ultralytics import YOLO
import os
# -------------------- Config --------------------
DANGER_CLASSES = [ 'gun']
SUSPICIOUS_CLASSES = ['mask', 'helmet', 'knife','fire']
NORMAL_CLASSES = ['person']

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "object_yolo.pt")

CONF_THRESHOLD = 0.4              # confidence threshold

model = YOLO(MODEL_PATH)

# -------------------- Helpers --------------------
def classify_detection(cls_name):
    """Map YOLO class name into severity category."""
    if cls_name in DANGER_CLASSES:
        return "danger"
    elif cls_name in SUSPICIOUS_CLASSES:
        return "suspicious"
    elif cls_name in NORMAL_CLASSES:
        return "normal"
    else:
        return "unknown"

def detect_from_frame(frame, threshold=CONF_THRESHOLD):
    """
    Run YOLO detection on a single frame (NumPy array).
    Returns a list of detections: 
    [{'class':..., 'severity':..., 'confidence':..., 'bbox':[x1,y1,x2,y2]}, ...]
    """
    results = model(frame)
    detections = []

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf < threshold:
                continue  # skip low-confidence predictions

            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            severity = classify_detection(cls_name)
            detections.append({
                "class": cls_name,
                "severity": severity,
                "confidence": conf,
                "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            })

    return detections

# -------------------- Optional testing --------------------
def detect_from_image(image_path, threshold=CONF_THRESHOLD):
    import cv2
    frame = cv2.imread(image_path)
    return detect_from_frame(frame, threshold)
