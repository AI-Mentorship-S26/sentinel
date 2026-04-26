import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data_sources" / "port_congestion_log.csv"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "congestion_rf.joblib"

REQUIRED_COLUMNS = [
    "timestamp",
    "port_name",
    "vessel_count",
    "anchored_count",
    "moored_count",
    "avg_speed",
]

FEATURE_COLUMNS = [
    "vessel_count",
    "anchored_count",
    "moored_count",
    "avg_speed",
    "traffic_count",
    "stationary_ratio",
]


def resolve_path(path_str: str, fallback: Path) -> Path:
    raw_path = Path(path_str) if path_str else fallback
    if raw_path.is_absolute():
        return raw_path
    return (PROJECT_ROOT / raw_path).resolve()


def _clamp_series(series: pd.Series, low: float, high: float) -> pd.Series:
    return series.clip(lower=low, upper=high)


def create_congestion_score(df: pd.DataFrame) -> pd.Series:
    traffic_norm = _clamp_series(df["traffic_count"] / 20.0, 0.0, 1.0)
    stationary_norm = _clamp_series(df["stationary_ratio"], 0.0, 1.0)
    speed_slowdown = _clamp_series((12.0 - df["avg_speed"]) / 12.0, 0.0, 1.0)

    score = (0.55 * traffic_norm) + (0.30 * stationary_norm) + (0.15 * speed_slowdown)
    return _clamp_series(score * 100.0, 0.0, 100.0)


def load_dataset(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Congestion CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV is empty: {csv_path}")

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV missing required columns: {missing_cols}")

    return df


def prepare_training_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    numeric_cols = ["vessel_count", "anchored_count", "moored_count", "avg_speed"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=numeric_cols).copy()
    if df.empty:
        raise ValueError("No valid numeric rows after cleaning congestion CSV.")

    df["traffic_count"] = df["vessel_count"] + df["anchored_count"] + df["moored_count"]
    safe_vessel = df["vessel_count"].where(df["vessel_count"] > 0, 1)
    df["stationary_ratio"] = (df["anchored_count"] + df["moored_count"]) / safe_vessel
    df["congestion_score"] = create_congestion_score(df)

    X = df[FEATURE_COLUMNS].copy()
    y = df["congestion_score"].copy()

    if X.empty or y.empty:
        raise ValueError("Training data is empty after preprocessing.")

    return X, y


def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    model = RandomForestRegressor(n_estimators=160, random_state=42, n_jobs=-1)
    model.fit(X, y)
    return model


def save_model(model: RandomForestRegressor, model_path: Path) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "model_type": "RandomForestRegressor",
        "version": "port-congestion-v1",
    }
    joblib.dump(payload, model_path)


def run_training(dataset_path: Path, model_path: Path) -> Path:
    df = load_dataset(dataset_path)
    X, y = prepare_training_data(df)
    model = train_model(X, y)
    save_model(model, model_path)
    return model_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the port congestion model.")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to congestion CSV (default: data_sources/port_congestion_log.csv).",
    )
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL_PATH),
        help="Path to save model joblib file (default: models/congestion_rf.joblib).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_path = resolve_path(args.dataset, DEFAULT_DATASET_PATH)
    model_path = resolve_path(args.model, DEFAULT_MODEL_PATH)

    print("=== PORT CONGESTION MODEL TRAINING ===")
    print(f"Dataset: {dataset_path}")
    print(f"Model out: {model_path}")

    try:
        saved_path = run_training(dataset_path=dataset_path, model_path=model_path)
        print("Training complete.")
        print(f"Saved model: {saved_path}")
    except Exception as exc:
        print(f"Training failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()