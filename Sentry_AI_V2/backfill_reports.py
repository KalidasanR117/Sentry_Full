# In backfill_reports.py
import os
import json
from datetime import datetime

OUTPUT_FOLDER = "output"
REPORT_LOG_FILE = "database/logs/event_log.json"

def backfill():
    print("--- Starting backfill process for existing PDFs ---")
    
    # Load existing reports to avoid duplicates
    existing_reports = []
    if os.path.exists(REPORT_LOG_FILE):
        with open(REPORT_LOG_FILE, "r") as f:
            try:
                existing_reports = json.load(f)
            except json.JSONDecodeError:
                pass # File is empty or corrupt
    
    existing_paths = {report.get("pdf_path") for report in existing_reports}
    
    new_reports_added = 0
    # Scan the output folder for PDF files
    for filename in os.listdir(OUTPUT_FOLDER):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(OUTPUT_FOLDER, filename)
            
            # If the report is already logged, skip it
            if pdf_path in existing_paths:
                continue

            # Create a new report entry
            report_type = "camera" if "LiveReport" in filename else "upload"
            report_entry = {
                "id": int(os.path.getmtime(pdf_path)), # Use file modification time for a unique ID
                "timestamp": datetime.fromtimestamp(os.path.getmtime(pdf_path)).strftime("%Y-%m-%d %H:%M:%S"),
                "report_type": report_type,
                "summary": "Summary not available for this legacy report.",
                "pdf_path": pdf_path
            }
            
            existing_reports.append(report_entry)
            new_reports_added += 1
            print(f"Added record for: {filename}")

    # Write the updated list back to the log file
    with open(REPORT_LOG_FILE, "w") as f:
        json.dump(existing_reports, f, indent=4)
        
    print(f"--- Backfill complete. Added {new_reports_added} new report(s). ---")

if __name__ == "__main__":
    backfill()