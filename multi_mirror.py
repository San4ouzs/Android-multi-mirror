
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import threading
import time
import queue
from typing import List, Tuple, Optional

import cv2
import numpy as np

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # Defaults
    cfg.setdefault("fps", 5)
    cfg.setdefault("cols", 2)
    cfg.setdefault("max_width", 540)
    cfg.setdefault("adb_path", "adb")
    return cfg

def run_adb_screencap(adb_path: str, serial: str, out_q: queue.Queue, stop_evt: threading.Event, fps: int):
    """Continuously capture PNG frames from a device and push ndarray frames to a queue."""
    min_interval = 1.0 / max(1, fps)
    while not stop_evt.is_set():
        start_t = time.time()
        try:
            # Use exec-out screencap -p to get a PNG frame
            proc = subprocess.Popen(
                [adb_path, "-s", serial, "exec-out", "screencap", "-p"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            png = proc.stdout.read()
            proc.stdout.close()
            proc.wait(timeout=5)
            if not png:
                raise RuntimeError("Empty frame")
            # Decode PNG to ndarray
            arr = np.frombuffer(png, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError("Decode error")
            out_q.put(img, block=False)
        except Exception as e:
            # Signal a black frame on error (optional), then backoff a bit
            out_q.put(None)  # indicate drop
            time.sleep(0.4)
        # throttle
        elapsed = time.time() - start_t
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

def make_grid(images: List[Optional[np.ndarray]], cols: int, max_width: int) -> np.ndarray:
    # Determine tile size: scale each image to max_width while preserving aspect
    tiles = []
    for img in images:
        if img is None:
            # Create a placeholder tile (black)
            tiles.append(np.zeros((400, max_width, 3), dtype=np.uint8))
            continue
        h, w = img.shape[:2]
        scale = min(1.0, max_width / float(w)) if max_width > 0 else 1.0
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        tiles.append(resized)

    # Normalize tiles to same height per row
    rows = []
    for i in range(0, len(tiles), cols):
        row_tiles = tiles[i:i+cols]
        max_h = max(t.shape[0] for t in row_tiles)
        norm_row = []
        for t in row_tiles:
            h, w = t.shape[:2]
            if h < max_h:
                pad = np.zeros((max_h - h, w, 3), dtype=np.uint8)
                t = np.vstack([t, pad])
            norm_row.append(t)
        # Pad columns to equal width
        max_w = max(t.shape[1] for t in norm_row)
        norm_row2 = []
        for t in norm_row:
            h, w = t.shape[:2]
            if w < max_w:
                pad = np.zeros((h, max_w - w, 3), dtype=np.uint8)
                t = np.hstack([t, pad])
            norm_row2.append(t)
        rows.append(np.hstack(norm_row2))
    grid = np.vstack(rows) if rows else np.zeros((400, max_width, 3), dtype=np.uint8)
    return grid

def main():
    cfg = load_config()
    devices: List[str] = cfg.get("devices", [])
    if not devices:
        print("No devices listed in config.json under 'devices'. Add ADB serials or ip:port from 'adb connect'.")
        return
    cols: int = max(1, int(cfg.get("cols", 2)))
    fps: int = max(1, int(cfg.get("fps", 5)))
    max_width: int = int(cfg.get("max_width", 540))
    adb_path: str = cfg.get("adb_path", "adb")

    # Queues and threads per device
    threads = []
    qs = []
    stops = []
    latest_frames = [None for _ in devices]

    for idx, serial in enumerate(devices):
        q = queue.Queue(maxsize=1)
        qs.append(q)
        stop_evt = threading.Event()
        stops.append(stop_evt)
        th = threading.Thread(target=run_adb_screencap, args=(adb_path, serial, q, stop_evt, fps), daemon=True)
        th.start()
        threads.append(th)

    cv2.namedWindow("Android Multi‑Mirror", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Android Multi‑Mirror", 1280, 720)

    try:
        while True:
            # Drain queues
            for i, q in enumerate(qs):
                try:
                    frame = q.get_nowait()
                    if frame is None:
                        # Keep existing frame; indicate dropout by border later maybe
                        pass
                    else:
                        latest_frames[i] = frame
                except queue.Empty:
                    pass

            # Ensure we have some image for each tile
            show_frames = [f if f is not None else np.zeros((400, max_width, 3), dtype=np.uint8) for f in latest_frames]
            grid = make_grid(show_frames, cols=cols, max_width=max_width)
            # Draw labels
            y = 30
            # Optional: add simple device labels on each tile border (skipped for performance)

            cv2.imshow("Android Multi‑Mirror", grid)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q')):
                break
    finally:
        for e in stops:
            e.set()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
