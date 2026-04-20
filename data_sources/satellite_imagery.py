"""
satellite_imagery.py
Fetch Sentinel-2 imagery with cloud filtering and near-realtime fallback.
"""

import os
import shutil
import requests
import numpy as np
from PIL import Image, ImageEnhance
from io import BytesIO
from datetime import datetime, timedelta, timezone
import math
import re
import sys

from ports_config import load_ports, get_port

INSTANCE_ID = "8bfa6630-6f4a-4968-b260-7691ee655aa5"
OUTPUT_DIR  = "data_sources/satellite_images/"

WMS_LAYER  = "TRUE_COLOR"
IMG_WIDTH  = 2048
IMG_HEIGHT = 2048
MAX_CC     = 10


# -------------------------------
# Helpers
# -------------------------------

def latlon_to_webmercator(lat, lon):
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34 / 180
    return x, y


def clear_output_dir():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

def get_token():
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


def remove_watermark(img: np.ndarray):
    return img[:-60, :, :]


def sanitize_filename(name: str):
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.replace(" ", "_"))


def enhance_image(img: np.ndarray):
    pil_img = Image.fromarray(img)

    # Increase contrast
    pil_img = ImageEnhance.Contrast(pil_img).enhance(1.5)

    # Slight brightness boost
    pil_img = ImageEnhance.Brightness(pil_img).enhance(1.1)

    return np.array(pil_img)


# -------------------------------
# Core Fetch Function
# -------------------------------

def fetch_image_for_date(port, port_name, date, token):
    min_lat = float(port['min_lat'])
    max_lat = float(port['max_lat'])
    min_lon = float(port['min_lon'])
    max_lon = float(port['max_lon'])

    min_x, min_y = latlon_to_webmercator(min_lat, min_lon)
    max_x, max_y = latlon_to_webmercator(max_lat, max_lon)

    bbox = f"{min_x},{min_y},{max_x},{max_y}"

    url = (
        f"https://sh.dataspace.copernicus.eu/ogc/wms/{INSTANCE_ID}"
        f"?SERVICE=WMS&REQUEST=GetMap"
        f"&LAYERS={WMS_LAYER}"
        f"&FORMAT=image/png"
        f"&WIDTH={IMG_WIDTH}&HEIGHT={IMG_HEIGHT}"
        f"&CRS=EPSG:3857"
        f"&BBOX={bbox}"
        f"&TIME={date}"
        f"&MAXCC={MAX_CC}"
    )

    print(f"[TRY] {port_name} @ {date}")

    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})

    if response.status_code != 200:
        return None

    img = np.array(Image.open(BytesIO(response.content)).convert("RGB"))
    img = remove_watermark(img)

    # Reject bad images
    if img.mean() < 20:
        print(f"[SKIP] Too dark/cloudy ({img.mean():.2f})")
        return None

    img = enhance_image(img)

    safe_name = sanitize_filename(port_name)
    path = os.path.join(OUTPUT_DIR, f"{safe_name}_{date}.png")

    Image.fromarray(img).save(path)
    print(f"[SAVE] {path}")

    return path


# -------------------------------
# Near-Realtime Logic
# -------------------------------

def get_realtime_image(port_name: str):
    port = get_port(port_name)
    token = get_token()

    #search last 10 days (most recent first)
    for days_back in range(0, 10):
        date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

        path = fetch_image_for_date(port, port_name, date, token)

        if path:
            print(f"[SUCCESS] Using {date}")
            return path

    print(f"[FAIL] No good image found for {port_name}")
    return None


# -------------------------------
# Multi-Port Processing
# -------------------------------

def get_all_ports_imagery():
    clear_output_dir()

    ports_df = load_ports()
    results = {}

    for _, row in ports_df.iterrows():
        port_name = row["port_name"]

        try:
            path = get_realtime_image(port_name)
            results[port_name] = path
        except Exception as e:
            print(f"[ERROR] {port_name}: {e}")
            results[port_name] = None

    return results


# -------------------------------
# Entry Point
# -------------------------------

if __name__ == "__main__":
    clear_output_dir()
    get_realtime_image("Port of Houston")