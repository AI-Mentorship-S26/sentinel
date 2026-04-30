from pathlib import Path
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from data_sources.combined_data import get_combined_sentinel_data

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "sentinel_model.pkl"

MODEL = None

# 1. Load the Global Model
try:
    MODEL = joblib.load(MODEL_PATH)
    print("✅ Sentinel Brain Loaded Successfully.")
except Exception as e:
    print(f"❌ Error: sentinel_model.pkl not found or incompatible: {e}")

def run_sentinel_assessment(port_name):
    if MODEL is None:
        return {
            "port_name": port_name,
            "overall_risk_level": "Low",
            "risk_score_numeric": 0,
            "vessels_tracked": 0,
            "message": "Sentinel model not loaded."
        }
    
    print("\n\n=== VESSEL CONGESTION PREDICTION ===")
    print(f"\n🕵️ Sentinel Aggregation active for: {port_name}")
    
    try:
        df_live = get_combined_sentinel_data(port_name)
    except Exception as e:
        print(f"❌ Error fetching live data: {e}")
        return None

    # --- THE FIX: Check if we actually got data columns ---
    if df_live.empty or len(df_live.columns) < 2:
        print(f"⚠️ No active ship telemetry found for {port_name} right now.")
        return {
            "port_name": port_name,
            "overall_risk_level": "Low",
            "risk_score_numeric": 0,
            "vessels_tracked": 0,
            "message": "No active vessels detected."
        }

    # 3. Preprocess to match training features
    cols_to_drop = ['mmsi', 'vessel_name', 'timestamp', 'eta_utc', 'is_delayed']
    X = df_live.drop(columns=[c for c in cols_to_drop if c in df_live.columns])

    # 4. Handle Categorical Data
    le = LabelEncoder()
    for col in X.select_dtypes(include=['object', 'string']).columns:
        X[col] = le.fit_transform(X[col].astype(str))

    # --- THE FIX: Ensure we only grab columns that the model expects AND exist in X ---
    expected_features = MODEL.feature_names_in_
    missing_cols = [col for col in expected_features if col not in X.columns]
    
    if missing_cols:
        print(f"⚠️ Missing columns from API: {missing_cols}. Filling with 0.")
        for col in missing_cols:
            X[col] = 0

    # Ensure order matches exactly
    X = X[list(expected_features)] 

    # 5. Make Predictions
    ship_predictions = MODEL.predict(X)
    
    # 6. Aggregate Metrics
    avg_risk_score = ship_predictions.mean()
    
    if avg_risk_score < 0.25:
        alert_level = "Low"
    elif avg_risk_score < 0.55:
        alert_level = "Moderate"
    else:
        alert_level = "High"

    port_summary = {
        "port_name": port_name,
        "overall_risk_level": alert_level,
        "risk_score_numeric": round(avg_risk_score * 100, 1),
        "vessels_tracked": len(df_live),
        "high_risk_ships": int((ship_predictions > 0.5).sum())
    }

    print("\n--- Sentinel Port Summary ---")
    print(f"Port: {port_summary['port_name']}")
    print(f"Risk: {port_summary['overall_risk_level']} ({port_summary['risk_score_numeric']}%)")
    
    return port_summary

if __name__ == "__main__":
    # Test manually with your dropdown options
    target = input("Enter port to scan (e.g., Port of Los Angeles): ").strip()
    summary = run_sentinel_assessment(target)
    
    if summary:
        print("\nJSON Response for Frontend:")
        print(summary)