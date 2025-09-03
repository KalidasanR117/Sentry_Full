# test_and_camera.py
import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import glob

# -------------------- Config --------------------
TEST_FOLDER = "./tests"   # your test folder
MODEL_PATH = "./models/ucf_crime_heavy_model.keras"
OUTPUT_DIR = "./output"
FRAME_SIZE = (128, 128)   # must match training input size
CLIP_LEN = 40             # number of frames per clip
THRESHOLD = 0.5

# Update this mapping according to your model
CLASS_LABELS = {
    0: "Normal",
    1: "Robbery",
    2: "Fighting"
}

# -------------------- Prepare output --------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------- Load model --------------------
print("[INFO] Loading model ...")
model = load_model(MODEL_PATH, compile=False)
print("[INFO] Model loaded successfully.")

# -------------------- Collect video paths --------------------
VIDEO_PATHS = []
for ext in ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.gif"]:
    VIDEO_PATHS.extend(glob.glob(os.path.join(TEST_FOLDER, ext)))
VIDEO_PATHS.sort()
print("[INFO] Files to test:", VIDEO_PATHS)

# -------------------- Preprocess --------------------
def preprocess_frame(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, FRAME_SIZE).astype("float32") / 255.0
    return frame_resized

# -------------------- Prediction helper --------------------
def run_prediction(frame_buffer):
    """Run model prediction, pad if not enough frames."""
    clip = np.array(frame_buffer)

    # Pad last frame until we reach CLIP_LEN
    while clip.shape[0] < CLIP_LEN:
        clip = np.vstack([clip, clip[-1:]])

    clip = np.expand_dims(clip, axis=0)  # (1,40,128,128,3)

    preds = model.predict(clip, verbose=0)[0]
    label = int(np.argmax(preds))
    confidence = float(np.max(preds))
    label_name = CLASS_LABELS.get(label, f"Class {label}")
    return f"{label_name} ({confidence:.2f})", label

# -------------------- Video Processing --------------------
def process_video(video_path):
    print(f"[INFO] Processing: {video_path}")
    frame_buffer = []
    last_prediction = "Collecting frames..."
    last_color = (0, 255, 255)

    vs = cv2.VideoCapture(video_path)
    writer = None
    (W, H) = (None, None)

    while True:
        grabbed, frame = vs.read()
        if not grabbed:
            break

        if W is None or H is None:
            (H, W) = frame.shape[:2]

        output_frame = frame.copy()
        frame_buffer.append(preprocess_frame(frame))

        text = f"Collecting {len(frame_buffer)}/{CLIP_LEN} frames..."
        color = (0, 255, 255)

        if len(frame_buffer) == CLIP_LEN:
            last_prediction, label = run_prediction(frame_buffer)
            last_color = (0, 0, 255) if label in [1, 2] else (0, 255, 0)
            frame_buffer = []  # reset

        cv2.putText(output_frame, text, (35, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        cv2.putText(output_frame, f"Prediction: {last_prediction}", (35, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, last_color, 2)

        if writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            output_path = os.path.join(
                OUTPUT_DIR, os.path.basename(video_path).replace(".gif", ".avi")
            )
            writer = cv2.VideoWriter(output_path, fourcc, 30, (W, H), True)

        writer.write(output_frame)
        cv2.imshow("Video Output", output_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # 🔑 Handle leftover frames
    if len(frame_buffer) > 0:
        final_pred, label = run_prediction(frame_buffer)
        print(f"[INFO] Final leftover prediction for {video_path}: {final_pred}")

    vs.release()
    if writer:
        writer.release()
        print(f"[INFO] Saved output video to {output_path}")
    cv2.destroyAllWindows()

# -------------------- Camera Processing --------------------
def process_camera():
    cap = cv2.VideoCapture(0)
    frame_buffer = []
    last_prediction = "Collecting frames..."
    last_color = (0, 255, 255)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_buffer.append(preprocess_frame(frame))

        text = f"Collecting {len(frame_buffer)}/{CLIP_LEN} frames..."
        color = (0, 255, 255)

        if len(frame_buffer) == CLIP_LEN:
            last_prediction, label = run_prediction(frame_buffer)
            last_color = (0, 0, 255) if label in [1, 2] else (0, 255, 0)
            frame_buffer = []  # reset

        cv2.putText(frame, text, (35, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        cv2.putText(frame, f"Prediction: {last_prediction}", (35, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, last_color, 2)

        cv2.imshow("Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # 🔑 Handle leftover frames
    if len(frame_buffer) > 0:
        final_pred, label = run_prediction(frame_buffer)
        print(f"[INFO] Final leftover prediction (camera): {final_pred}")

    cap.release()
    cv2.destroyAllWindows()

# -------------------- Run --------------------
if __name__ == "__main__":
    # Run on test videos
    for video in VIDEO_PATHS:
        process_video(video)

    # Run real-time camera after video tests
    # process_camera()
