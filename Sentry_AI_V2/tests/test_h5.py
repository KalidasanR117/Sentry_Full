# test_local.py
import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from collections import deque
import glob

# -------------------- Config --------------------
TEST_FOLDER = "./tests"
MODEL_PATH = "./models/modelnew.h5"
OUTPUT_DIR = "./output"
FRAME_SIZE = (128, 128)
DEQUE_LEN = 128
THRESHOLD = 0.5

# -------------------- Prepare output --------------------
if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

# -------------------- Load model --------------------
print("[INFO] Loading model ...")
model = load_model(MODEL_PATH, compile=False)
print("[INFO] Model loaded successfully.")

# -------------------- Collect video paths --------------------
VIDEO_PATHS = glob.glob(os.path.join(TEST_FOLDER, "*.mp4")) + \
              glob.glob(os.path.join(TEST_FOLDER, "*.gif"))
VIDEO_PATHS.sort()
print("Files to test:", VIDEO_PATHS)

# -------------------- Video processing --------------------
def process_video(video_path):
    print(f"[INFO] Processing: {video_path}")
    Q = deque(maxlen=DEQUE_LEN)
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
        # Preprocess frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, FRAME_SIZE).astype("float32") / 255.0
        frame_input = np.expand_dims(frame_resized, axis=0)

        # Predict
        preds = model.predict(frame_input, verbose=0)[0]
        Q.append(preds)
        avg_preds = np.array(Q).mean(axis=0)

        # Determine label
        label = 1 if avg_preds[0] > THRESHOLD else 0  # 1=Violence, 0=NonViolence
        text = "Violence" if label else "NonViolence"
        color = (0, 0, 255) if label else (0, 255, 0)

        # Put text on frame
        cv2.putText(output_frame, text, (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.25, color, 3)

        # Initialize video writer
        if writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            output_path = os.path.join(OUTPUT_DIR, os.path.basename(video_path))
            writer = cv2.VideoWriter(output_path, fourcc, 30, (W, H), True)

        writer.write(output_frame)
        cv2.imshow("Output", output_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vs.release()
    writer.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Saved output video to {output_path}")

# -------------------- Real-time Camera processing --------------------
def process_camera(camera_index=0):
    print("[INFO] Starting camera feed...")
    Q = deque(maxlen=DEQUE_LEN)
    vs = cv2.VideoCapture(camera_index)

    if not vs.isOpened():
        print("[ERROR] Cannot access camera.")
        return

    while True:
        grabbed, frame = vs.read()
        if not grabbed:
            break

        output_frame = frame.copy()
        # Preprocess frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, FRAME_SIZE).astype("float32") / 255.0
        frame_input = np.expand_dims(frame_resized, axis=0)

        # Predict
        preds = model.predict(frame_input, verbose=0)[0]
        Q.append(preds)
        avg_preds = np.array(Q).mean(axis=0)

        # Determine label
        label = 1 if avg_preds[0] > THRESHOLD else 0
        text = "Violence" if label else "NonViolence"
        color = (0, 0, 255) if label else (0, 255, 0)

        # Put text on frame
        cv2.putText(output_frame, text, (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.25, color, 3)

        cv2.imshow("Camera Feed", output_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vs.release()
    cv2.destroyAllWindows()
    print("[INFO] Camera feed stopped.")

# -------------------- Run --------------------
if __name__ == "__main__":
    # # Run on test videos
    # for video in VIDEO_PATHS:
    #     if os.path.exists(video):
    #         process_video(video)
    #     else:
    #         print(f"[WARN] {video} not found!")

    # Run real-time camera after video tests
    process_camera()
