'''import websocket
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("AISSTREAM_API_KEY")


def format_vessel(vessel):
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "mmsi": int(vessel.get("UserID", 0)),
        "latitude": float(vessel.get("Latitude", 0)),
        "longitude": float(vessel.get("Longitude", 0)),
        "speed": float(vessel.get("Sog", 0)),
        "course": float(vessel.get("Cog", 0))
    }


def get_ais_data(port_bounds, max_messages=20):
    """
    Connects to AISStream and returns a list of vessel data.
    
    Args:
        port_bounds: [[min_lat, min_lon], [max_lat, max_lon]]
        max_messages: number of messages to collect
    
    Returns:
        List of vessel dictionaries
    """

    collected_data = []

    def on_message(ws, message):
        data = json.loads(message)

        try:
            vessel = data["Message"]["PositionReport"]
            formatted = format_vessel(vessel)

            # basic filtering
            if formatted["latitude"] != 0 and formatted["longitude"] != 0:
                collected_data.append(formatted)

        except:
            pass

        # stop after enough data
        if len(collected_data) >= max_messages:
            ws.close()

    def on_open(ws):
        subscribe_message = {
            "APIKey": API_KEY,
            "BoundingBoxes": [port_bounds]
        }
        ws.send(json.dumps(subscribe_message))

    socket = "wss://stream.aisstream.io/v0/stream"

    ws = websocket.WebSocketApp(
        socket,
        on_message=on_message
    )

    ws.on_open = on_open
    ws.run_forever()

    return collected_data
'''
import websocket
import json
import os
import ast  # To safely parse the text file format
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("AISSTREAM_API_KEY")

def get_port_bounds(port_name):
    """
    Parses the 'AIM Sentinel Ports.txt' file to find coordinates for a specific port.
    Note: The file format in your screenshot looks like: "Port Name": [lon1, lat1, lon2, lat2]
    """
    file_path = "data_sources/CSV Files/AIM Sentinel Ports.txt" # Update path as needed
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    # We strip comments and clean the text to make it look like a valid Python dict
    lines = [line.strip().rstrip(',') for line in content.split('\n') if ':' in line and not line.startswith('#')]
    ports_dict = {}
    for line in lines:
        key, value = line.split(':', 1)
        ports_dict[key.strip().strip('"')] = ast.literal_eval(value.strip())
    
    bounds = ports_dict.get(port_name)
    if not bounds:
        raise ValueError(f"Port '{port_name}' not found in the configuration file.")
    
    # AISStream expects: [[min_lat, min_lon], [max_lat, max_lon]]
    # Based on your text file: [lon1, lat1, lon2, lat2]
    lon1, lat1, lon2, lat2 = bounds
    return [[min(lat1, lat2), min(lon1, lon2)], [max(lat1, lat2), max(lon1, lon2)]]

def format_vessel(vessel):
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "mmsi": int(vessel.get("UserID", 0)),
        "latitude": float(vessel.get("Latitude", 0)),
        "longitude": float(vessel.get("Longitude", 0)),
        "speed": float(vessel.get("Sog", 0)),
        "course": float(vessel.get("Cog", 0))
    }

def get_ais_data(port_name, max_messages=20):
    """
    Main method to be called by the team.
    Example: get_ais_data("Port of Houston")
    """
    port_bounds = get_port_bounds(port_name)
    collected_data = []

    def on_message(ws, message):
        data = json.loads(message)
        try:
            vessel = data["Message"]["PositionReport"]
            formatted = format_vessel(vessel)
            if formatted["latitude"] != 0:
                collected_data.append(formatted)
        except KeyError:
            pass

        if len(collected_data) >= max_messages:
            ws.close()

    def on_open(ws):
        subscribe_message = {
            "APIKey": API_KEY,
            "BoundingBoxes": [port_bounds]
        }
        ws.send(json.dumps(subscribe_message))

    ws = websocket.WebSocketApp(
        "wss://stream.aisstream.io/v0/stream",
        on_message=on_message,
        on_open=on_open
    )

    ws.run_forever()
    return collected_data
    # ... (rest of your code above)

if __name__ == "__main__":
    # Test call to see if it works
    print("Connecting to AISStream for Port of Houston...")
    try:
        data = get_ais_data("Port of Houston", max_messages=5)
        
        if data:
            print(f"Successfully collected {len(data)} messages:")
            for vessel in data:
                print(vessel)
        else:
            print("No data collected. Check your API key or port bounds.")
            
    except Exception as e:
        print(f"An error occurred: {e}")