"""
ship_detection.py
Ship detection using mayrajeo/marine-vessel-yolo (YOLO11)
"""

from ultralytics import YOLO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image
import os
import torch

# -------------------------------------------------------------------
# Model config
# -------------------------------------------------------------------
MODEL_URL  = "https://huggingface.co/mayrajeo/marine-vessel-yolo/resolve/main/yolo11s_tci.pt"
MODEL_FILE = "models/yolo11s_tci.pt"

IMAGE_DIR  = "data_sources/satellite_images"
OUTPUT_DIR = "outputs/detections"

os.makedirs("models", exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------------------------
# Inference settings (aligned with model)
# -------------------------------------------------------------------
INFER_IMGSZ = 640   # model upsamples 320 → 640
INFER_CONF  = 0.25
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"


def load_model() -> YOLO:
    if not os.path.exists(MODEL_FILE):
        print("[MODEL] Downloading model...")
        model = YOLO(MODEL_URL)
        model.save(MODEL_FILE)
    else:
        print("[MODEL] Loading cached model...")
        model = YOLO(MODEL_FILE)

    model.to(DEVICE)
    print(f"[MODEL] Using device: {DEVICE}")
    return model


def detect_ships(image_path: str, model: YOLO) -> dict:
    print(f"[DETECT] {os.path.basename(image_path)}")

    results = model.predict(
        source=image_path,
        conf=INFER_CONF,
        imgsz=INFER_IMGSZ,
        device=DEVICE,
        verbose=False,
    )

    result = results[0]
    ship_count = len(result.boxes) if result.boxes is not None else 0

    print(f"[DETECT] Ships detected: {ship_count}")

    # Visualization
    img = np.array(Image.open(image_path).convert("RGB"))
    fig, ax = plt.subplots(1, figsize=(8, 8))
    ax.imshow(img)

    # Masks
    if result.masks is not None:
        for mask in result.masks.data:
            mask_np = mask.cpu().numpy()

            mask_resized = np.array(
                Image.fromarray((mask_np * 255).astype(np.uint8)).resize(
                    (img.shape[1], img.shape[0]), Image.NEAREST
                )
            ) / 255.0

            colored = np.zeros((*mask_resized.shape, 4))
            colored[mask_resized > 0.5] = [1, 0, 0, 0.4]
            ax.imshow(colored)

    # Boxes
    if result.boxes is not None:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()

            rect = patches.Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                linewidth=1.5,
                edgecolor="red",
                facecolor="none"
            )
            ax.add_patch(rect)

            ax.text(
                x1, y1 - 3,
                f"{conf:.2f}",
                color="white",
                fontsize=7,
                bbox=dict(facecolor="black", alpha=0.5, pad=1)
            )

    ax.axis("off")

    save_path = os.path.join(
        OUTPUT_DIR,
        os.path.basename(image_path).replace(".png", "_detected.png")
    )

    plt.savefig(save_path, bbox_inches="tight", pad_inches=0)
    plt.close()

    return {
        "ship_count": ship_count,
        "save_path": save_path
    }


def detect_ships_for_port(port_name: str, model: YOLO = None) -> dict:
    if model is None:
        model = load_model()

    safe_name = port_name.replace(" ", "_").replace("/", "-")

    matches = [
        f for f in os.listdir(IMAGE_DIR)
        if f.startswith(safe_name)
    ]

    if not matches:
        print(f"[ERROR] No image found for {port_name}")
        return {"ship_count": 0, "save_path": None}

    image_path = os.path.join(IMAGE_DIR, sorted(matches)[-1])
    return detect_ships(image_path, model)


if __name__ == "__main__":
    model = load_model()
    result = detect_ships_for_port("Port of Houston", model)

    print(f"\nShips: {result['ship_count']}")
    print(f"Output: {result['save_path']}")