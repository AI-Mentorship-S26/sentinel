from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Import Kshiti's Model Logic
from predict_risk import run_sentinel_assessment

# Import YOUR (Ira's) Card Logic
from risk_engine import get_detailed_risk_assessment

app = FastAPI(title="Sentinel Maritime Intelligence API")

# --- CORS Settings ---
# Allows your React/Figma-coded frontend to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PortRequest(BaseModel):
    port_name: str

@app.get("/")
def home():
    return {"status": "Sentinel System Online", "version": "1.1.0"}

@app.post("/predict")
def predict_port_risk(request: PortRequest):
    """
    Combines the Random Forest Global Model with 
    Ira's Detailed Risk Assessment Cards.
    """
    print(f"🚀 Processing full assessment for: {request.port_name}")
    
    # 1. Get the Overall Port Risk (Kshiti's part)
    # This returns: port_name, overall_risk_level, risk_score_numeric, etc.
    overall_data = run_sentinel_assessment(request.port_name)
    
    if not overall_data:
        raise HTTPException(status_code=404, detail="Port data not found")

    # 2. Get the Detailed Assessment Cards (Ira's part)
    # For now, we pass dummy values. Later, you'll plug in live crime/weather variables.
    mock_payload = {
        "wind_speed": 12,        # Low Risk
        "recent_thefts": 3,      # Moderate Risk (Matches Figma)
        "labor_sentiment": 0.1   # Low Risk
    }
    
    cards = get_detailed_risk_assessment(request.port_name, mock_payload)

    # 3. Combine everything into one JSON response
    final_response = {
        "summary": overall_data,
        "risk_assessment_cards": cards
    }
        
    return final_response

if __name__ == "__main__":
    import uvicorn
    # Runs the server on http://127.0.0.1:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)