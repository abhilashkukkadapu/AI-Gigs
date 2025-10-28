from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import cv2
from loguru import logger


# Uses OpenCV DNN face detector with pre-trained model if available; otherwise falls back to Haar cascades

HAAR_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def detect_faces_samples(input_path: Path, sample_stride_s: float = 1.0, max_samples: int = 200) -> List[Dict]:
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    stride_frames = max(1, int(sample_stride_s * fps))

    face_cascade = cv2.CascadeClassifier(HAAR_PATH)

    results: List[Dict] = []
    frame_idx = 0
    samples = 0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        timestamp = frame_idx / fps
        for (x, y, w, h) in faces:
            results.append({"t": round(timestamp, 3), "bbox": [int(x), int(y), int(w), int(h)]})
        samples += 1
        if samples >= max_samples:
            break
        frame_idx += stride_frames

    cap.release()
    logger.info("Collected {} face samples across ~{}s", len(results), round(total_frames / max(fps, 1.0), 1))
    return results
