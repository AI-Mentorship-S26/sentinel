import websocket
import json
import os
import csv
import threading
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------

load_dotenv()
API_KEY = os.getenv("AISSTREAM_API_KEY")
PORTS_CSV = "data_sources/CSV Files/ports.csv"
LOG_FILE = "data_sources/port_congestion_log.csv"

NAV_STATUS = {
    0:  "Underway (Engine)",
    1:  "At Anchor",
    2:  "Not Under Command",
    3:  "Restricted Manoeuvrability",
    4:  "Constrained by Draught",
    5:  "Moored",
    6:  "Aground",
    7:  "Engaged in Fishing",
    8:  "Underway (Sailing)",
    15: "Unknown"
}

# ---------------------------------------------------------------------------
# Data Loading & Preparation
# ---------------------------------------------------------------------------

def load_all_ports(csv_path=PORTS_CSV):
    """Reads ports.csv and returns a dict of bounding boxes."""
    ports = {}
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["port_name"].strip()
            ports[name] = [
                [float(row["min_lat"]), float(row["min_lon"])],
                [float(row["max_lat"]), float(row["max_lon"])]
            ]
    return ports

# ---------------------------------------------------------------------------
# AIS Formatting
# ---------------------------------------------------------------------------

def format_vessel(data):
    """Extracts and formats vessel data from AIS messages."""
    vessel = data["Message"].get("PositionReport", {})
    meta = data.get("Metadata", {})
    
    # Use ShipName from Metadata; fallback to MMSI if unknown
    name = meta.get("ShipName", "Unknown").strip()
    if not name or name == "Unknown":
        name = f"MMSI: {vessel.get('UserID')}"

    nav_code = int(vessel.get("NavigationalStatus", 15))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "mmsi": int(vessel.get("UserID", 0)),
        "vessel_name": name,
        "speed_knots": float(vessel.get("Sog", 0)),
        "course_deg": float(vessel.get("Cog", 0)),
        "heading_deg": int(vessel.get("TrueHeading", 511)),
        "nav_status": NAV_STATUS.get(nav_code, "Unknown"),
        "nav_code": nav_code,
        "rate_of_turn": float(vessel.get("RateOfTurn", -128)),
    }

# ---------------------------------------------------------------------------
# Data Collection Logic
# ---------------------------------------------------------------------------

def get_ais_data(port_name, port_bounds, max_messages=10):
    """Connects to WebSocket and collects a snapshot of vessel data."""
    collected_data = []
    done = threading.Event()

    def on_message(ws, message):
        data = json.loads(message)
        if "Message" in data and "PositionReport" in data["Message"]:
            formatted = format_vessel(data)
            collected_data.append(formatted)

        if len(collected_data) >= max_messages:
            ws.close()
            done.set()

    def on_error(ws, error):
        print(f" Error in {port_name}: {error}")
        done.set()

    def on_open(ws):
        ws.send(json.dumps({
            "APIKey": API_KEY,
            "BoundingBoxes": [port_bounds],
            "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
        }))

    ws = websocket.WebSocketApp(
        "wss://stream.aisstream.io/v0/stream",
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=lambda ws, *args: done.set()
    )

    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()
    
    # Wait up to 60s for the port to report enough vessels
    done.wait(timeout=60)
    ws.close()

    return collected_data

# ---------------------------------------------------------------------------
# ML Logging Logic
# ---------------------------------------------------------------------------

def log_port_metrics(results, log_file=LOG_FILE):
    """Summarizes ship data into port-level features for the ML model."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_exists = os.path.isfile(log_file)
    
    with open(log_file, mode='a', newline='') as f:
        fieldnames = ['timestamp', 'port_name', 'vessel_count', 'anchored_count', 'moored_count', 'avg_speed']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        for port_name, vessels in results.items():
            if not vessels:
                continue 
                
            total = len(vessels)
            anchored = sum(1 for v in vessels if v["nav_code"] == 1)
            moored = sum(1 for v in vessels if v["nav_code"] == 5)
            avg_speed = sum(v["speed_knots"] for v in vessels) / total
            
            writer.writerow({
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'),
                "port_name": port_name,
                "vessel_count": total,
                "anchored_count": anchored,
                "moored_count": moored,
                "avg_speed": round(avg_speed, 2)
            })

# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    all_ports = load_all_ports()
    results = {}

    # Check for single port argument: python ship_data.py "Port of Houston"
    target_port = sys.argv[1] if len(sys.argv) > 1 else None

    if target_port:
        if target_port in all_ports:
            print(f"\n[TARGET] {target_port} ... ", end="", flush=True)
            vessels = get_ais_data(target_port, all_ports[target_port])
            results[target_port] = vessels
            print(f"{len(vessels)} vessel(s) found.")
        else:
            print(f"Error: Port '{target_port}' not found in CSV.")
            sys.exit(1)
    else:
        print(f"\nCollecting AIS data for {len(all_ports)} ports...\n")
        for i, (name, bounds) in enumerate(all_ports.items(), 1):
            print(f"  [{i}/{len(all_ports)}] {name} ... ", end="", flush=True)
            try:
                vessels = get_ais_data(name, bounds, max_messages=10)
                results[name] = vessels
                print(f"{len(vessels)} found.")
            except Exception as e:
                print(f"error: {e}")

    # Log metrics to CSV for the ML model
    if results:
        print("\nSaving metrics to congestion log...")
        log_port_metrics(results)
        print(f"✅ Log updated: {LOG_FILE}")