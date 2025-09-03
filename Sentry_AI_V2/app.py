import os
import cv2
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# --- SentryAI module imports ---
from input.camera_stream import capture_frames
from detector.yolo_detector import detect_from_frame
from detector.i3d_detector import run_prediction
from detector.severity_selector import select_severity
from llm.llm_summary import generate_summary_from_events
from reports.report_generator import generate_pdf_report
from alerts.telegram_bot import send_alert, send_pdf_with_summary
from database.event_logger import log_report, get_reports, delete_report

# Set a longer timeout for network streams
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;60000"

# -------------------- Configuration --------------------
UPLOAD_FOLDER = "input"
OUTPUT_FOLDER = "output"
SCREENSHOT_DIR = os.path.join(OUTPUT_FOLDER, "screenshots")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CLIP_LEN = 40
YOLO_CONF_THRESHOLD = 0.4
ALERT_COOLDOWN = 15
I3D_INPUT_SIZE = (128, 128)

# -------------------- Flask App Setup --------------------
app = Flask(__name__)
CORS(app)

# -------------------- Annotation Helper Function --------------------
def draw_annotations(frame, yolo_results):
    """Draws bounding boxes and labels on a frame."""
    annotated_frame = frame.copy()
    for det in yolo_results:
        try:
            x1, y1, x2, y2 = map(int, det["bbox"])
            label = f"{det['class']} ({det.get('confidence', 0.0):.2f})"
            color = (0, 255, 0)  # Green for all boxes
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, (x1, y1 - 20), (x1 + w, y1), color, -1)
            cv2.putText(annotated_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        except Exception as e:
            print(f"Could not draw annotation for det {det}: {e}")
    return annotated_frame

# -------------------- Real-time Camera State Management --------------------
camera_thread = None
is_camera_processing = threading.Event()
camera_alert_buffer = []
camera_report_buffer = []
lock = threading.Lock()
last_alert_time = 0
latest_camera_frame = None

# -------------------- Workflow 1: Uploaded Video Processing --------------------
@app.route("/api/process-video", methods=["POST"])
def process_video():
    if "file" not in request.files: return jsonify({"error": "No file provided"}), 400
    video = request.files["file"]
    save_path = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(save_path)
    video_specific_events, local_last_alert_time = [], 0
    try:
        for frame_count, (frame, clip) in enumerate(capture_frames(save_path)):
            yolo_results = detect_from_frame(frame, threshold=YOLO_CONF_THRESHOLD)
            i3d_pred, i3d_conf = "normal", 0.0
            if len(clip) >= CLIP_LEN:
                clip_preprocessed = [cv2.resize(f, I3D_INPUT_SIZE) for f in clip]
                i3d_pred, i3d_conf = run_prediction(clip_preprocessed)
            severity = select_severity(yolo_results, i3d_pred)
            if severity in ["danger", "suspicious"]:
                annotated_frame = draw_annotations(frame, yolo_results)
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"upload_{time.time()}.jpg")
                cv2.imwrite(screenshot_path, annotated_frame)
                yolo_classes = [f"{det['class']} ({det.get('confidence', 0.0):.2f})" for det in yolo_results]
                event_data = {
                    "frame": frame_count, "yolo": ", ".join(yolo_classes), "i3d": f"{i3d_pred} ({i3d_conf:.2f})",
                    "final": severity, "screenshot": screenshot_path, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                video_specific_events.append(event_data)
                if severity == "danger" and (time.time() - local_last_alert_time) > ALERT_COOLDOWN:
                    send_alert(annotated_frame, severity)
                    local_last_alert_time = time.time()
        if video_specific_events:
            summary_text = generate_summary_from_events(video_specific_events)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = os.path.join(OUTPUT_FOLDER, f"SentryAI_Report_{timestamp}.pdf")
            generate_pdf_report(video_specific_events, summary_text, pdf_path)
            send_pdf_with_summary(pdf_path, summary_text)
            log_report('upload', summary_text, pdf_path)
        return jsonify({"status": "Video processed and report generated.", "events_found": len(video_specific_events)})
    except Exception as e:
        print(f"Error processing uploaded video: {e}")
        return jsonify({"error": f"Failed to analyze video: {e}"}), 500

# -------------------- Workflow 2: Live Camera Processing --------------------
def camera_analysis_loop(source=0):
    global last_alert_time, latest_camera_frame
    try:
        for frame_count, (frame, clip) in enumerate(capture_frames(source)):
            if not is_camera_processing.is_set(): break
            
            yolo_results = detect_from_frame(frame, threshold=YOLO_CONF_THRESHOLD)
            
            # ✅ FINAL FIX: Always draw annotations and update the shared frame with the annotated version.
            annotated_frame = draw_annotations(frame, yolo_results)
            with lock:
                latest_camera_frame = annotated_frame.copy()

            i3d_pred, i3d_conf = "normal", 0.0
            if len(clip) >= CLIP_LEN:
                clip_preprocessed = [cv2.resize(f, I3D_INPUT_SIZE) for f in clip]
                i3d_pred, i3d_conf = run_prediction(clip_preprocessed)
            severity = select_severity(yolo_results, i3d_pred)
            
            if severity in ["danger", "suspicious"]:
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"live_{time.time()}.jpg")
                cv2.imwrite(annotated_frame, screenshot_path) # Save the annotated frame
                yolo_classes = [det['class'] for det in yolo_results]
                alert_message = {
                    "message": f"{severity.capitalize()} Detected: {', '.join(yolo_classes)}",
                    "type": "error" if severity == "danger" else "warning", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                yolo_strings = [f"{det['class']} ({det.get('confidence', 0.0):.2f})" for det in yolo_results]
                report_data = {
                    "frame": frame_count, "yolo": ", ".join(yolo_strings), "i3d": f"{i3d_pred} ({i3d_conf:.2f})",
                    "final": severity, "screenshot": screenshot_path
                }
                with lock:
                    camera_alert_buffer.append(alert_message)
                    camera_report_buffer.append(report_data)
                if severity == "danger" and (time.time() - last_alert_time) > ALERT_COOLDOWN:
                    send_alert(annotated_frame, severity)
                    last_alert_time = time.time()
    except Exception as e:
        print(f"Error in camera analysis thread: {e}")
    finally:
        with lock: latest_camera_frame = None
        print("Camera analysis thread stopped.")

@app.route("/api/start_camera", methods=["POST"])
def start_camera_analysis():
    global camera_thread
    if camera_thread is None or not camera_thread.is_alive():
        data = request.get_json()
        video_source = data.get('source', 0) if data else 0
        if isinstance(video_source, str) and not video_source.strip(): video_source = 0
        print(f"Testing video source: {video_source}")
        cap_test = cv2.VideoCapture(video_source)
        if not cap_test.isOpened():
            cap_test.release()
            print(f"!!! FAILED to open video source: {video_source}")
            return jsonify({"error": f"Failed to open video stream. Check the URL or camera index, and ensure it's not blocked by a firewall."}), 400
        cap_test.release()
        print("Video source test successful.")
        is_camera_processing.set()
        with lock:
            camera_alert_buffer.clear()
            camera_report_buffer.clear()
        camera_thread = threading.Thread(target=camera_analysis_loop, args=(video_source,), daemon=True)
        camera_thread.start()
        return jsonify({"status": "Camera analysis started."})
    return jsonify({"status": "Camera analysis is already running."})

@app.route("/api/stop_camera", methods=["POST"])
def stop_camera_analysis():
    global camera_thread
    if camera_thread and camera_thread.is_alive():
        is_camera_processing.clear()
        camera_thread.join()
        camera_thread = None
        return jsonify({"status": "Camera analysis stopped."})
    return jsonify({"status": "Camera analysis is not running."})

@app.route("/api/generate-camera-report", methods=["POST"])
def generate_camera_report():
    with lock:
        if not camera_report_buffer: return jsonify({"status": "No events to report."}), 404
        events_to_report = list(camera_report_buffer)
        camera_report_buffer.clear()
        camera_alert_buffer.clear()
    try:
        summary_text = generate_summary_from_events(events_to_report)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(OUTPUT_FOLDER, f"SentryAI_LiveReport_{timestamp}.pdf")
        generate_pdf_report(events_to_report, summary_text, pdf_path)
        send_pdf_with_summary(pdf_path, summary_text)
        log_report('camera', summary_text, pdf_path)
        return jsonify({"status": f"Report generated and sent with {len(events_to_report)} events."})
    except Exception as e:
        print(f"!!! [Report Generation] AN ERROR OCCURRED: {e} !!!")
        return jsonify({"status": f"An error occurred during report generation: {e}"}), 500

# -------------------- Past Reports Routes --------------------
@app.route("/api/reports", methods=["GET"])
def fetch_reports():
    reports = get_reports()
    return jsonify(reports)

@app.route("/api/reports/<int:report_id>", methods=["DELETE"])
def remove_report(report_id):
    pdf_path = delete_report(report_id)
    if pdf_path:
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            return jsonify({"status": "Report deleted successfully."})
        except Exception as e:
            return jsonify({"error": f"Error deleting file: {e}"}), 500
    return jsonify({"error": "Report not found in log."}), 404

@app.route("/api/download-report/<path:filename>", methods=["GET"])
def download_report(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found."}), 404

# -------------------- Basic and Utility Routes --------------------
@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    with lock: return jsonify(camera_alert_buffer[-5:][::-1])

@app.route("/api/health", methods=["GET"])
def health_check():
    return {"status": "ok", "message": "Sentry AI is running"}, 200

def gen_frames_from_thread():
    while True:
        time.sleep(0.03)
        with lock:
            if not is_camera_processing.is_set(): break
            if latest_camera_frame is None: continue
            ret, buffer = cv2.imencode('.jpg', latest_camera_frame)
            frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/api/video_feed')
def video_feed():
    return Response(gen_frames_from_thread(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
