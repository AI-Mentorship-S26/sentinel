import argparse
import importlib.util
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data_sources" / "port_congestion_log.csv"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "congestion_rf.joblib"
DEFAULT_PORT = "Port of Houston"


def load_training_module():
    module_path = Path(__file__).resolve().parent / "train_congestion_model.py"
    spec = importlib.util.spec_from_file_location("port_congestion_train_module", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load training module from: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TRAINING_MODULE = load_training_module()
FEATURE_COLUMNS = TRAINING_MODULE.FEATURE_COLUMNS
REQUIRED_COLUMNS = TRAINING_MODULE.REQUIRED_COLUMNS
run_training = TRAINING_MODULE.run_training


def resolve_path(path_str: str, fallback: Path) -> Path:
    raw_path = Path(path_str) if path_str else fallback
    if raw_path.is_absolute():
        return raw_path
    return (PROJECT_ROOT / raw_path).resolve()


def to_congestion_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def make_message(port_name: str, level: str, score: float, traffic_count: int) -> str:
    return (
        f"{port_name} congestion is {level.upper()} "
        f"(score={score:.2f}, traffic_count={traffic_count})."
    )


def validate_and_prepare_data(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Congestion CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV is empty: {csv_path}")

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV missing required columns: {missing_cols}")

    numeric_cols = ["vessel_count", "anchored_count", "moored_count", "avg_speed"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols).copy()

    if df.empty:
        raise ValueError("No valid numeric rows after cleaning congestion CSV.")

    df["traffic_count"] = df["vessel_count"] + df["anchored_count"] + df["moored_count"]
    safe_vessel = df["vessel_count"].where(df["vessel_count"] > 0, 1)
    df["stationary_ratio"] = (df["anchored_count"] + df["moored_count"]) / safe_vessel

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def get_latest_port_row(df: pd.DataFrame, port_name: str) -> pd.Series:
    port_df = df[df["port_name"].str.lower() == port_name.lower()].copy()
    if port_df.empty:
        available = sorted(df["port_name"].dropna().unique().tolist())
        raise ValueError(
            f"Port not found: {port_name}. "
            f"Available ports include: {', '.join(available[:8])}"
        )

    if port_df["timestamp"].notna().any():
        port_df = port_df.sort_values("timestamp", ascending=False)
    return port_df.iloc[0]


def load_or_train_model(model_path: Path, dataset_path: Path):
    if model_path.exists():
        try:
            payload = joblib.load(model_path)
            if isinstance(payload, dict) and "model" in payload:
                model = payload["model"]
                model_features = payload.get("feature_columns", FEATURE_COLUMNS)
            else:
                model = payload
                model_features = FEATURE_COLUMNS

            if not hasattr(model, "predict"):
                raise ValueError("Loaded object is not a valid predictive model.")

            return model, list(model_features)
        except Exception as exc:
            print(f"Existing model invalid, retraining. Reason: {exc}")

    print("Model file missing or unusable. Training a fresh model now...")
    run_training(dataset_path=dataset_path, model_path=model_path)
    payload = joblib.load(model_path)

    if isinstance(payload, dict) and "model" in payload:
        return payload["model"], list(payload.get("feature_columns", FEATURE_COLUMNS))
    return payload, FEATURE_COLUMNS


def predict_for_port(port_name: str, dataset_path: Path, model_path: Path) -> dict:
    df = validate_and_prepare_data(dataset_path)
    latest_row = get_latest_port_row(df, port_name)

    model, model_features = load_or_train_model(model_path, dataset_path)
    for col in model_features:
        if col not in latest_row.index:
            raise ValueError(f"Model expects feature '{col}' but it is unavailable in current data.")

    feature_input = pd.DataFrame([{col: latest_row[col] for col in model_features}])
    score = float(model.predict(feature_input[model_features])[0])
    score = max(0.0, min(100.0, score))

    traffic_count = int(latest_row.get("traffic_count", 0))
    level = to_congestion_level(score)

    return {
        "port_name": str(latest_row["port_name"]),
        "congestion_level": level,
        "congestion_score": round(score, 2),
        "traffic_count": traffic_count,
        "message": make_message(str(latest_row["port_name"]), level, score, traffic_count),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict congestion for one selected port.")
    parser.add_argument("--port", default=DEFAULT_PORT, help="Port name to predict.")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to congestion CSV (default: data_sources/port_congestion_log.csv).",
    )
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL_PATH),
        help="Path to model joblib file (default: models/congestion_rf.joblib).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_path = resolve_path(args.dataset, DEFAULT_DATASET_PATH)
    model_path = resolve_path(args.model, DEFAULT_MODEL_PATH)

    print("=== PORT CONGESTION PREDICTION ===")
    print(f"Port: {args.port}")
    print(f"Dataset: {dataset_path}")
    print(f"Model: {model_path}")

    try:
        result = predict_for_port(
            port_name=args.port,
            dataset_path=dataset_path,
            model_path=model_path,
        )
        print("Prediction complete.")
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Prediction failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()