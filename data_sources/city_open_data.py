import logging
import time
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from sodapy import Socrata

from ports_config import load_ports

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

# config
RECORD_LIMIT = 50000
DATE_FILTER = "2024-01-01T00:00:00"
OUTPUT_DIR = Path("output")
OUTPUT_FORMAT = "csv"  # "parquet" or "csv"

CITY_APIS = [
    {
        "domain": "data.seattle.gov",
        "dataset": "tazs-3rd5",
        "lat": "latitude",
        "lon": "longitude",
        "date": "offense_date",
        "type": "offense_category",
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
        "dataset": "mnz3-dyi8",
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
    {
        "domain": "data.cityofchicago.org",
        "dataset": "ijzp-q8t2",
        "lat": "latitude",
        "lon": "longitude",
        "date": "date",
        "type": "primary_type",
    },
    {
        "domain": "data.baltimorecity.gov",
        "dataset": "wsfq-mvij",
        "lat": "latitude",
        "lon": "longitude",
        "date": "crimetime",
        "type": "description",
    },
    {
        "domain": "data.sfgov.org",
        "dataset": "wg3w-h783",
        "lat": "latitude",
        "lon": "longitude",
        "date": "incident_datetime",
        "type": "incident_category",
    },
    {
        "domain": "data.boston.gov",
        "dataset": "qem9-ugh5",
        "lat": "lat",
        "lon": "long",
        "date": "occurred_on_date",
        "type": "offense_description",
    },
    {
        "domain": "data.oaklandca.gov",
        "dataset": "ppgh-7dqv",
        "lat": "latitude",
        "lon": "longitude",
        "date": "datetime",
        "type": "crimetype",
    },
]

# ── Spatial setup — built from ports.csv, not hardcoded ──────────────────────

def build_port_geodataframe() -> gpd.GeoDataFrame:
    """Build a GeoDataFrame of port bounding boxes from ports.csv."""
    ports_df = load_ports()
    records = [
        {
            "port_name": row["port_name"],
            "geometry": box(row["min_lon"], row["min_lat"],
                            row["max_lon"], row["max_lat"]),
        }
        for _, row in ports_df.iterrows()
    ]
    return gpd.GeoDataFrame(records, crs="EPSG:4326")

PORT_GDF = build_port_geodataframe()


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    log.error("All %d retries exhausted for dataset '%s'. Skipping.", retries, dataset)
    return []


def validate_columns(df: pd.DataFrame, cols: list, source: str) -> bool:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        log.warning("'%s' missing expected columns: %s", source, missing)
        return False
    return True


def tag_ports(df: pd.DataFrame) -> pd.DataFrame:
    """Spatially join crime points to port bounding boxes."""
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(gdf, PORT_GDF, how="inner", predicate="within")
    joined = joined.drop(columns=["index_right", "geometry"])
    return pd.DataFrame(joined)


# ── Core fetch ────────────────────────────────────────────────────────────────

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
    df["latitude"]   = pd.to_numeric(df[api["lat"]], errors="coerce")
    df["longitude"]  = pd.to_numeric(df[api["lon"]], errors="coerce")
    df["date"]       = pd.to_datetime(df[api["date"]], errors="coerce")
    df["crime_type"] = df[api["type"]]
    df = df.dropna(subset=["latitude", "longitude", "date"])

    df = tag_ports(df)
    if df.empty:
        log.info("  No records near any port from %s.", api["domain"])
        return pd.DataFrame()

    df["source"] = api["domain"]
    log.info("  Port-tagged records from %s: %d", api["domain"], len(df))
    return df[["port_name", "date", "crime_type", "source", "latitude", "longitude"]]


# ── Export ────────────────────────────────────────────────────────────────────

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


# ── Main pipeline ─────────────────────────────────────────────────────────────

def get_data() -> pd.DataFrame:
    frames = []
    ports_with_data = set()

    for api in CITY_APIS:
        df = fetch_city(api)
        if not df.empty:
            frames.append(df)
            ports_with_data.update(df["port_name"].unique())

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


if __name__ == "__main__":
    df = get_data()
    if not df.empty:
        print(df.head(20))
        print(f"\nTotal records: {len(df)}")