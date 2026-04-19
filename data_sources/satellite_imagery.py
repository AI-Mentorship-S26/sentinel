"""
satellite_imagery.py
Fetches Sentinel-2 L1C-TCI imagery aligned with
mayrajeo/marine-vessel-yolo model requirements.

FIXED:
- Uses EPSG:3857 (Web Mercator) to avoid WMS 400 errors
- Correct bounding box projection
"""

import os
import shutil
import requests
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta, timezone
import math

from ports_config import load_ports, get_port

INSTANCE_ID = "8bfa6630-6f4a-4968-b260-7691ee655aa5"
OUTPUT_DIR  = "data_sources/satellite_images/"

# -------------------------------------------------------------------
# Model-aligned settings
# -------------------------------------------------------------------
WMS_LAYER  = "TRUE_COLOR"

# MUST match training patch size
IMG_WIDTH  = 320
IMG_HEIGHT = 320

MAX_CC = 20
BBOX_EXPAND = 0.01


# -------------------------------------------------------------------
# Coordinate conversion (FIX)
# -------------------------------------------------------------------
def latlon_to_webmercator(lat, lon):
    """Convert lat/lon to EPSG:3857"""
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34 / 180
    return x, y


def clear_output_dir(port_name: str = None):
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    label = port_name if port_name else OUTPUT_DIR
    print(f"[SATELLITE] Cleared output folder: {label}")


def get_latest_date() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")


def get_start_date() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")


def get_token() -> str:
    response = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("SH_CLIENT_ID"),
            "client_secret": os.getenv("SH_CLIENT_SECRET"),
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_satellite_imagery(port_name: str, date: str = None) -> str | None:
    clear_output_dir(port_name)

    end_date   = date if date else get_latest_date()
    start_date = get_start_date()

    token = get_token()
    port  = get_port(port_name)

    # ---------------------------------------------------------------
    # Get and validate bbox
    # ---------------------------------------------------------------
    min_lat = float(port['min_lat']) - BBOX_EXPAND
    max_lat = float(port['max_lat']) + BBOX_EXPAND
    min_lon = float(port['min_lon']) - BBOX_EXPAND
    max_lon = float(port['max_lon']) + BBOX_EXPAND

    # Ensure correct ordering
    if min_lat > max_lat:
        min_lat, max_lat = max_lat, min_lat
    if min_lon > max_lon:
        min_lon, max_lon = max_lon, min_lon

    print("\n[DEBUG] Lat/Lon BBOX:")
    print(min_lat, min_lon, max_lat, max_lon)

    # ---------------------------------------------------------------
    # Convert to EPSG:3857 (FIX)
    # ---------------------------------------------------------------
    min_x, min_y = latlon_to_webmercator(min_lat, min_lon)
    max_x, max_y = latlon_to_webmercator(max_lat, max_lon)

    bbox = f"{min_x},{min_y},{max_x},{max_y}"

    print("[DEBUG] WebMercator BBOX:")
    print(bbox)

    # ---------------------------------------------------------------
    # Build WMS request
    # ---------------------------------------------------------------
    url = (
        f"https://sh.dataspace.copernicus.eu/ogc/wms/{INSTANCE_ID}"
        f"?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS={WMS_LAYER}"
        f"&FORMAT=image/png"
        f"&WIDTH={IMG_WIDTH}&HEIGHT={IMG_HEIGHT}"
        f"&CRS=EPSG:3857"
        f"&BBOX={bbox}"
        f"&TIME={start_date}/{end_date}"
        f"&MAXCC={MAX_CC}"
    )

    print(f"\n[SATELLITE] Fetching {port_name} | {IMG_WIDTH}x{IMG_HEIGHT}px")

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"[ERROR] {port_name}: HTTP {response.status_code}")
        print(response.text)  # helpful debug
        return None

    img = np.array(Image.open(BytesIO(response.content)).convert("RGB"))

    safe_name = port_name.replace(" ", "_").replace("/", "-")
    save_path = os.path.join(OUTPUT_DIR, f"{safe_name}_{end_date}.png")

    fig, ax = plt.subplots(1, figsize=(IMG_WIDTH / 100, IMG_HEIGHT / 100), dpi=100)
    ax.imshow(img)
    ax.axis("off")

    plt.subplots_adjust(0, 0, 1, 1)
    plt.savefig(save_path, bbox_inches="tight", pad_inches=0)
    plt.close()

    print(f"[SATELLITE] Saved: {save_path}")
    return save_path


def get_all_ports_imagery(date: str = None) -> dict:
    clear_output_dir()
    df = load_ports()

    return {
        row["port_name"]: get_satellite_imagery(row["port_name"], date)
        for _, row in df.iterrows()
    }


if __name__ == "__main__":
    get_satellite_imagery("Port of Houston")