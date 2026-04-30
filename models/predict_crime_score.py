"""
Port crime risk model.
Returns a 0-1 score per port based on crime volume, severity, and recency.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data_sources"))

import pandas as pd
import numpy as np
from city_open_data import get_data

SEVERITY_WEIGHTS = {
    "theft": 3.0, "burglary": 3.0, "robbery": 3.5, "cargo": 4.0,
    "smuggling": 4.0, "weapon": 3.5, "shooting": 4.0, "homicide": 4.0,
    "vehicle": 2.5, "truck": 3.5,
    "assault": 2.0, "fraud": 2.0, "vandalism": 1.5, "drug": 2.0,
    "noise": 0.3, "disorder": 0.5, "trespass": 0.8,
}
DEFAULT_WEIGHT = 1.0
_cached_scores = None


def _severity(crime_type):
    t = str(crime_type).lower()
    for keyword, weight in SEVERITY_WEIGHTS.items():
        if keyword in t:
            return weight
    return DEFAULT_WEIGHT


def _time_decay(date, half_life_days=180):
    date = pd.to_datetime(date, errors="coerce", utc=True)
    if pd.isna(date):
        return 0.5
    age_days = (pd.Timestamp.now(tz="UTC") - date).days
    return 0.5 ** (max(age_days, 0) / half_life_days)


def _compute_all_port_scores():
    global _cached_scores
    if _cached_scores is not None:
        return _cached_scores

    df = get_data()
    if df.empty:
        _cached_scores = {}
        return _cached_scores

    df["severity"] = df["crime_type"].apply(_severity)
    df["recency"]  = df["date"].apply(_time_decay)
    df["weight"]   = df["severity"] * df["recency"]

    raw = df.groupby("port_name")["weight"].sum()

    if len(raw) == 0 or raw.max() == raw.min():
        _cached_scores = {p: 0.5 for p in raw.index}
    else:
        normalized = (raw - raw.min()) / (raw.max() - raw.min())
        _cached_scores = normalized.to_dict()

    return _cached_scores


def predict_crime_score(port_name):
    """Returns a 0-1 risk score for the given port."""
    scores = _compute_all_port_scores()
    return round(scores.get(port_name, 0.0), 3)


if __name__ == "__main__":
    scores = _compute_all_port_scores()
    for port, score in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"{port:35s} {score:.3f}")