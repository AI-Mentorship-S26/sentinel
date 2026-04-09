"""
satellite_imagery.py
Data source: Copernicus / Sentinel-2 L2A True Color via WMS.
Provides get_satellite_imagery(port_name) which returns a PNG file path.
"""

import os
import shutil
import requests
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta, timezone
from ports_config import load_ports, get_port

INSTANCE_ID = "8bfa6630-6f4a-4968-b260-7691ee655aa5"
OUTPUT_DIR = "C:/Users/laxmi/New folder/sentinel2_output"


def clear_output_dir(port_name: str = None):
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    if port_name:
        print(f"[SATELLITE] Cleared output folder for: {port_name}")
    else:
        print(f"[SATELLITE] Cleared output folder: {OUTPUT_DIR}")


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
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_satellite_imagery(port_name: str, date: str = None) -> str | None:
    """
    Fetches latest Sentinel-2 true-color imagery for a given port.
    Always returns the most recent image regardless of cloud cover.

    Args:
        port_name: Must match a port_name in ports.csv
        date:      Optional end date "YYYY-MM-DD". Defaults to latest available.

    Returns:
        Path to saved PNG file, or None if fetch failed.
    """
    clear_output_dir(port_name)
    end_date = date if date else get_latest_date()
    start_date = get_start_date()

    token = get_token()
    port = get_port(port_name)

    url = (
        f"https://sh.dataspace.copernicus.eu/ogc/wms/{INSTANCE_ID}"
        f"?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS=TRUE_COLOR"
        f"&FORMAT=image/png&WIDTH=2048&HEIGHT=2048&CRS=EPSG:4326"
        f"&BBOX={port['min_lat']},{port['min_lon']},{port['max_lat']},{port['max_lon']}"
        f"&TIME={start_date}/{end_date}"
        f"&MAXCC=100"
    )

    print(f"[SATELLITE] Fetching {port_name} ({start_date} to {end_date})...")
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)

    if response.status_code != 200:
        print(f"[ERROR] {port_name}: HTTP {response.status_code}")
        return None

    img = np.array(Image.open(BytesIO(response.content)))
    safe_name = port_name.replace(" ", "_").replace("/", "-")
    save_path = os.path.join(OUTPUT_DIR, f"{safe_name}_{end_date}.png")

    plt.figure(figsize=(10, 10))
    plt.imshow(img)
    plt.axis("off")
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.savefig(save_path, bbox_inches="tight", pad_inches=0)
    plt.close()

    print(f"[SATELLITE] Saved: {save_path}")
    return save_path


def get_all_ports_imagery(date: str = None) -> dict:
    """Fetches imagery for every port in ports.csv."""
    clear_output_dir()
    df = load_ports()
    return {row["port_name"]: get_satellite_imagery(row["port_name"], date=date)
            for _, row in df.iterrows()}


if __name__ == "__main__":
    get_satellite_imagery("Port of Houston")  # test single port
    # get_all_ports_imagery()               # uncomment for all ports