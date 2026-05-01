from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os
import re
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = str(Path(__file__).resolve().parent / "satellite_images")
print(f"[DEBUG] IMAGE_DIR = {IMAGE_DIR}")

# Add models + aggregator paths
sys.path.insert(0, str(BASE_DIR / "models"))

# Import aggregator instead of direct model
from score_aggregator import get_final_port_score


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sanitize(port_name: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9_]", "_", port_name.replace(" ", "_").replace("-", "_"))
    return re.sub(r"_+", "_", result).strip("_")

@app.get("/")
def home():
    return {"message": "API working"}

@app.get("/predict")
def predict(port_name: str):
    score = get_final_port_score(port_name)

    if score is None:
        return {"error": "Port not found"}

    return {
        "port": port_name,
        "congestion_score": float(score)
    }


# # TEST ENDPOINT
# @app.get("/test-risk")
# def test_risk():
#     return {
#         "port": "Los Angeles",
#         "risks": {
#             "overall": "moderate",
#             "congestion": "high",
#             "crime": "low",
#             "weather": "moderate"
#         }
#     } 

@app.get("/image/{port_name}")
def get_port_image(port_name: str):
    key = sanitize(port_name)

    print(f"[DEBUG] key={key}")
    print(f"[DEBUG] files={os.listdir(IMAGE_DIR)}")
 
    files = [
        f for f in os.listdir(IMAGE_DIR)
        if re.sub(r"_+", "_", f).startswith(key)
    ]

    print(f"[DEBUG] matched={files}")

 
    if not files:
        raise HTTPException(
            status_code=404,
            detail=f"No image found for '{port_name}'"
        )
 
    # Pick the latest file
    latest = sorted(files)[-1]
    path = os.path.join(IMAGE_DIR, latest)
 
    return FileResponse(
        path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )