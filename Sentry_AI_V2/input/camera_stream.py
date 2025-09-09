import cv2
from collections import deque

CLIP_LEN = 40  # must match i3d_detector

def capture_frames(source=0):
    """
    Generator that yields frames and maintains a buffer for I3D clips.
    Returns a tuple: (current_frame, clip_buffer)
    """
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise Exception(f"Cannot open video source {source}")

    clip_buffer = deque(maxlen=CLIP_LEN)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Add frame to clip buffer
        clip_buffer.append(frame.copy())

        yield frame, list(clip_buffer)

    cap.release()
