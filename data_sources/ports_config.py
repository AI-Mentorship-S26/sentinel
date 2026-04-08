"""
ports_config.py
Shared utility — loads port data from ports.csv.
Every data source file imports this instead of hardcoding coordinates.
"""

import os
import pandas as pd

# Path to ports.csv — assumes it sits in the same folder as this file
PORTS_CSV = os.path.join(os.path.dirname(__file__), "ports.csv")

def load_ports() -> pd.DataFrame:
    """
    Returns a DataFrame with columns:
      port_name, min_lon, min_lat, max_lon, max_lat
    """
    return pd.read_csv(PORTS_CSV)

def get_port(port_name: str) -> dict:
    """
    Returns a single port's coordinates as a dict.
    Raises ValueError if port not found.
    """
    df = load_ports()
    row = df[df["port_name"] == port_name]
    if row.empty:
        raise ValueError(f"Port '{port_name}' not found in ports.csv")
    return row.iloc[0].to_dict()

def get_all_port_names() -> list:
    """Returns a list of all port names."""
    return load_ports()["port_name"].tolist()
