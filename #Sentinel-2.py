#Sentinel-2 

import os
from datetime import datetime, timedelta
from sentinelhub import (
    SHConfig, BBox, CRS, SentinelHubRequest,
    DataCollection, MimeType, bbox_to_dimensions
)

# ── Auth ──────────────────────────────────────────────
config = SHConfig()
config.sh_client_id     = os.getenv("SH_CLIENT_ID")
config.sh_client_secret = os.getenv("SH_CLIENT_SECRET")

# ── Areas of Interest ─────────────────────────────────
PORTS = {
    "Port of Houston":        [-95.35, 29.55, -94.85, 29.85],
    "Port of Corpus Christi": [-97.50, 27.75, -97.00, 28.00],
    "Port of Brownsville":    [-97.50, 25.90, -97.10, 26.10],
}

# ── Evalscript: true-color RGB ────────────────────────
evalscript = """
//VERSION=3
function setup() {
    return { input: ["B04", "B03", "B02"], output: { bands: 3 } };
}
function evaluatePixel(sample) {
    return [3.5 * sample.B04, 3.5 * sample.B03, 3.5 * sample.B02];
}
"""

# ── Fetch image for one port ──────────────────────────
def fetch_port_image(name, bbox_coords, date):
    bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    size = bbox_to_dimensions(bbox, resolution=10)
    time_interval = (date - timedelta(days=15), date)  # 15-day window for cloud-free image

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A,
            time_interval=time_interval,
            mosaicking_order="leastCC"
        )],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        size=size,
        config=config
    )

    image = request.get_data()[0]  # numpy array (H, W, 3)
    print(f"{name}: {image.shape}")
    return image

# ── Run for all ports ─────────────────────────────────
today = datetime.utcnow()
images = {name: fetch_port_image(name, bbox, today) for name, bbox in PORTS.items()}