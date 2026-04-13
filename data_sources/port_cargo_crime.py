"""
Port Cargo Crime Fetcher
========================
Fetches FBI cargo theft data for every port listed in ports.csv.

Usage
-----
    pip install requests pandas tqdm

    python port_cargo_crime.py --fbi-key YOUR_KEY
    python port_cargo_crime.py --fbi-key YOUR_KEY --start-year 2018 --end-year 2022
    python port_cargo_crime.py --fbi-key YOUR_KEY --ports-file path/to/ports.csv

Get a free API key at: https://api.data.gov/signup/

Output
------
    cargo_theft_all_ports.csv   – combined DataFrame, one row per port/year/variable
    ./cargo_theft_by_port/      – one CSV per port

Returns (if imported)
---------------------
    fbi_dfs : dict { port_name -> pd.DataFrame }
"""

import argparse
import os
import time

import pandas as pd
import requests
from tqdm import tqdm

# FBI ORI codes — nearest reporting police agency for each port
PORT_ORI = {
    "Port of Houston":                   "TX2270300",
    "Port of Corpus Christi":            "TX3550100",
    "Port of Brownsville":               "TX3130100",
    "Port Arthur / Beaumont":            "TX3610400",
    "Port of Galveston":                 "TX0840200",
    "Port of New Orleans":               "LA0360200",
    "Port of Lake Charles":              "LA0190100",
    "Port of Mobile":                    "AL0970100",
    "Port of Tampa Bay":                 "FL2910200",
    "Port of Pascagoula":                "MS0590100",
    "Port of Gulfport":                  "MS0470100",
    "Port of Freeport":                  "TX0200100",
    "Port of New York / New Jersey":     "NY0303000",
    "Port of Baltimore":                 "MD0040100",
    "Port of Virginia (Norfolk)":        "VA0830100",
    "Port of Savannah":                  "GA0510200",
    "Port of Charleston":                "SC0190100",
    "Port of Jacksonville":              "FL0160100",
    "Port Everglades (Fort Lauderdale)": "FL0600100",
    "Port of Miami":                     "FL0250100",
    "Port of Port Canaveral":            "FL0090100",
    "Port of Philadelphia":              "PA1010000",
    "Port of Boston":                    "MA0020100",
    "Port of Providence":                "RI0040100",
    "Port of Wilmington (NC)":           "NC0260100",
    "Port of Brunswick (GA)":            "GA1270100",
    "Port of Los Angeles":               "CA0194200",
    "Port of Long Beach":                "CA0190600",
    "Port of San Diego":                 "CA0730200",
    "Port of San Francisco":             "CA0380100",
    "Port of Oakland":                   "CA0010600",
    "Port of Seattle":                   "WA0330100",
    "Port of Tacoma":                    "WA0530500",
    "Port of Portland (OR)":             "OR0260100",
    "Port Hueneme":                      "CA1110200",
    "Port of Chicago":                   "IL0160000",
    "Port of Detroit":                   "MI0820200",
    "Port of Cleveland":                 "OH0350100",
    "Port of Milwaukee":                 "WI0400100",
    "Port of Duluth / Superior":         "MN0170100",
    "Port of Toledo":                    "OH0430400",
    "Port of Buffalo":                   "NY0140100",
    "Port of St. Louis":                 "MO0950100",
    "Port of Memphis":                   "TN0790100",
    "Port of Baton Rouge":               "LA0170100",
}

FBI_BASE = "https://api.usa.gov/crime/fbi/sapi"


def load_ports(ports_file="ports.csv"):
    """Load port names and bounding boxes from ports.csv."""
    df = pd.read_csv(ports_file)
    # returns list of port_name strings (bbox available if needed later)
    return df


def fbi_get(path, api_key):
    """GET from FBI API with basic retry on rate limit."""
    url = f"{FBI_BASE}/{path}"
    for attempt in range(3):
        try:
            r = requests.get(url, params={"api_key": api_key}, timeout=30)
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == 2:
                print(f"  [warn] {path}: {e}")
                return None
            time.sleep(1)
    return None


