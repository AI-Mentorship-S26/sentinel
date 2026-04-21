from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "final_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "congestion_rf.joblib"

FEATURE_COLUMNS = [
    "Total_TEU",
    "AVERAGE of Avg. Berthing Time (hr)",
    "Median Berthing Time (hour)",
    "Calls",
]

TARGET_COLUMN = "congestion_score"


def load_dataset(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return df


def prepare_data(df: pd.DataFrame):
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")

    combined = pd.concat([X, y], axis=1).dropna()

    X = combined[FEATURE_COLUMNS]
    y = combined[TARGET_COLUMN]

    return X, y


def train_model(X_train, y_train) -> RandomForestRegressor:
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test):
    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = mse ** 0.5
    r2 = r2_score(y_test, predictions)

    print("\n=== MODEL EVALUATION ===")
    print(f"MAE :  {mae:.6f}")
    print(f"MSE :  {mse:.6f}")
    print(f"RMSE:  {rmse:.6f}")
    print(f"R^2 :  {r2:.6f}")

    results_df = pd.DataFrame({
        "Actual": y_test.values,
        "Predicted": predictions
    })

    print("\n=== SAMPLE PREDICTIONS ===")
    print(results_df.head(10).to_string(index=False))

    importances = pd.Series(model.feature_importances_, index=FEATURE_COLUMNS).sort_values(ascending=False)

    print("\n=== FEATURE IMPORTANCE ===")
    print(importances.to_string())


def save_model(model, model_path: Path):
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")


def main():
    print("TRAINING SCRIPT STARTED")
    try:
        df = load_dataset(DATASET_PATH)
        X, y = prepare_data(df)

        # X_train, X_test, y_train, y_test = train_test_split(
        #     X,
        #     y,
        #     test_size=0.2,
        #     random_state=42
        # )

        # model = train_model(X_train, y_train)
        # evaluate_model(model, X_test, y_test)
        # save_model(model, MODEL_PATH)
        model = train_model(X, y)
        print("\nTraining on full dataset (no train/test split due to small data)...")
        save_model(model, MODEL_PATH)


    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()