from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# Add models + aggregator paths
sys.path.append(str(BASE_DIR / "models"))

# Import aggregator instead of direct model
from models.score_aggregator import get_final_port_score

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