"""
ship_detection.py
Ship detection using YOLO (marine-vessel-yolo)
"""

import matplotlib
matplotlib.use("Agg")

from ultralytics import YOLO
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image
from io import BytesIO
import os
import torch

MODEL_URL  = "https://huggingface.co/mayrajeo/marine-vessel-yolo/resolve/main/yolo11s_tci.pt"
MODEL_FILE = "models/yolo11s_tci.pt"
IMAGE_DIR = str(Path(__file__).resolve().parent.parent / "data_sources" / "satellite_images")


print("[CACHE] Starting preload...")

os.makedirs("models", exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

SHIP_MIN = 0
SHIP_MAX = 50


def normalize_ship_count(ship_count: int) -> float:
    if ship_count <= SHIP_MIN:
        return 0.0
    if ship_count >= SHIP_MAX:
        return 1.0
    return round((ship_count - SHIP_MIN) / (SHIP_MAX - SHIP_MIN), 4)


def load_model():
    if not os.path.exists(MODEL_FILE):
        model = YOLO(MODEL_URL)
        model.save(MODEL_FILE)
    else:
        model = YOLO(MODEL_FILE)
    model.to(DEVICE)
    return model


def detect_ships(image_path, model):
    print(f"[DETECT] {image_path}")

    img = np.array(Image.open(image_path).convert("RGB"))
    img = np.array(Image.fromarray(img).resize((2560, 2560)))

    H, W = img.shape[:2]
    patch_size = 320
    stride = 320
    all_boxes = []

    for y in range(0, H - patch_size, stride):
        for x in range(0, W - patch_size, stride):
            patch = img[y:y+patch_size, x:x+patch_size]

            results = model.predict(
                source=patch,
                conf=0.01,
                imgsz=640,
                device=DEVICE,
                verbose=False
            )

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                cls = int(box.cls[0].item()) if box.cls is not None else 0
                if cls != 0:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                all_boxes.append([x1 + x, y1 + y, x2 + x, y2 + y, conf])

    print(f"[DEBUG] Raw detections: {len(all_boxes)}")

    def nms(boxes, iou_threshold=0.4):
        if len(boxes) == 0:
            return []
        boxes = np.array(boxes)
        x1, y1, x2, y2, scores = boxes.T
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(boxes[i])
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            order = order[np.where(iou <= iou_threshold)[0] + 1]
        return keep

    final_boxes = nms(all_boxes)
    print(f"[DETECT] Ships detected: {len(final_boxes)}")

    # Draw boxes and return as BytesIO for streaming
    fig, ax = plt.subplots(1, figsize=(8, 8))
    ax.imshow(img)

    for (x1, y1, x2, y2, conf) in final_boxes:
        rect = patches.Rectangle(
            (x1, y1), x2 - x1, y2 - y1,
            linewidth=1.5, edgecolor="red", facecolor="none"
        )
        ax.add_patch(rect)
        ax.text(
            x1, y1 - 3, f"{conf:.2f}",
            color="white", fontsize=7,
            bbox=dict(facecolor="black", alpha=0.5, pad=1)
        )

    ax.axis("off")

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
    plt.close()
    buffer.seek(0)

    print(f"[SCORE] Congestion score: {normalize_ship_count(len(final_boxes))}")

    return {
        "ship_count":       len(final_boxes),
        "congestion_score": normalize_ship_count(len(final_boxes)),
        "image_buffer":     buffer
    }


def detect_latest(port_name, model=None):
    """Read the latest saved image for a port from the satellite_images folder."""
    if model is None:
        model = load_model()

    safe_name = (
        port_name
        .replace(" ", "_")
        .replace("/", "_")
        .replace("(", "_")
        .replace(")", "_")
    )

    files = [f for f in os.listdir(IMAGE_DIR) if f.startswith(safe_name)]

    if not files:
        return {"ship_count": 0, "congestion_score": 0.0, "image_buffer": None}

    path = os.path.join(IMAGE_DIR, sorted(files)[-1])
    return detect_ships(path, model)


def get_port_congestion_score(port_name: str, model=None) -> float:
    """
    Full pipeline: fetch image → save to folder → detect → return score.
    """
    from satellite_imagery import get_realtime_image

    if model is None:
        model = load_model()

    get_realtime_image(port_name)
    result = detect_latest(port_name, model=model)
    return result["congestion_score"]