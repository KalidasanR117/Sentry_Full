import os
import cv2
import time
from input.camera_stream import capture_frames
from detector.yolo_detector import detect_from_frame
from detector.violence_detector import run_violence_detection
from detector.severity_selector import select_severity
from database.event_logger import log_event
from llm.llm_summary import generate_summary_from_events
from reports.report_generator import generate_pdf_report
from alerts.telegram_bot import send_alert, send_pdf_with_summary  # Telegram integration

# -------------------- Config --------------------
VIDEO_SOURCE = r"./tests/124.mp4"  # or 0 for webcam
SCREENSHOT_DIR = r"./output/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
YOLO_CONF_THRESHOLD = 0.4
ALERT_COOLDOWN = 15  # seconds between consecutive danger alerts

event_buffer = []   # Collected events for report
last_alert_time = 0
last_logged = {"severity": "normal", "yolo": ""}  # Prevent duplicate logs

# -------------------- Main --------------------
def main():
    global last_alert_time, last_logged
    print("[INFO] Starting Mini SentryAI+...")

    frame_id = 0
    for frame, _ in capture_frames(VIDEO_SOURCE):
        frame_id += 1

        # -------------------- YOLO Object Detection --------------------
        yolo_results = detect_from_frame(frame, threshold=YOLO_CONF_THRESHOLD)

        # -------------------- YOLO Violence Detection --------------------
        violence_pred, violence_conf = run_violence_detection(frame)

        # -------------------- Severity selection --------------------
        severity = select_severity(yolo_results, violence_pred)

        # -------------------- Event logging --------------------
        yolo_classes = []
        for det in yolo_results:
            cls = det["class"]
            conf = det.get("confidence", 0.0)
            yolo_classes.append(f"{cls} ({conf:.2f})")

        # Log every frame to JSON (for history)
        log_event(frame, yolo_results, f"{violence_pred} ({violence_conf:.2f})", severity)

        # -------------------- Save annotated screenshot --------------------
        if severity in ["danger", "suspicious"]:
            current_yolo = ", ".join(yolo_classes)

            # Only log when severity or classes change
            if severity != last_logged["severity"] or current_yolo != last_logged["yolo"]:
                annotated_frame = frame.copy()
                for det in yolo_results:
                    x1, y1, x2, y2 = map(int, det["bbox"])
                    color = (0, 0, 255) if det["severity"] == "danger" else (0, 255, 255)
                    label = f"{det['class']} ({det['severity']}) {det['confidence']:.2f}"
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated_frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                severity_color = (0, 0, 255) if severity == "danger" else (0, 255, 255)
                cv2.putText(annotated_frame, f"Final Severity: {severity}", (35, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, severity_color, 2)

                screenshot_path = os.path.join(SCREENSHOT_DIR, f"event_{frame_id}.jpg")
                cv2.imwrite(screenshot_path, annotated_frame)

                event_buffer.append({
                    "frame": frame_id,
                    "yolo": current_yolo,
                    "violence": f"{violence_pred} ({violence_conf:.2f})",
                    "final": severity,
                    "screenshot": screenshot_path
                })

                last_logged = {"severity": severity, "yolo": current_yolo}

                # -------------------- Telegram alert with cooldown --------------------
                if severity == "danger" and (time.time() - last_alert_time) > ALERT_COOLDOWN:
                    send_alert(annotated_frame, severity)
                    last_alert_time = time.time()

        # -------------------- Visualization --------------------
        for det in yolo_results:
            x1, y1, x2, y2 = map(int, det["bbox"])
            color = (0, 0, 255) if det["severity"] == "danger" else (0, 255, 255)
            label = f"{det['class']} ({det['severity']}) {det['confidence']:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        severity_color = (
            (0, 0, 255) if severity == "danger"
            else (0, 255, 255) if severity == "suspicious"
            else (0, 255, 0)
        )
        cv2.putText(frame, f"Final Severity: {severity}", (35, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, severity_color, 2)

        cv2.imshow("Mini SentryAI+", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()

    # -------------------- Generate LLM summary --------------------
    if event_buffer:
        summary_text = generate_summary_from_events(event_buffer)
        print("[INFO] LLM Summary Generated:")
        print(summary_text)

        # -------------------- Generate PDF report --------------------
        pdf_path = os.path.join("./output", "MiniSentryAI_Report.pdf")
        generate_pdf_report(event_buffer, summary_text, pdf_path)
        print(f"[INFO] PDF report saved to {pdf_path}")

        # -------------------- Send final PDF via Telegram --------------------
        send_pdf_with_summary(pdf_path, summary_text)

if __name__ == "__main__":
    main()
