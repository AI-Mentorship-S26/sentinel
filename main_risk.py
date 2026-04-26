from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from predict_risk import run_sentinel_assessment
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sentinel Maritime Intelligence API")

# --- CORS Settings ---
# This allows your React/HTML frontend to talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define what the request from your frontend looks like
class PortRequest(BaseModel):
    port_name: str

@app.get("/")
def home():
    return {"status": "Sentinel System Online", "version": "1.0.0"}

@app.post("/predict")
def predict_port_risk(request: PortRequest):
    """
    Endpoint that takes a port name and returns the 
    RandomForest aggregated risk assessment.
    """
    print(f"🚀 API Request received for: {request.port_name}")
    
    # Call your existing prediction logic
    result = run_sentinel_assessment(request.port_name)
    
    if not result:
        raise HTTPException(status_code=404, detail="Port data could not be retrieved")
        
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)