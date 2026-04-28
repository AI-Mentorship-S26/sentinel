import pandas as pd
import os
import sys

# Maintain the path fix so it can find neighbor files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ship_data import load_all_ports, get_ais_data
from marine_traffic_data import get_marine_traffic_data

def get_combined_sentinel_data(port_name):
    """
    Fetches and merges all available AIS and MarineTraffic data for a specific port.
    """
    # 1. Load port bounds from the CSV
    all_ports = load_all_ports()
    
    if port_name not in all_ports:
        available = ", ".join(list(all_ports.keys())[:5])
        raise ValueError(f"Port '{port_name}' not found. Try: {available}...")

    print(f"📡 Snapshotting {port_name}...")

    # 2. Get your full AIS data snapshot
    # max_messages=50 ensures we get a decent sample size for the model
    ais_raw = get_ais_data(port_name, all_ports[port_name], max_messages=50)
    df_ais = pd.DataFrame(ais_raw)

    # 3. Get Ira's full Marine Traffic Intelligence data
    df_marine = get_marine_traffic_data(port_name)

    # 4. Combine Datasets
    # We use a horizontal concat (axis=1). 
    # This aligns the port-level risk data with the individual ship telemetry.
    if df_ais.empty or df_marine.empty:
        print("⚠️ Warning: One of the data sources returned an empty set.")
        return pd.concat([df_ais, df_marine], axis=1).fillna(0)

    # Merging all columns from both DataFrames
    combined_df = pd.concat([df_ais.reset_index(drop=True), df_marine.reset_index(drop=True)], axis=1)
    
    # Clean up: Remove any duplicate columns that might appear in both APIs
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
    
    # Add this line so the model knows which port this row belongs to
    combined_df['port_name'] = port_name
    
    # Fill missing values with 0 so the Random Forest doesn't crash
    return combined_df.fillna(0)

if __name__ == "__main__":
    # Now the script asks for input in the terminal!
    target = input("Enter the port name (e.g., Port of Houston): ").strip()
    
    try:
        df = get_combined_sentinel_data(target)
        print(f"\n✅ Data Retrieved for {target}")
        # Changed 'combined_df.columns' to 'df.columns'
        print(f"Columns found: {list(df.columns)}") 
        print(f"Total Records: {len(df)}")
        print("\n--- Full Data Preview ---")
        print(df.head())
    except Exception as e:
        print(f"❌ Error: {e}")