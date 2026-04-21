import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler


# Path to this file's directory
BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR / "CSV_Files"


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

def print_dataset(name, df):
    print("\n" + "=" * 80)
    print(f"{name}")
    print("=" * 80)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 200):
        print(df)
    print("\n")

def main():
    avg_df = get_avg_berthing_data()
    median_df = get_median_berthing_data()
    teu_df = get_teu_data()
    vessel_df = get_vessel_calls_data()

    df = teu_df.merge(avg_df, on=["Port"], how="outer") \
            .merge(median_df, on=["Port"], how="outer") \
            .merge(vessel_df, on=["Port"], how="outer")

    numeric_cols = [
        "Export_Loaded",
        "Import_Loaded",
        "AVERAGE of Avg. Berthing Time (hr)",
        "Median Berthing Time (hour)",
        "Calls"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")

    df["Total_TEU"] = df["Export_Loaded"] + df["Import_Loaded"]

    score_cols = [
        "Total_TEU",
        "AVERAGE of Avg. Berthing Time (hr)",
        "Calls"
    ]

    scaler = MinMaxScaler()

    df[["TEU_norm", "Berth_norm", "Calls_norm"]] = scaler.fit_transform(df[score_cols])

    df["congestion_score"] = (
        0.4 * df["TEU_norm"] +
        0.3 * df["Berth_norm"] +
        0.3 * df["Calls_norm"]
    )
    
    print(df[[
        "Port",
        "Total_TEU",
        "AVERAGE of Avg. Berthing Time (hr)",
        "Calls",
        "TEU_norm",
        "Berth_norm",
        "Calls_norm",
        "congestion_score"
    ]])

    #print_dataset("TEU DATA", teu_df)
    #print_dataset("AVERAGE BERTHING DATA", avg_df)
    #print_dataset("MEDIAN BERTHING DATA", median_df)
    #print_dataset("VESSEL CALLS DATA", vessel_df)
    #print_dataset("MERGED DATA", df)

    df.to_csv("final_dataset.csv", index=False)


if __name__ == "__main__":
    main()