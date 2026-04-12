"""
fbi_cargo_theft.py

Loads FBI NIBRS cargo theft data.

Source: FBI public S3 bucket (no login required)
Direct URL: https://s3-us-gov-west-1.amazonaws.com/cg-d3f0433b-a53e-4934-8b94-c678aa2cbaf3/cargo_theft.csv

Covers: 2011-2019, US cargo theft incidents by state/agency
Fields include: state, agency, year, offense type, stolen value, recovered value

Usage:
    from fbi_cargo_theft import get_cargo_theft

    df = get_cargo_theft()              # downloads if not cached locally
    df = get_cargo_theft("my_file.csv") # loads from local file
"""

import os
import requests
import pandas as pd

# Direct public download — no API key needed
FBI_S3_URL = (
    "https://s3-us-gov-west-1.amazonaws.com/"
    "cg-d3f0433b-a53e-4934-8b94-c678aa2cbaf3/cargo_theft.csv"
)

DEFAULT_LOCAL_PATH = "data/fbi_cargo_theft.csv"


def get_cargo_theft(local_path: str = DEFAULT_LOCAL_PATH) -> pd.DataFrame:
    """
    Load FBI cargo theft data. Tries local file first, downloads if missing.

    Args:
        local_path: Where to look for (and save) the CSV file.

    Returns:
        DataFrame with normalized column names and cleaned types.
    """
    raw = _load_raw(local_path)
    return _parse(raw)


# --- Internal functions ---

def _load_raw(local_path: str) -> pd.DataFrame:
    if os.path.exists(local_path):
        print(f"[fbi_cargo_theft] Loading from local file: {local_path}")
        return pd.read_csv(local_path, encoding="latin-1", low_memory=False)

    print(f"[fbi_cargo_theft] Local file not found. Downloading from FBI S3...")
    response = requests.get(FBI_S3_URL, timeout=60)
    response.raise_for_status()

    # Save locally so you don't have to download again
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(response.content)
    print(f"[fbi_cargo_theft] Saved to {local_path}")

    return pd.read_csv(local_path, encoding="latin-1", low_memory=False)


def _parse(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize column names: lowercase, spaces to underscores
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Drop rows with no state or year — they're unusable
    df = df.dropna(subset=["state_name", "data_year"])

    # Standardize types
    df["data_year"] = pd.to_numeric(df["data_year"], errors="coerce").astype("Int64")

    # Normalize dollar values if present
    for col in ["value_of_property_stolen", "value_of_property_recovered"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add a clean label column
    df["source"] = "fbi_nibrs_cargo_theft"

    print(f"[fbi_cargo_theft] {len(df):,} records | years: {df['data_year'].min()}–{df['data_year'].max()}")
    return df


# --- Quick exploration helpers ---

def by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Total incidents and stolen value grouped by state."""
    agg = {"source": "count"}
    if "value_of_property_stolen" in df.columns:
        agg["value_of_property_stolen"] = "sum"
    return (
        df.groupby("state_name")
        .agg(agg)
        .rename(columns={"source": "incident_count"})
        .sort_values("incident_count", ascending=False)
    )


def by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Total incidents per year."""
    return (
        df.groupby("data_year")
        .size()
        .reset_index(name="incident_count")
        .sort_values("data_year")
    )


if __name__ == "__main__":
    df = get_cargo_theft()
    print("\n--- By State (top 10) ---")
    print(by_state(df).head(10))
    print("\n--- By Year ---")
    print(by_year(df))