def fetch_cargo_theft(port_name, ori, api_key, start_year, end_year):
    """
    Fetch FBI cargo theft data for one port's ORI code.
    Returns a DataFrame with columns:
        port, ori, year, stolen_value, recovered_value,
        incidents, location_type, cargo_desc
    """
    path = f"api/cargo-theft/agencies/{ori}/{start_year}/{end_year}"
    data = fbi_get(path, api_key)

    if not data or "results" not in data or not data["results"]:
        return pd.DataFrame()

    df = pd.DataFrame(data["results"])
    df.insert(0, "port", port_name)
    df.insert(1, "ori", ori)
    return df


def main(fbi_key, ports_file="ports.csv", start_year=2015, end_year=2023, save_csv=True):
    """
    Parameters
    ----------
    fbi_key    : str   – data.gov API key
    ports_file : str   – path to ports.csv
    start_year : int
    end_year   : int
    save_csv   : bool

    Returns
    -------
    fbi_dfs : dict { port_name -> pd.DataFrame }
    """
    ports_df = load_ports(ports_file)
    port_names = ports_df["port_name"].tolist()

    if save_csv:
        os.makedirs("cargo_theft_by_port", exist_ok=True)

    fbi_dfs = {}
    missing_ori = []
    no_data = []

    print(f"\nFetching FBI cargo theft data ({start_year}–{end_year}) for {len(port_names)} ports...\n")

    for port_name in tqdm(port_names, desc="Ports"):
        ori = PORT_ORI.get(port_name)
        if not ori:
            missing_ori.append(port_name)
            continue

        df = fetch_cargo_theft(port_name, ori, api_key=fbi_key,
                               start_year=start_year, end_year=end_year)

        if df.empty:
            no_data.append(port_name)
        else:
            fbi_dfs[port_name] = df
            if save_csv:
                safe = port_name.replace("/", "_").replace(" ", "_")
                df.to_csv(f"cargo_theft_by_port/{safe}.csv", index=False)

        time.sleep(0.15)

    # Remove no-data ports from ports.csv
    if no_data or missing_ori:
        drop = set(no_data + missing_ori)
        ports_df = load_ports(ports_file)
        ports_df = ports_df[~ports_df["port_name"].isin(drop)]
        ports_df.to_csv(ports_file, index=False)
        print(f"\nRemoved {len(drop)} ports from {ports_file}: {sorted(drop)}")

    # Combined file
    if fbi_dfs and save_csv:
        combined = pd.concat(fbi_dfs.values(), ignore_index=True)
        combined.to_csv("cargo_theft_all_ports.csv", index=False)
        print(f"Saved: cargo_theft_all_ports.csv ({len(combined)} rows)")

    # Summary
    print(f"\n{'='*55}")
    print(f"  Results")
    print(f"{'='*55}")
    print(f"  Ports kept         : {len(fbi_dfs)}")
    print(f"  Removed (no data)  : {len(no_data)}  {no_data if no_data else ''}")
    print(f"  Removed (no ORI)   : {len(missing_ori)}  {missing_ori if missing_ori else ''}")

    return fbi_dfs


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch FBI cargo theft data for ports.")
    parser.add_argument("--fbi-key",     required=True, help="data.gov API key")
    parser.add_argument("--ports-file",  default="ports.csv", help="Path to ports.csv")
    parser.add_argument("--start-year",  default=2015, type=int)
    parser.add_argument("--end-year",    default=2023, type=int)
    parser.add_argument("--no-csv",      action="store_true")
    args = parser.parse_args()

    fbi_dfs = main(
        fbi_key    = args.fbi_key,
        ports_file = args.ports_file,
        start_year = args.start_year,
        end_year   = args.end_year,
        save_csv   = not args.no_csv,
    )
