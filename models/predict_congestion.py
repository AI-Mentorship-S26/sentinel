from pathlib import Path
import sys

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "congestion_rf.joblib"

FEATURE_COLUMNS = [
    "Total_TEU",
    "AVERAGE of Avg. Berthing Time (hr)",
    "Median Berthing Time (hour)",
    "Calls",
]


def load_model(model_path: Path):
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return joblib.load(model_path)


def predict_congestion(model, total_teu, avg_berthing, median_berthing, calls):
    input_df = pd.DataFrame([{
        "Total_TEU": total_teu,
        "AVERAGE of Avg. Berthing Time (hr)": avg_berthing,
        "Median Berthing Time (hour)": median_berthing,
        "Calls": calls
    }])

    prediction = model.predict(input_df[FEATURE_COLUMNS])[0]
    return prediction


def get_congestion_score(port_name: str):
    try:
        model = load_model(MODEL_PATH)

        df = pd.read_csv(BASE_DIR / "final_dataset.csv")

        port_data = df[df["Port"] == port_name]

        if port_data.empty:
            print(f"Port not found: {port_name}")
            return

        prediction = model.predict(port_data[FEATURE_COLUMNS])[0]

        print("\n=== CONGESTION PREDICTION ===")
        print(f"Port: {port_name}")
        print(f"Predicted congestion score: {prediction:.6f}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)