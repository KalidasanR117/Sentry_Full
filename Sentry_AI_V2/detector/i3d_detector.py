import cv2
import numpy as np
from tensorflow.keras.models import load_model
import os

# -------------------- Config --------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "ucf_crime_heavy_model.keras")

FRAME_SIZE = (128, 128)
CLIP_LEN = 40
THRESHOLD = 0.5  # minimum confidence to consider prediction

CLASS_LABELS = {
    0: "normal",
    1: "fight",
    2: "robbery"
}

# -------------------- Load model --------------------
print("[INFO] Loading I3D model...")
model = load_model(MODEL_PATH, compile=False)
print("[INFO] I3D model loaded.")

# -------------------- Helpers --------------------
def preprocess_frame(frame):
    """Resize and normalize a single frame"""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, FRAME_SIZE).astype("float32") / 255.0
    return frame_resized

def run_prediction(frame_buffer):
    """Predict action from a clip"""
    clip = np.array(frame_buffer)
    while clip.shape[0] < CLIP_LEN:
        clip = np.vstack([clip, clip[-1:]])
    clip = np.expand_dims(clip, axis=0)  # (1, CLIP_LEN, H, W, 3)
    preds = model.predict(clip, verbose=0)[0]
    label = int(np.argmax(preds))
    confidence = float(np.max(preds))
    return CLASS_LABELS.get(label, "unknown"), confidence

def detect_from_video(video_path, show=True, threshold=THRESHOLD):
    """
    Run I3D detection on a video file.
    Returns the final prediction and shows live overlay if show=True.
    """
    cap = cv2.VideoCapture(video_path)
    frame_buffer = []
    last_pred = "Collecting frames..."
    last_color = (0, 255, 255)
    last_conf = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_buffer.append(preprocess_frame(frame))
        text = f"Collecting {len(frame_buffer)}/{CLIP_LEN} frames..."
        color = (0, 255, 255)

        # Run prediction when clip is full
        if len(frame_buffer) == CLIP_LEN:
            last_pred, last_conf = run_prediction(frame_buffer, threshold=threshold)
            last_color = (0, 0, 255) if last_pred != "normal" else (0, 255, 0)
            frame_buffer = []  # reset buffer

        if show:
            output_frame = frame.copy()
            cv2.putText(output_frame, text, (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.putText(output_frame, f"Prediction: {last_pred} ({last_conf:.2f})", (35, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, last_color, 2)
            cv2.imshow("I3D Detection", output_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Handle leftover frames at the end
    if len(frame_buffer) > 0:
        final_pred, final_conf = run_prediction(frame_buffer, threshold=threshold)
        print(f"[INFO] Final leftover prediction: {final_pred} ({final_conf:.2f})")
        last_pred, last_conf = final_pred, final_conf

    cap.release()
    cv2.destroyAllWindows()
    return last_pred, last_conf
