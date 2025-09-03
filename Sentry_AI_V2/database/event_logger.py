# In database/event_logger.py
import os
import json
from datetime import datetime
from pathlib import Path
import cv2

# --- ✅ NEW: Robust, Absolute Path Calculation ---
# This ensures the log files are always found in the correct place,
# no matter how the application is started.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# --- File paths now use the absolute LOG_DIR ---
EVENT_LOG_FILE = os.path.join(LOG_DIR, "event_log.json")
REPORT_LOG_FILE = os.path.join(LOG_DIR, "report_log.json")

# --- Original Event Logging (for individual frames) ---
def log_event(frame, yolo_results, i3d_pred, severity):
    """ Log individual events to JSON file. """
    event = {
        "timestamp": datetime.now().isoformat(),
        "severity": severity,
        "yolo_results": yolo_results,
        "i3d_prediction": i3d_pred
    }
    logs = []
    if os.path.exists(EVENT_LOG_FILE):
        try:
            with open(EVENT_LOG_FILE, "r") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, ValueError):
            logs = []
    logs.append(event)
    with open(EVENT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)
    if severity == "danger":
        SNAP_DIR = Path(LOG_DIR) / "snapshots"
        SNAP_DIR.mkdir(exist_ok=True)
        filename = SNAP_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(filename), frame)

def get_events():
    """ Retrieve all logged events. """
    if not os.path.exists(EVENT_LOG_FILE):
        return []
    try:
        with open(EVENT_LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

# --- Report Logging (for final summaries and PDFs) ---
def log_report(report_type: str, summary: str, pdf_path: str):
    """ Logs a generated report summary to a separate JSON file. """
    report_entry = {
        "id": int(datetime.now().timestamp()), # Simple unique ID
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report_type": report_type,
        "summary": summary,
        "pdf_path": pdf_path
    }
    reports = []
    if os.path.exists(REPORT_LOG_FILE):
        try:
            with open(REPORT_LOG_FILE, "r") as f:
                reports = json.load(f)
        except (json.JSONDecodeError, ValueError):
            reports = []
    reports.append(report_entry)
    with open(REPORT_LOG_FILE, "w") as f:
        json.dump(reports, f, indent=4)

def get_reports():
    """ Retrieves all reports, newest first. """
    if not os.path.exists(REPORT_LOG_FILE):
        return []
    try:
        with open(REPORT_LOG_FILE, "r") as f:
            reports = json.load(f)
            formatted_reports = [
                {
                    "id": r.get("id"),
                    "timestamp": r.get("timestamp"),
                    "report_type": r.get("report_type"),
                    "summary": r.get("summary"),
                    "pdf_filename": os.path.basename(r.get("pdf_path", ""))
                }
                for r in reports
            ]
            return sorted(formatted_reports, key=lambda x: x.get('id', 0), reverse=True)
    except (json.JSONDecodeError, ValueError):
        return []

def delete_report(report_id_to_delete: int):
    """Deletes a report record from the JSON file and returns its path."""
    if not os.path.exists(REPORT_LOG_FILE):
        return None
    
    reports = []
    path_to_delete = None
    
    with open(REPORT_LOG_FILE, "r") as f:
        try:
            reports = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return None
    
    updated_reports = []
    report_was_found = False
    for report in reports:
        if report.get("id") == report_id_to_delete:
            path_to_delete = report.get("pdf_path")
            report_was_found = True
        else:
            updated_reports.append(report)
            
    if report_was_found:
        with open(REPORT_LOG_FILE, "w") as f:
            json.dump(updated_reports, f, indent=4)
            
    return path_to_delete