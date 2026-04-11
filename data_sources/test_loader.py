import pandas as pd
from data_loader import (
    get_avg_berthing_data,
    get_median_berthing_data,
    get_teu_data,
    get_vessel_calls_data
)

# Make pandas print everything
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


def print_dataset(name, df):
    print("\n" + "=" * 80)
    print(f"{name}")
    print("=" * 80)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 200):
        print(df)
    print("\n")


def main():
    print("Loading all datasets...\n")

    avg_df = get_avg_berthing_data()
    median_df = get_median_berthing_data()
    teu_df = get_teu_data()
    vessel_df = get_vessel_calls_data()

    print_dataset("TEU DATA", teu_df)
    print_dataset("AVERAGE BERTHING DATA", avg_df)
    print_dataset("MEDIAN BERTHING DATA", median_df)
    print_dataset("VESSEL CALLS DATA", vessel_df)

    print("Done.")


if __name__ == "__main__":
    main()