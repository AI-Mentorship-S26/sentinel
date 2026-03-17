import websocket
import json
import os


API_KEY = os.getenv("AISSTREAM_API_KEY")



# This function runs every time a new message is received from AISStream
def on_message(ws, message):
    # Convert the incoming JSON string into a Python dictionary
    data = json.loads(message)

    try:
        # Extract vessel position data from the message
        vessel = data["Message"]["PositionReport"]

        # Format and clean the data into a more readable structure
        formatted = {
            "mmsi": vessel["UserID"],        # Unique vessel identifier
            "latitude": vessel["Latitude"],  # Current latitude
            "longitude": vessel["Longitude"],# Current longitude
            "speed": vessel["Sog"],          # Speed over ground (knots)
            "course": vessel["Cog"]          # Direction of travel (degrees)
        }

        # Print the formatted vessel data
        print(formatted)

    except:
        # Ignore messages that don't contain PositionReport data
        pass


# This function runs once when the WebSocket connection is opened
def on_open(ws):
    # Define subscription message with API key and geographic bounding box
    subscribe_message = {
        "APIKey": API_KEY,
        "BoundingBoxes": [[[18, -98], [31, -80]]]  # Gulf of Mexico region
    }

    # Send the subscription request to start receiving data
    ws.send(json.dumps(subscribe_message))


# WebSocket endpoint for AISStream
socket = "wss://stream.aisstream.io/v0/stream"

# Create WebSocket connection and assign message handler
ws = websocket.WebSocketApp(
    socket,
    on_message=on_message
)

# Assign function to run when connection opens
ws.on_open = on_open

# Keep the connection running and continuously receive data
ws.run_forever()