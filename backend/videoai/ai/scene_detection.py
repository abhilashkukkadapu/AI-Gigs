from __future__ import annotations

from pathlib import Path
from typing import List

import cv2
import numpy as np
from loguru import logger


def detect_scenes(input_path: Path, threshold: float = 30.0, min_scene_len_s: float = 1.0) -> List[float]:
    """
    Extremely lightweight scene cut detector using HSV histogram differences.
    Returns a list of timestamps (in seconds) where a new scene begins (first scene at 0.0 included).
    """
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    prev_hist = None
    scene_starts = [0.0]
    last_scene_start = 0.0

    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        if prev_hist is not None:
            diff = cv2.compareHist(prev_hist.astype('float32'), hist.astype('float32'), cv2.HISTCMP_BHATTACHARYYA)
            # Convert to a pseudo percentage scale
            score = float(diff) * 100.0
            timestamp = frame_idx / fps
            if score > threshold and (timestamp - last_scene_start) >= min_scene_len_s:
                scene_starts.append(round(timestamp, 3))
                last_scene_start = timestamp
        prev_hist = hist
        frame_idx += 1

    cap.release()
    logger.info("Detected {} scenes in {} frames", len(scene_starts), frame_count)
    return scene_starts
