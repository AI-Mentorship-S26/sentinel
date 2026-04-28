def get_detailed_risk_assessment(port_name, data_payload):
    """
    Analyzes specific data points to determine the status of the 4 Figma cards.
    """
    
    # 1. Weather Logic (Example: threshold-based)
    wind_speed = data_payload.get('wind_speed', 0)
    weather_desc = "Clear conditions. Normal operations expected."
    weather_level = "Low"
    
    if wind_speed > 35:
        weather_level = "High"
        weather_desc = "Severe weather warning. Potential port closure."
    elif wind_speed > 20:
        weather_level = "Moderate"
        weather_desc = "Heavier winds detected. Expect minor delays."

    # 2. Cargo Theft Logic (Example: incident-count based)
    crime_incidents = data_payload.get('recent_thefts', 0)
    theft_level = "Low"
    theft_desc = "Standard security protocols in effect."
    
    if crime_incidents > 5:
        theft_level = "High"
        theft_desc = "Significant spike in localized cargo theft."
    elif crime_incidents >= 2:
        theft_level = "Moderate"
        theft_desc = "Elevated cargo theft incidents in surrounding area."

    # 3. Labor Logic (Example: Keyword/Sentiment based)
    news_sentiment = data_payload.get('labor_sentiment', 0) # -1 to 1
    labor_level = "Low"
    labor_desc = "Recent contract agreement. Stable workforce."
    
    if news_sentiment < -0.5:
        labor_level = "High"
        labor_desc = "High strike risk. Labor negotiations stalled."
    
    # 4. Security Logic
    # (Defaulting to Low unless an active threat is flagged in news)
    security_level = "Low"
    security_desc = "No active threats. Standard security protocols in effect."

    return {
        "security": {"level": security_level, "desc": security_desc},
        "weather": {"level": weather_level, "desc": weather_desc},
        "labor": {"level": labor_level, "desc": labor_desc},
        "cargo_theft": {"level": theft_level, "desc": theft_desc}
    }