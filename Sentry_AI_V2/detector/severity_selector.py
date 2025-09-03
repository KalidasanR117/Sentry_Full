from detector.yolo_detector import detect_from_frame

# I3D → severity mapping
I3D_SEVERITY_MAP = {
    "normal": "normal",
    "robbery": "danger",
    "fight": "suspicious"
}

def select_severity(yolo_detections, i3d_prediction):
    """
    Combine YOLO detections and I3D prediction to decide final severity.
    
    Args:
        yolo_detections: list of dicts [{"class":..., "severity":..., ...}, ...]
        i3d_prediction: string output from I3D ("normal", "robbery", "fight")
        
    Returns:
        final_severity: "normal", "suspicious", or "danger"
    """
    # 1️⃣ Default severity from I3D
    final_severity = I3D_SEVERITY_MAP.get(i3d_prediction, "normal")

    # 2️⃣ Override if YOLO finds danger
    for det in yolo_detections:
        if det["severity"] == "danger":
            final_severity = "danger"
            break
        elif det["severity"] == "suspicious" and final_severity != "danger":
            final_severity = "suspicious"

    return final_severity
