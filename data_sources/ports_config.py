"""
ports_config.py
Loads port bounding boxes from ports.csv
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
PORTS_CSV = os.path.join(BASE_DIR,"CSV Files", "ports.csv")

def load_ports():
    return pd.read_csv(PORTS_CSV)

def get_port(port_name: str):
    df = load_ports()
    row = df[df["port_name"] == port_name]

    if row.empty:
        raise ValueError(f"{port_name} not found")

    return row.iloc[0].to_dict()


def get_all_port_names():
    return load_ports()["port_name"].tolist()