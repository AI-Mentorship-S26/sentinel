
import os
import requests
import pandas as pd

# --- city configurations ---
# this will map the city key → Socrata API endpoint + port bounding box
CITY_CONFIG = {
    "la": {
        "name": "Los Angeles",
        "port_name": "Port of Los Angeles",
        "api_url": "https://data.lacity.org/resource/2nrs-mtv8.json",
        "date_col": "date_occ",
        "lat_col": "lat",
        "lon_col": "lon",
        "crime_col": "crm_cd_desc",
        "id_col": "dr_no",
        # bounding box for San Pedro / Port of LA area
        "bbox": {"lat_min": 33.69, "lat_max": 33.76, "lon_min": -118.30, "lon_max": -118.19},
    },
    "nyc": {
        "name": "New York City",
        "port_name": "Port of New York/New Jersey",
        "api_url": "https://data.cityofnewyork.us/resource/5uac-w243.json",
        "date_col": "cmplnt_fr_dt",
        "lat_col": "latitude",
        "lon_col": "longitude",
        "crime_col": "ofns_desc",
        "id_col": "cmplnt_num",
        # bounsinf box for Red Hook / Port Newark area
        "bbox": {"lat_min": 40.63, "lat_max": 40.70, "lon_min": -74.10, "lon_max": -74.01},
    },
    "chi": {
        "name": "Chicago",
        "port_name": "Port of Chicago",
        "api_url": "https://data.cityofchicago.org/resource/ijzp-q8t2.json",
        "date_col": "date",
        "lat_col": "latitude",
        "lon_col": "longitude",
        "crime_col": "primary_type",
        "id_col": "id",
        # bounding box for Calumet Harbor / Lake Calumet area
        "bbox": {"lat_min": 41.70, "lat_max": 41.75, "lon_min": -87.56, "lon_max": -87.52},
    },
}

# crime keywords to keep — everything else is filtered out
PORT_CRIME_KEYWORDS = [
    "THEFT", "BURGLARY", "ROBBERY", "CARGO",
    "ASSAULT", "BATTERY", "SMUGGL", "CONTRABAND",
    "TRESPASS", "VANDALISM", "WEAPON", "NARCOTICS",
]


def get_city_crime(
    city: str,
    local_path: str = None,
    start_date: str = "2022-01-01",
    app_token: str = None,
    limit: int = 10000,
) -> pd.DataFrame:

    # Load city crime data near port areas.

    city = city.lower()
    if city not in CITY_CONFIG:
        raise ValueError(f"Unknown city '{city}'. Choose from: {list(CITY_CONFIG.keys())}")

    config = CITY_CONFIG[city]

    if local_path and os.path.exists(local_path):
        print(f"[city_crime:{city}] Loading from local file: {local_path}")
        raw = pd.read_csv(local_path, low_memory=False)
    else:
        if local_path:
            print(f"[city_crime:{city}] Local file not found at '{local_path}'. Trying API...")
        raw = _fetch_from_api(city, config, start_date, app_token, limit)

    return _parse(raw, city, config)


# --- Internal functions ---

def _fetch_from_api(
    city: str,
    config: dict,
    start_date: str,
    app_token: str,
    limit: int,
) -> pd.DataFrame:
    bbox = config["bbox"]
    date_col = config["date_col"]
    lat_col = config["lat_col"]
    lon_col = config["lon_col"]

    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token

    where = (
        f"{date_col} >= '{start_date}T00:00:00' "
        f"AND {lat_col} >= '{bbox['lat_min']}' AND {lat_col} <= '{bbox['lat_max']}' "
        f"AND {lon_col} >= '{bbox['lon_min']}' AND {lon_col} <= '{bbox['lon_max']}'"
    )

    params = {"$limit": limit, "$where": where, "$order": f"{date_col} DESC"}

    print(f"[city_crime:{city}] Fetching from API (from {start_date})...")
    response = requests.get(config["api_url"], headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    print(f"[city_crime:{city}] Got {len(data)} raw records")
    return pd.DataFrame(data)


def _parse(df: pd.DataFrame, city: str, config: dict) -> pd.DataFrame:
    df.columns = df.columns.str.strip().str.lower()

    lat_col = config["lat_col"].lower()
    lon_col = config["lon_col"].lower()
    date_col = config["date_col"].lower()
    crime_col = config["crime_col"].lower()
    id_col = config["id_col"].lower()

    # Drop rows missing critical fields
    df = df.dropna(subset=[lat_col, lon_col])
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col])

    # Filter to port-relevant crime types only
    if crime_col in df.columns:
        mask = df[crime_col].str.upper().str.contains(
            "|".join(PORT_CRIME_KEYWORDS), na=False
        )
        before = len(df)
        df = df[mask]
        print(f"[city_crime:{city}] Filtered to {len(df)} port-relevant records (from {before})")

    # Build a normalized output DataFrame
    normalized = pd.DataFrame({
        "source_id": df.get(id_col, pd.Series(dtype=str)),
        "source": f"city_open_data_{city}",
        "port_name": config["port_name"],
        "date": pd.to_datetime(df.get(date_col), errors="coerce").dt.strftime("%Y-%m-%d"),
        "lat": df[lat_col],
        "lon": df[lon_col],
        "crime_type": df.get(crime_col, pd.Series(dtype=str)).str.upper(),
    })

    print(f"[city_crime:{city}] {len(normalized):,} normalized records")
    return normalized


if __name__ == "__main__":
    # Example: load LA data from a downloaded CSV
    # df = get_city_crime("la", local_path="data/la_crime.csv")

    # Example: pull NYC from API (no token needed for small pulls)
    df = get_city_crime("nyc", start_date="2023-01-01")
    print(df.head())
    print(f"\nCrime types found:\n{df['crime_type'].value_counts().head(10)}")
