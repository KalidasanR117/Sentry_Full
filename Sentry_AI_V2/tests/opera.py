# test_and_camera_torch_async.py
import os
import cv2
import glob
import torch
import numpy as np
import threading
from transformers import VideoMAEForVideoClassification

# -------------------- Config --------------------
TEST_FOLDER = "./tests"   # your test folder
OUTPUT_DIR = "./output"
FRAME_SIZE = (224, 224)   # must match VideoMAE input size
CLIP_LEN = 16             # number of frames per clip
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# -------------------- Label Mappings --------------------
CLASS_LABELS = {
    0: "Abuse", 1: "Arrest", 2: "Arson", 3: "Assault", 4: "Burglary",
    5: "Explosion", 6: "Fighting", 7: "Normal Videos", 8: "Road Accidents",
    9: "Robbery", 10: "Shooting", 11: "Shoplifting", 12: "Stealing", 13: "Vandalism"
}
REVERSE_LABELS = {v: k for k, v in CLASS_LABELS.items()}

# -------------------- Prepare output --------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------- Load model --------------------
print("[INFO] Loading model ...")
MODEL_NAME = "OPear/videomae-large-finetuned-UCF-Crime"
model = VideoMAEForVideoClassification.from_pretrained(
    MODEL_NAME,
    id2label=CLASS_LABELS,
    label2id=REVERSE_LABELS,
    ignore_mismatched_sizes=True,
).to(DEVICE)
model.eval()
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
    clip = np.array(frame_buffer)  # [T, H, W, C]

    while clip.shape[0] < CLIP_LEN:
        clip = np.vstack([clip, clip[-1:]])

    frames_tensor = torch.tensor(clip, dtype=torch.float32).permute(0, 3, 1, 2)  # [T, C, H, W]
    frames_tensor = frames_tensor.unsqueeze(0).to(DEVICE)  # [1, T, C, H, W]

    with torch.no_grad():
        outputs = model(frames_tensor)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        label = torch.argmax(probs, dim=-1).item()
        confidence = probs[0, label].item()

    label_name = model.config.id2label[label]
    return f"{label_name} ({confidence:.2f})", label

# -------------------- Async Prediction Thread --------------------
last_prediction = "Waiting for prediction..."
last_color = (0, 255, 255)
lock = threading.Lock()

def async_prediction(frame_buffer):
    global last_prediction, last_color
    try:
        print("[DEBUG] Running async prediction...")
        pred, label = run_prediction(frame_buffer)
        with lock:
            last_prediction = pred
            last_color = (0, 0, 255) if label != 7 else (0, 255, 0)  # Normal = green
        print(f"[INFO] Prediction updated: {pred}")
    except Exception as e:
        print(f"[ERROR] In async prediction: {e}")

# -------------------- Video Processing --------------------
def process_video(video_path):
    global last_prediction, last_color
    print(f"[INFO] Processing: {video_path}")
    frame_buffer = []

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

        if len(frame_buffer) == CLIP_LEN:
            frames_copy = list(frame_buffer)  # ✅ copy buffer safely
            threading.Thread(target=async_prediction, args=(frames_copy,)).start()
            frame_buffer = []  # reset

        # Overlay text
        with lock:
            cv2.putText(output_frame, f"Prediction: {last_prediction}", (35, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, last_color, 2)

        if writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            output_path = os.path.join(
                OUTPUT_DIR, os.path.basename(video_path).replace(".gif", ".mp4")
            )
            writer = cv2.VideoWriter(output_path, fourcc, 30, (W, H), True)

        writer.write(output_frame)
        cv2.imshow("Video Output", output_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    vs.release()
    if writer:
        writer.release()
        print(f"[INFO] Saved output video to {output_path}")
    cv2.destroyAllWindows()

# -------------------- Camera Processing --------------------
def process_camera():
    global last_prediction, last_color
    cap = cv2.VideoCapture(0)
    frame_buffer = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_buffer.append(preprocess_frame(frame))

        if len(frame_buffer) == CLIP_LEN:
            frames_copy = list(frame_buffer)
            threading.Thread(target=async_prediction, args=(frames_copy,)).start()
            frame_buffer = []  # reset

        # Overlay text
        with lock:
            cv2.putText(frame, f"Prediction: {last_prediction}", (35, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, last_color, 2)

        cv2.imshow("Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# -------------------- Run --------------------
if __name__ == "__main__":
    # Run on test videos
    for video in VIDEO_PATHS:
        process_video(video)

    # Run real-time camera after video tests
    # process_camera()
