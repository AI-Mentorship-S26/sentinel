"""
Port crime risk model.
Returns a 0-1 cargo theft risk score using local FBI cargo theft CSVs.
"""

from pathlib import Path
import pandas as pd

CRIME_CSV = Path(__file__).resolve().parents[1] / "cargo_theft_port_relevant.csv"

_cached_score = None

PORT_CRIME_MULTIPLIERS = {
    "Port of Los Angeles": 1.65,
    "Port of Long Beach": 1.10,
    "Port of Houston": 1.05,
    "Port of New York / New Jersey": 1.00,
    "Port of Oakland": 0.95,
    "Port of Seattle": 0.90,
    "Port of Savannah": 0.85,
    "Port of Charleston": 0.80,
    "Port of Virginia (Norfolk)": 0.80,
}


def predict_crime_score(port_name):
    global _cached_score

    if _cached_score is None:
        df = pd.read_csv(CRIME_CSV)

        total_stolen = df["stolen_value"].sum()
        total_recovered = df["recovered_value"].sum()

        if total_stolen <= 0:
            _cached_score = 0.0
        else:
            risk = 1 - (total_recovered / total_stolen)
            _cached_score = round(max(0, min(risk, 1)), 3)

    multiplier = PORT_CRIME_MULTIPLIERS.get(port_name, 1.0)
    port_score = _cached_score * (0.8 + 0.2 * multiplier)

    return round(max(0, min(port_score, 1)), 3)


if __name__ == "__main__":
    for port in [
        "Port of Houston",
        "Port of Los Angeles",
        "Port of Savannah",
        "Port of Long Beach"
    ]:
        print(port, predict_crime_score(port))