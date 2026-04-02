import logging
import time
from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
from sodapy import Socrata

# logging setup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("port_crime.log"),
    ],
)
log = logging.getLogger(__name__)

# config for ports and bounding boxes

RECORD_LIMIT = 50000
DATE_FILTER = "2024-01-01T00:00:00"

# Output config
OUTPUT_DIR = Path("output")
OUTPUT_FORMAT = "parquet"  # "parquet" or "csv"

PORT_BBOXES = {
    "Port of Houston":          [-95.35, 29.55, -94.85, 29.85],
    "Port of Corpus Christi":   [-97.50, 27.75, -97.00, 28.00],
    "Port of Brownsville":      [-97.50, 25.90, -97.10, 26.10],
    "Port Arthur / Beaumont":   [-94.20, 29.85, -93.80, 30.10],
    "Port of Galveston":        [-94.90, 29.25, -94.70, 29.40],
    "Port of New Orleans":      [-90.10, 29.90, -89.90, 30.05],
    "Port of Lake Charles":     [-93.30, 30.15, -93.10, 30.25],
    "Port of Mobile":           [-88.10, 30.60, -87.90, 30.75],
    "Port of Tampa Bay":        [-82.55, 27.85, -82.35, 28.00],
    "Port of Pascagoula":       [-88.65, 30.30, -88.45, 30.45],
    "Port of Gulfport":         [-89.15, 30.30, -88.95, 30.45],
    "Port of Freeport":         [-95.40, 28.90, -95.20, 29.05],

    "Port of New York / New Jersey": [-74.15, 40.55, -73.85, 40.75],
    "Port of Baltimore":        [-76.65, 39.20, -76.45, 39.35],
    "Port of Virginia (Norfolk)": [-76.40, 36.85, -76.20, 37.05],
    "Port of Savannah":         [-81.15, 31.95, -80.95, 32.15],
    "Port of Charleston":       [-79.97, 32.70, -79.87, 32.85],
    "Port of Jacksonville":     [-81.65, 30.30, -81.50, 30.45],
    "Port Everglades (Fort Lauderdale)": [-80.15, 26.05, -80.05, 26.15],
    "Port of Miami":            [-80.20, 25.75, -80.10, 25.85],
    "Port of Port Canaveral":   [-80.65, 28.38, -80.55, 28.48],
    "Port of Philadelphia":     [-75.20, 39.85, -75.00, 40.05],
    "Port of Boston":           [-71.10, 42.30, -70.90, 42.45],

    "Port of Los Angeles":      [-118.30, 33.65, -118.10, 33.80],
    "Port of Long Beach":       [-118.25, 33.70, -118.10, 33.85],
    "Port of San Diego":        [-117.20, 32.65, -117.05, 32.80],
    "Port of Oakland":          [-122.35, 37.75, -122.20, 37.85],
    "Port of Seattle":          [-122.45, 47.55, -122.30, 47.70],

    "Port of Chicago":          [-87.75, 41.70, -87.55, 41.90],
    "Port of Detroit":          [-83.15, 42.25, -82.95, 42.45],
}

CITY_APIS = [
    {
        "domain": "data.seattle.gov",
        "dataset": "tazs-3rd5",
        "lat": "latitude",
        "lon": "longitude",
        "date": "offense_start_datetime",
        "type": "offense",
    },
    {
        "domain": "data.lacity.org",
        "dataset": "2nrs-mtv8",
        "lat": "lat",
        "lon": "lon",
        "date": "date_occ",
        "type": "crm_cd_desc",
    },
    {
        "domain": "data.houstontx.gov",
        "dataset": "gxrs-zszg",
        "lat": "latitude",
        "lon": "longitude",
        "date": "date",
        "type": "offense_type",
    },
    {
        "domain": "data.cityofnewyork.us",
        "dataset": "qgea-i56i",
        "lat": "latitude",
        "lon": "longitude",
        "date": "cmplnt_fr_dt",
        "type": "ofns_desc",
    },
]

# spatial data setup

