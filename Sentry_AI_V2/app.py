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
from detector.violence_detector import run_violence_detection
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

YOLO_CONF_THRESHOLD = 0.4
ALERT_COOLDOWN = 15

# -------------------- Flask App Setup --------------------
app = Flask(__name__)
CORS(app)

# -------------------- Annotation Helper Function --------------------
def draw_annotations(frame, yolo_results, violence_results):
    """Draws bounding boxes for both object and violence detection."""
    annotated_frame = frame.copy()
    for det in yolo_results:
        try:
            x1, y1, x2, y2 = map(int, det["bbox"])
            label = f"Object: {det['class']} ({det.get('confidence', 0.0):.2f})"
            color = (0, 255, 0)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        except Exception as e:
            print(f"Could not draw object annotation: {e}")
    for det in violence_results:
        if det.get("class") == "violence":
            try:
                x1, y1, x2, y2 = map(int, det["bbox"])
                label = f"Action: {det['class']} ({det.get('confidence', 0.0):.2f})"
                color = (0, 0, 255)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, label, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            except Exception as e:
                print(f"Could not draw violence annotation: {e}")
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
        for frame_count, (frame, _) in enumerate(capture_frames(save_path)):
            yolo_results = detect_from_frame(frame, threshold=YOLO_CONF_THRESHOLD)
            violence_results = run_violence_detection(frame)
            violence_prediction = violence_results[0]['class']
            severity = select_severity(yolo_results, violence_prediction)
            
            if severity in ["danger", "suspicious"]:
                annotated_frame = draw_annotations(frame, yolo_results, violence_results)
                screenshot_path = os.path.abspath(os.path.join(SCREENSHOT_DIR, f"upload_{time.time()}.jpg"))
                cv2.imwrite(screenshot_path, annotated_frame)
                
                yolo_classes = [f"{det['class']}" for det in yolo_results]
                alert_message = {
                    "message": f"{severity.capitalize()} Detected in Upload: {', '.join(yolo_classes)} & {violence_prediction}",
                    "type": "error" if severity == "danger" else "warning",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with lock:
                    camera_alert_buffer.append(alert_message)

                yolo_strings = [f"{det['class']} ({det.get('confidence', 0.0):.2f})" for det in yolo_results]
                event_data = {
                    "frame": frame_count,
                    "yolo": ", ".join(yolo_strings),
                    "violence": violence_prediction,
                    "yolo_object": ", ".join(yolo_strings),
                    "yolo_violence": violence_prediction,
                    "final": severity,
                    "screenshot": screenshot_path,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

# -------------------- Workflow 2: Live Camera Processing (Hybrid Approach) --------------------
def camera_analysis_loop_local(source=0):
    global last_alert_time, latest_camera_frame
    try:
        for frame_count, (frame, _) in enumerate(capture_frames(source)):
            if not is_camera_processing.is_set(): break
            yolo_results = detect_from_frame(frame, threshold=YOLO_CONF_THRESHOLD)
            violence_results = run_violence_detection(frame)
            violence_prediction = violence_results[0]['class']
            annotated_frame = draw_annotations(frame, yolo_results, violence_results)
            with lock:
                latest_camera_frame = annotated_frame.copy()
            severity = select_severity(yolo_results, violence_prediction)
            
            if severity in ["danger", "suspicious"]:
                screenshot_path = os.path.abspath(os.path.join(SCREENSHOT_DIR, f"live_local_{time.time()}.jpg"))
                try:
                    save_success = cv2.imwrite(screenshot_path, annotated_frame)
                    if not save_success:
                        print(f"⚠️ WARNING: Failed to save screenshot to {screenshot_path}")
                        screenshot_path = None
                except Exception as e:
                    print(f"!!! ERROR saving screenshot: {e}")
                    screenshot_path = None

                if screenshot_path:
                    yolo_classes = [det['class'] for det in yolo_results]
                    alert_message = { "message": f"{severity.capitalize()} Detected: {', '.join(yolo_classes)} & {violence_prediction}", "type": "error" if severity == "danger" else "warning", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S") }
                    yolo_strings = [f"{det['class']} ({det.get('confidence', 0.0):.2f})" for det in yolo_results]
                    
                    report_data = {
                        "frame": frame_count,
                        "yolo": ", ".join(yolo_strings),
                        "violence": violence_prediction,
                        "yolo_object": ", ".join(yolo_strings),
                        "yolo_violence": violence_prediction,
                        "final": severity,
                        "screenshot": screenshot_path
                    }
                    with lock:
                        camera_alert_buffer.append(alert_message)
                        camera_report_buffer.append(report_data)
                    if severity == "danger" and (time.time() - last_alert_time) > ALERT_COOLDOWN:
                        send_alert(annotated_frame, severity)
                        last_alert_time = time.time()
    except Exception as e:
        print(f"Error in LOCAL camera analysis thread: {e}")
    finally:
        with lock: latest_camera_frame = None
        print("Local camera analysis thread stopped.")

def camera_analysis_loop_network(source=0):
    global last_alert_time, latest_camera_frame
    cap = None
    try:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"!!! FATAL ERROR in thread: Could not open network stream: {source}")
            return
        frame_count = 0
        while is_camera_processing.is_set():
            cap.grab()
            success, frame = cap.retrieve()
            if not success:
                time.sleep(0.1)
                continue
            yolo_results = detect_from_frame(frame, threshold=YOLO_CONF_THRESHOLD)
            violence_results = run_violence_detection(frame)
            violence_prediction = violence_results[0]['class']
            annotated_frame = draw_annotations(frame, yolo_results, violence_results)
            with lock:
                latest_camera_frame = annotated_frame.copy()
            severity = select_severity(yolo_results, violence_prediction)

            if severity in ["danger", "suspicious"]:
                # ✅ FIXED: Use an absolute path and add error checking for network stream screenshots.
                screenshot_path = os.path.abspath(os.path.join(SCREENSHOT_DIR, f"live_network_{time.time()}.jpg"))
                try:
                    save_success = cv2.imwrite(screenshot_path, annotated_frame)
                    if not save_success:
                        print(f"⚠️ WARNING: Failed to save NETWORK screenshot to {screenshot_path}")
                        screenshot_path = None
                except Exception as e:
                    print(f"!!! ERROR saving NETWORK screenshot: {e}")
                    screenshot_path = None

                if screenshot_path:
                    yolo_classes = [det['class'] for det in yolo_results]
                    alert_message = { "message": f"{severity.capitalize()} Detected: {', '.join(yolo_classes)} & {violence_prediction}", "type": "error" if severity == "danger" else "warning", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S") }
                    yolo_strings = [f"{det['class']} ({det.get('confidence', 0.0):.2f})" for det in yolo_results]
                    
                    report_data = {
                        "frame": frame_count,
                        "yolo": ", ".join(yolo_strings),
                        "violence": violence_prediction,
                        "yolo_object": ", ".join(yolo_strings),
                        "yolo_violence": violence_prediction,
                        "final": severity,
                        "screenshot": screenshot_path
                    }
                    with lock:
                        camera_alert_buffer.append(alert_message)
                        camera_report_buffer.append(report_data)
                    if severity == "danger" and (time.time() - last_alert_time) > ALERT_COOLDOWN:
                        send_alert(annotated_frame, severity)
                        last_alert_time = time.time()
            frame_count += 1
            time.sleep(0.01)
    except Exception as e:
        print(f"Error in NETWORK camera analysis thread: {e}")
    finally:
        if cap: cap.release()
        with lock: latest_camera_frame = None
        print("Network camera analysis thread stopped.")

@app.route("/api/start_camera", methods=["POST"])
def start_camera_analysis():
    global camera_thread
    if camera_thread is None or not camera_thread.is_alive():
        data = request.get_json()
        video_source = data.get('source', 0) if data else 0
        is_network_stream = isinstance(video_source, str)
        if is_network_stream and not video_source.strip():
            video_source = 0
            is_network_stream = False
        target_loop = camera_analysis_loop_network if is_network_stream else camera_analysis_loop_local
        is_camera_processing.set()
        with lock:
            camera_alert_buffer.clear()
            camera_report_buffer.clear()
        camera_thread = threading.Thread(target=target_loop, args=(video_source,), daemon=True)
        camera_thread.start()
        print(f"Starting analysis with {'NETWORK' if is_network_stream else 'LOCAL'} loop for source: {video_source}")
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

@app.route("/api/reports", methods=["GET"])
def fetch_reports():
    reports = get_reports()
    return jsonify(reports)

@app.route("/api/reports/<int:report_id>", methods=["DELETE"])
def remove_report(report_id):
    pdf_path = delete_report(report_id)
    if pdf_path:
        try:
            if os.path.exists(pdf_path): os.remove(pdf_path)
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
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

