# Expected API Data Structures

This document defines the expected JSON structure for each data source you'll integrate.

## 1. Congestion Score API

**Endpoint:** `GET /api/congestion/{port_name}`

**Response:**
```json
{
  "port_name": "Port of Houston",
  "score": 0.65,
  "vessel_count": 42,
  "avg_wait_time_hours": 115.2,
  "timestamp": "2026-04-24T12:00:00Z"
}
```

**Dashboard Mapping:**
- `score` (0-1) → `congestion.percentage` (multiply by 100)
- `score` → `congestion.level` (use `scoreToLevel()` function)
- `vessel_count` → `congestion.vesselCount`
- `avg_wait_time_hours` → `congestion.avgWaitTime` (convert to days/hours)

---

## 2. Satellite Imagery API

**Endpoint:** `GET /api/satellite/{port_name}`

**Option A: Image URL Response**
```json
{
  "port_name": "Port of Houston",
  "image_url": "https://your-storage.com/images/houston_20260424.jpg",
  "captured_at": "2026-04-24T10:30:00Z",
  "bounding_box": {
    "min_lat": 29.67,
    "max_lat": 29.70,
    "min_lon": -95.02,
    "max_lon": -94.97
  }
}
```

**Option B: Base64 Encoded Image**
```json
{
  "port_name": "Port of Houston",
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "captured_at": "2026-04-24T10:30:00Z"
}
```

**Dashboard Mapping:**
- `image_url` or `image_base64` → `satelliteImage`

---

## 3. News Feed API

**Endpoint:** `GET /api/news/{port_name}?limit=10`

**Response:**
```json
{
  "port_name": "Port of Houston",
  "articles": [
    {
      "title": "Container throughput increases at Houston port",
      "source": "Port of Houston Authority",
      "published_at": "2026-04-24T10:00:00Z",
      "category": "operations",
      "url": "https://example.com/article-1",
      "summary": "Brief description of the article..."
    },
    {
      "title": "Infrastructure upgrades scheduled for Q3",
      "source": "Maritime Executive",
      "published_at": "2026-04-24T08:00:00Z",
      "category": "infrastructure",
      "url": "https://example.com/article-2"
    }
  ]
}
```

**Dashboard Mapping:**
- `title` → `news[].title`
- `source` → `news[].source`
- `published_at` → `news[].time` (convert to relative time: "2h ago", "1d ago")
- `category` → `news[].category` (must be: "operations" | "infrastructure" | "trade" | "incident")

**Category Mapping:**
- `operations` → Blue
- `infrastructure` → Purple
- `trade` → Green
- `incident` → Red

---

## 4. Crime & Risk Statistics API

**Endpoint:** `GET /api/risks/{port_name}`

**Response:**
```json
{
  "port_name": "Port of Houston",
  "overall_risk": "moderate",
  "risk_categories": [
    {
      "category": "Security",
      "level": "moderate",
      "score": 0.55,
      "description": "Petrochemical cargo requires enhanced protocols.",
      "incidents_last_30_days": 2
    },
    {
      "category": "Weather",
      "level": "high",
      "score": 0.72,
      "description": "Tropical system developing in Gulf of Mexico.",
      "alerts": ["Tropical Storm Watch"]
    },
    {
      "category": "Cargo Theft",
      "level": "moderate",
      "score": 0.48,
      "description": "Elevated theft incidents in surrounding area.",
      "incidents_last_30_days": 5
    },
    {
      "category": "Congestion",
      "level": "high",
      "score": 0.65,
      "description": "Vessel backlog causing delays."
    }
  ],
  "last_updated": "2026-04-24T12:00:00Z"
}
```

**Dashboard Mapping:**
- `overall_risk` → `risks.overall` (must be: "low" | "moderate" | "high" | "critical")
- `risk_categories[].category` → `risks.categories[].name`
- `risk_categories[].level` → `risks.categories[].level`
- `risk_categories[].description` → `risks.categories[].description`

**Risk Level Calculation (from score 0-1):**
- 0.75+ → "critical"
- 0.50-0.74 → "high"
- 0.25-0.49 → "moderate"
- 0-0.24 → "low"

---

## 5. Port Statistics API

**Endpoint:** `GET /api/statistics/{port_name}`

**Response:**
```json
{
  "port_name": "Port of Houston",
  "statistics": {
    "annual_teu_capacity": 3200000,
    "annual_teu_formatted": "3.2M",
    "current_vessels": 42,
    "total_berths": 41,
    "active_cranes": 87,
    "throughput_today_teu": 5671,
    "throughput_today_formatted": "5,671 TEU",
    "yoy_growth_percentage": 2.3,
    "yoy_growth_formatted": "+2.3%"
  },
  "timestamp": "2026-04-24T12:00:00Z"
}
```

**Dashboard Mapping:**
- `annual_teu_formatted` → `statistics.annualTEU`
- `current_vessels` → `statistics.currentVessels`
- `total_berths` → `statistics.berths`
- `active_cranes` → `statistics.craneOperations`
- `throughput_today_formatted` → `statistics.throughputToday`
- `yoy_growth_formatted` → `statistics.yoyGrowth`

---

## 6. Batch Endpoint (Recommended)

For efficiency, consider creating a single endpoint that returns all data:

**Endpoint:** `GET /api/ports/{port_name}/dashboard`

**Response:**
```json
{
  "port_name": "Port of Houston",
  "timestamp": "2026-04-24T12:00:00Z",
  "congestion": {
    "score": 0.65,
    "level": "high",
    "vessel_count": 42,
    "avg_wait_time_hours": 115.2
  },
  "satellite": {
    "image_url": "https://...",
    "captured_at": "2026-04-24T10:30:00Z"
  },
  "news": [...],
  "risks": {...},
  "statistics": {...}
}
```

This reduces the number of API calls from the dashboard.

---

## Time Format Conversion

For relative time display (e.g., "2h ago", "1d ago"):

```typescript
function timeAgo(isoTimestamp: string): string {
  const now = new Date();
  const then = new Date(isoTimestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}
```

---

## Example Integration Flow

1. User selects "Port of Houston" from dropdown
2. Dashboard calls: `GET /api/ports/Port%20of%20Houston/dashboard`
3. API returns combined data object
4. Dashboard updates all components with fresh data
5. Optional: Set up polling (every 5 minutes) for real-time updates

---

## Questions?

- What authentication does your API require? (API key, OAuth, etc.)
- Do you need real-time updates or periodic refreshes?
- Should we cache data or always fetch fresh?
- Are there rate limits on your APIs we should consider?
