import pandas as pd
from pathlib import Path

# Path to this file's directory
BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR / "CSV Files"


def load_csv(filename):
    """
    Generic helper method to load a CSV file from the CSV Files folder.
    """
    file_path = CSV_DIR / filename
    return pd.read_csv(file_path)


def get_avg_berthing_data():
    """
    Returns the Average Berthing dataset.
    """
    return load_csv("Avg_Berthing_Data.csv")


def get_median_berthing_data():
    """
    Returns the Median Berthing dataset.
    """
    return load_csv("Median_Berthing_Data.csv")


def get_teu_data():
    """
    Returns the TEU dataset.
    """
    return load_csv("TEU_Data.csv")


def get_vessel_calls_data():
    """
    Returns the Vessel Calls dataset.
    """
    return load_csv("Vessel_Calls.csv")


def get_ports_data():
    """
    Returns the Ports dataset.
    Optional helper dataset.
    """
    return load_csv("ports.csv")