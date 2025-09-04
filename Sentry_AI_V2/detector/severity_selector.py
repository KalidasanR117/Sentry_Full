from detector.yolo_detector import detect_from_frame

# Violence YOLO → severity mapping
VIOLENCE_SEVERITY_MAP = {
    "non-violence": "normal",
    "violence": "danger"  # violence is treated as danger
}

def select_severity(yolo_detections, violence_prediction):
    """
    Combine YOLO object detections and Violence YOLO prediction to decide final severity.
    
    Args:
        yolo_detections: list of dicts [{"class":..., "severity":..., ...}, ...]
        violence_prediction: string output from Violence YOLO ("violence", "non-violence")
        
    Returns:
        final_severity: "normal", "suspicious", or "danger"
    """
    # 1️⃣ Default severity from Violence YOLO
    final_severity = VIOLENCE_SEVERITY_MAP.get(violence_prediction, "normal")

    # 2️⃣ Override if Object YOLO finds higher severity
    for det in yolo_detections:
        if det["severity"] == "danger":
            final_severity = "danger"
            break
        elif det["severity"] == "suspicious" and final_severity != "danger":
            final_severity = "suspicious"

    return final_severity
