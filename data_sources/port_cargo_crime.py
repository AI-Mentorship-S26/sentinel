"""
Port Cargo Crime Fetcher
========================
Reads FBI cargo theft data from local xlsx files (2022-2024)
and produces clean DataFrames filtered to port-relevant property types.


Usage
-----
    pip install pandas openpyxl

    python port_cargo_crime.py
    python port_cargo_crime.py --data-dir path/to/cargo-theft-folders

    # Import and call directly:
    from port_cargo_crime import load_all_years, get_port_relevant
    df = load_all_years()
    port_df = get_port_relevant(df)

Output
------
    cargo_theft_all_years.csv         - all property types, 2022-2024
    cargo_theft_port_relevant.csv     - port-relevant types only
"""

import argparse
import os
from pathlib import Path

import pandas as pd

# ── Property types relevant to port/maritime cargo ────────────────────────────
PORT_RELEVANT_TYPES = {
    "Trucks",
    "Trailers",
    "Merchandise",
    "Consumable goods",
    "Computer hardware, software",
    "Portable electronic communications",
    "Clothes, furs",
    "Industrial equipment",
    "Metals, non-precious",
    "Chemicals",
    "Fuel",
    "Other motor vehicles",
    "Vehicle parts",
    "Farm equipment",
    "Alcohol",
    "Drugs, narcotics",
    "Firearms",
    "Other",
    "Total",
}

# ── File map: year -> expected filename pattern ───────────────────────────────
FILE_PATTERNS = {
    2022: "Table_2_Cargo_Theft_Property_Stolen_and_Recovered_by_Type_and_Value_2022.xlsx",
    2023: "Table_2_Cargo_Theft_Property_Stolen_and_Recovered_by_Type_and_Value_2023.xlsx",
    2024: "Cargo_Theft_Table_2_Cargo_Theft_Property_Stolen_and_Recovered_by_Type_and_Value_2024.xlsx",
}

SHEET_NAMES = {
    2022: "22tbl02",
    2023: "23tbl02",
    2024: "24tbl02",
}


def find_file(data_dir: Path, year: int) -> Path:
    """Find the Table 2 xlsx for a given year in data_dir or its subdirs."""
    # Try exact filename first
    exact = data_dir / FILE_PATTERNS[year]
    if exact.exists():
        return exact

    # Search subdirectories
    for p in data_dir.rglob("*.xlsx"):
        if f"Table_2" in p.name or "Table2" in p.name or "tbl02" in p.name.lower():
            if str(year) in p.name:
                return p

    return None


def parse_table2(filepath: Path, year: int) -> pd.DataFrame:
    """
    Parse a Table 2 xlsx file into a clean DataFrame with columns:
        year, property_type, stolen_value, recovered_value, pct_recovered
    """
    sheet = SHEET_NAMES[year]
    raw = pd.read_excel(filepath, sheet_name=sheet, header=None)

    # Data starts at row 5 (0-indexed), columns: 0=type, 1=stolen, 2=recovered, 3=pct
    data = raw.iloc[5:].copy()
    data.columns = ["property_type", "stolen_value", "recovered_value", "pct_recovered"]

    # Drop footnote rows (non-string or NaN property_type)
    data = data[data["property_type"].apply(lambda x: isinstance(x, str))]
    data = data[~data["property_type"].str.startswith(("1 ", "2 ", "*", "Due", "According"))]

    # Clean up
    data["property_type"] = data["property_type"].str.strip()
    data["stolen_value"] = pd.to_numeric(data["stolen_value"], errors="coerce")
    data["recovered_value"] = pd.to_numeric(data["recovered_value"], errors="coerce")
    data["pct_recovered"] = pd.to_numeric(
        data["pct_recovered"].replace("*", "0.05"), errors="coerce"
    )
    data["year"] = year

    return data[["year", "property_type", "stolen_value", "recovered_value", "pct_recovered"]].reset_index(drop=True)


def load_all_years(data_dir: str = ".") -> pd.DataFrame:
    """
    Load and combine Table 2 data for all available years.

    Parameters
    ----------
    data_dir : str
        Directory containing the xlsx files or year subfolders.

    Returns
    -------
    pd.DataFrame with columns:
        year, property_type, stolen_value, recovered_value, pct_recovered
    """
    data_dir = Path(data_dir)
    frames = []

    for year in [2022, 2023, 2024]:
        filepath = find_file(data_dir, year)
        if filepath is None:
            print(f"  [warn] Could not find Table 2 file for {year} in {data_dir}")
            continue
        df = parse_table2(filepath, year)
        frames.append(df)
        print(f"  Loaded {year}: {len(df)} property types  ({filepath.name})")

    if not frames:
        print("No files loaded. Check your --data-dir path.")
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n  Total rows: {len(combined)} across {len(frames)} year(s)")
    return combined


def get_port_relevant(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to port-relevant property types only.

    Returns
    -------
    pd.DataFrame — subset of input, sorted by year and stolen_value desc
    """
    mask = df["property_type"].isin(PORT_RELEVANT_TYPES)
    filtered = df[mask].copy()
    filtered = filtered.sort_values(["year", "stolen_value"], ascending=[True, False])
    return filtered.reset_index(drop=True)


def main(data_dir: str = ".", save_csv: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load all years and produce two DataFrames.

    Returns
    -------
    all_df       : all property types combined
    port_df      : port-relevant types only
    """
    print(f"\nLoading FBI cargo theft data from: {Path(data_dir).resolve()}\n")
    all_df = load_all_years(data_dir)

    if all_df.empty:
        return all_df, pd.DataFrame()

    port_df = get_port_relevant(all_df)
    print(f"  Port-relevant rows: {len(port_df)}")

    if save_csv:
        all_df.to_csv("cargo_theft_all_years.csv", index=False)
        port_df.to_csv("cargo_theft_port_relevant.csv", index=False)
        print(f"\nSaved:")
        print(f"  cargo_theft_all_years.csv     ({len(all_df)} rows)")
        print(f"  cargo_theft_port_relevant.csv ({len(port_df)} rows)")

    print(f"\n{'='*55}")
    print(f"  Port-Relevant Cargo Theft Summary")
    print(f"{'='*55}")
    summary = (
        port_df.groupby("year")[["stolen_value", "recovered_value"]]
        .sum()
        .assign(pct_recovered=lambda x: (x["recovered_value"] / x["stolen_value"] * 100).round(1))
    )
    print(summary.to_string())

    return all_df, port_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load FBI cargo theft xlsx files.")
    parser.add_argument(
        "--data-dir", default=".",
        help="Directory containing the xlsx files or cargo-theft-20XX subfolders (default: current dir)"
    )
    parser.add_argument("--no-csv", action="store_true", help="Skip saving CSVs")
    args = parser.parse_args()

    all_df, port_df = main(data_dir=args.data_dir, save_csv=not args.no_csv)