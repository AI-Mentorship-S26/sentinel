# API Integration Guide

This guide explains how to integrate your Python congestion prediction API with the dashboard.

## Current Status

✅ Dashboard updated with your 9 ports from `ports.csv`  
✅ Coordinates from CSV integrated  
⏳ Congestion scores are currently placeholder values  
⏳ Waiting for your Python API endpoint

## Your Ports

The dashboard now displays these 9 ports:

1. Port of Houston
2. Port of Long Beach
3. Port of Los Angeles
4. Port of Seattle
5. Port of Oakland
6. Port of New York / New Jersey
7. Port of Virginia (Norfolk)
8. Port of Savannah
9. Port of Charleston

## Integration Steps

### Step 1: Set Up Your Python API

Your Python API should expose an endpoint that returns congestion scores (0-1) for each port.

**Example Python API endpoint (Flask/FastAPI):**

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/congestion/<port_name>', methods=['GET'])
def get_congestion(port_name):
    # Your model prediction logic here
    score = your_model.predict(port_name)  # Returns 0-1
    
    return jsonify({
        "port_name": port_name,
        "score": float(score),
        "timestamp": "2026-04-24T12:00:00Z"
    })

@app.route('/api/congestion/all', methods=['GET'])
def get_all_congestion():
    # Return all port scores at once
    scores = {}
    for port in all_ports:
        scores[port] = your_model.predict(port)
    
    return jsonify(scores)
```

### Step 2: Update the API Utility

Edit `/src/app/utils/congestionApi.ts`:

1. Replace `YOUR_API_ENDPOINT` with your actual API URL (e.g., `http://localhost:5000/api`)
2. Adjust the response parsing based on your API structure
3. Optionally modify the `scoreToLevel()` thresholds:
   - `0.85+` → Critical
   - `0.65-0.84` → High
   - `0.45-0.64` → Moderate
   - `0-0.44` → Low

### Step 3: Connect the Dashboard to Your API

Update `/src/app/App.tsx` to fetch data from your API:

```typescript
import { useEffect, useState } from "react";
import { fetchCongestionScore, scoreToLevel } from "./utils/congestionApi";

export default function App() {
  const [selectedPortId, setSelectedPortId] = useState("houston");
  const [congestionData, setCongestionData] = useState({});

  // Fetch congestion data when port changes
  useEffect(() => {
    async function loadCongestionData() {
      const portName = PORT_DATA[selectedPortId].name;
      const score = await fetchCongestionScore(portName);
      const level = scoreToLevel(score);
      const percentage = Math.round(score * 100);

      // Update the port data with real API values
      setCongestionData({
        level,
        percentage,
        // vesselCount and avgWaitTime can also come from your API
      });
    }

    loadCongestionData();
  }, [selectedPortId]);

  // Use congestionData in your component...
}
```

### Step 4: Test Your Integration

1. Start your Python API server
2. Update the API endpoint URL in `congestionApi.ts`
3. Open the dashboard and verify:
   - Congestion scores load from your API
   - The correct congestion level displays (low/moderate/high/critical)
   - The percentage matches your model's 0-1 score

## Converting Model Output (0-1) to Dashboard Values

Your model returns a score from 0 to 1. Here's how it maps to the dashboard:

| Score Range | Congestion Level | Color | Example |
|-------------|------------------|-------|---------|
| 0.85 - 1.0  | Critical         | Red   | 0.92 → 92% Critical |
| 0.65 - 0.84 | High            | Orange | 0.78 → 78% High |
| 0.45 - 0.64 | Moderate        | Yellow | 0.58 → 58% Moderate |
| 0.0 - 0.44  | Low             | Green  | 0.34 → 34% Low |

## Data Sources to Integrate

Based on your requirements, you'll need to integrate:

- ✅ **Congestion scores** - Your Python model (ready to integrate)
- ⏳ **Satellite imagery** - Your satellite data code
- ⏳ **News feed** - Your news API
- ⏳ **Crime/risk statistics** - Your crime data source
- ⏳ **Port statistics** - Throughput, vessel counts, etc.

## CORS Issues?

If you get CORS errors when calling your API from the browser:

**Option 1: Add CORS headers to your Python API**
```python
from flask_cors import CORS
CORS(app)
```

**Option 2: Use a proxy** (for development)
Add to `vite.config.ts`:
```typescript
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:5000'
    }
  }
}
```

## Need Help?

If you encounter issues:
1. Check browser console for errors
2. Verify your API is returning the expected JSON structure
3. Test your API endpoint directly with curl/Postman first
4. Ensure your API server is running and accessible
