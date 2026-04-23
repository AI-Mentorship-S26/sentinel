import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from data_sources.combined_data import get_combined_sentinel_data

def train_sentinel_model():
    # These match your frontend dropdown exactly
    target_ports = [
        "Port of Charleston", "Port of Houston", "Port of Long Beach", 
        "Port of Los Angeles", "Port of Seattle", "Port of Oakland", 
        "Port of New York", "Port of Savannah"
    ]
    
    all_data_frames = []

    print(f"🚀 Sentinel Global Training: Fetching data for {len(target_ports)} ports...")

    for port in target_ports:
        try:
            df = get_combined_sentinel_data(port)
            if not df.empty:
                # Add a column so the model knows which port the data came from
                df['port_name'] = port 
                all_data_frames.append(df)
                print(f"  ✅ Added {port}")
        except Exception as e:
            print(f"  ⚠️ Skipping {port}: {e}")

    if not all_data_frames:
        print("❌ No data collected. Training aborted.")
        return

    # Combine all ports into one big training table
    full_df = pd.concat(all_data_frames, axis=0, ignore_index=True)

    # --- Preprocessing (Same as before) ---
    cols_to_ignore = ['mmsi', 'vessel_name', 'timestamp', 'eta_utc']
    df_clean = full_df.drop(columns=[c for c in cols_to_ignore if c in full_df.columns])

    le = LabelEncoder()
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = le.fit_transform(df_clean[col].astype(str))

    X = df_clean.drop(columns=['is_delayed'])
    y = df_clean['is_delayed'].astype(int)

    print(f"🧠 Training Global Model on {len(df_clean)} total vessels...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, 'sentinel_model.pkl')
    print("-" * 30)
    print("✅ SUCCESS: Global Sentinel Model saved.")
    print(f"📊 Trained with ports: {target_ports}")

if __name__ == "__main__":
    train_sentinel_model()