def build_port_geodataframe() -> gpd.GeoDataFrame:
    """
    Build a GeoDataFrame of port bounding boxes.
    This is constructed once and reused for all spatial joins.
    """
    records = [
        {"port_name": name, "geometry": box(lon_min, lat_min, lon_max, lat_max)}
        for name, (lon_min, lat_min, lon_max, lat_max) in PORT_BBOXES.items()
    ]
    return gpd.GeoDataFrame(records, crs="EPSG:4326")

PORT_GDF = build_port_geodataframe()

# helper functions

def fetch_with_retry(client, dataset, where=None, retries=3):
    for attempt in range(retries):
        try:
            return client.get(dataset, where=where, limit=RECORD_LIMIT)
        except Exception as e:
            wait = 2 ** attempt
            log.warning(
                "Attempt %d/%d failed for dataset '%s': %s. Retrying in %ds...",
                attempt + 1, retries, dataset, e, wait,
            )
            time.sleep(wait)
    log.error(
        "All %d retries exhausted for dataset '%s'. Skipping.", retries, dataset
    )
    return []


def validate_columns(df: pd.DataFrame, cols: list, source: str) -> bool:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        log.warning("'%s' missing expected columns: %s", source, missing)
        return False
    return True


def tag_ports(df: pd.DataFrame) -> pd.DataFrame:
    """
    Spatially join crime points to port bounding boxes using a spatial index.
    Much faster than iterating over bounding boxes row-by-row.
    """
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )

    joined = gpd.sjoin(gdf, PORT_GDF, how="inner", predicate="within")

    # Drop the spatial join index column and geometry
    joined = joined.drop(columns=["index_right", "geometry"])

    return pd.DataFrame(joined)


# core function to fetch, clean, and tag data for a single city API

def fetch_city(api: dict) -> pd.DataFrame:
    log.info("Fetching from %s (dataset: %s)...", api["domain"], api["dataset"])
    client = Socrata(api["domain"], None)

    where_clause = f"{api['date']} >= '{DATE_FILTER}'" if DATE_FILTER else None
    records = fetch_with_retry(client, api["dataset"], where_clause)

    if not records:
        log.warning("No records returned from %s.", api["domain"])
        return pd.DataFrame()

    df = pd.DataFrame(records)
    log.info("  Raw records from %s: %d", api["domain"], len(df))

    required = [api["lat"], api["lon"], api["date"], api["type"]]
    if not validate_columns(df, required, api["domain"]):
        return pd.DataFrame()

    df = df.dropna(subset=required)
    df["latitude"] = pd.to_numeric(df[api["lat"]], errors="coerce")
    df["longitude"] = pd.to_numeric(df[api["lon"]], errors="coerce")
    df["date"] = pd.to_datetime(df[api["date"]], errors="coerce")
    df["crime_type"] = df[api["type"]]
    df = df.dropna(subset=["latitude", "longitude", "date"])

    df = tag_ports(df)

    if df.empty:
        log.info("  No records near any port from %s.", api["domain"])
        return pd.DataFrame()

    df["source"] = api["domain"]
    log.info("  Port-tagged records from %s: %d", api["domain"], len(df))

    return df[["port_name", "date", "crime_type", "source", "latitude", "longitude"]]


# export function

def export(df: pd.DataFrame, fmt: str = OUTPUT_FORMAT) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if fmt == "parquet":
        path = OUTPUT_DIR / "port_crimes.parquet"
        df.to_parquet(path, index=False)
    elif fmt == "csv":
        path = OUTPUT_DIR / "port_crimes.csv"
        df.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Use 'parquet' or 'csv'.")

    log.info("Exported %d records to %s", len(df), path)
    return path


# main pipeline function
def get_data() -> pd.DataFrame:
    frames = []

    for api in CITY_APIS:
        df = fetch_city(api)
        if not df.empty:
            frames.append(df)

    if not frames:
        log.warning("No data fetched from any source.")
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates()

    log.info(
        "Pipeline complete: %d total records from %d cities.",
        len(combined), len(frames),
    )
    return combined


# run the pipeline

if __name__ == "__main__":
    df = get_data()
    if not df.empty:
        export(df)
        print(df.head(20))