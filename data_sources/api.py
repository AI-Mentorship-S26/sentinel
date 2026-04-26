from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "models"))

from predict_congestion import get_congestion_score

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API working"}

@app.get("/predict/{port_name}")
def predict(port_name: str):
    score = get_congestion_score(port_name)

    if score is None:
        return {"error": "Port not found"}

    return {
        "port": port_name,
        "congestion_score": float(score)
    }