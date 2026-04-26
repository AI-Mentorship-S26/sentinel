"""
this model uses a hybrid sentiment + LLm approach to classify news and crime data
    congestion risk levels:
    high       - strong evidence of port congestion
    moderate   - some disruption likely
    low        - minor or indirect impact
    none       - no congestion signal

the architecture:
fast path  : keyword/rule signals and then direct label (no API call)
LLM path   : ambiguous cases > Google Gemini for deeper reasoning

Usage
-----
    pip install pandas requests python-dotenv

    # Set your Google AI API key in .env:
    GOOGLE_AI_KEY=your_key_here

    from port_congestion_classifier import classify_article, classify_crime, classify_batch

    # Single article
    result = classify_article("Longshoremen strike halts operations at Port of LA")

    # Crime record
    result = classify_crime("truck theft", stolen_value=450000, port="Port of Houston")

    # Batch DataFrame
    results_df = classify_batch(df, text_col="title", source="news")
"""

from __future__ import annotations
import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_KEY", "")  # set in .env
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

LABELS = ["high", "moderate", "low", "none"]

# ── fast-path keyword rules ───────────────────────────────────────────────────
# if ANY of these match → return label directly without hitting the LLM

FAST_HIGH = [
    "port closure", "terminal closed", "strike", "walkout", "labor dispute",
    "ships anchored", "vessel queue", "port congestion", "backlog",
    "operations suspended", "cargo backup", "dock workers strike",
    "longshoremen strike", "shutdown", "blockade", "seized", "smuggling ring",
    "cargo theft ring", "armed robbery", "shooting at port",
]

FAST_LOW = [
    "record throughput", "smooth operations", "no disruption",
    "back to normal", "resolved", "reopened", "cleared backlog",
    "efficiency record", "on schedule",
]

FAST_NONE = [
    "usb port", "software", "gaming", "wine port", "airport",
    "computer port", "charging port",
]

# crime types that are direct high-signal
HIGH_CRIME_TYPES = {
    "cargo theft", "truck theft", "trailer theft", "smuggling",
    "armed robbery", "weapons", "shooting", "organized theft",
}
MODERATE_CRIME_TYPES = {
    "robbery", "burglary", "assault", "fraud", "bribery",
    "extortion", "drug", "narcotics", "vehicle theft",
}


# Fast path 

def fast_classify(text: str) -> str | None:
    """
    Check text against keyword rules.
    Returns label if matched, None if ambiguous (needs LLM).
    """
    text_lower = text.lower()

    for kw in FAST_NONE:
        if kw in text_lower:
            return "none"

    for kw in FAST_HIGH:
        if kw in text_lower:
            return "high"

    for kw in FAST_LOW:
        if kw in text_lower:
            return "low"

    return None  # ambiguous → send to LLM


# LLM path (Google Gemini) 

SYSTEM_PROMPT = """You are an expert in maritime logistics and port operations.
Your job is to analyze text (news articles or crime reports) and determine
how likely it is to cause or indicate port congestion.

Port congestion is caused by: labor disputes, vessel backups, cargo theft,
infrastructure failures, weather events, security incidents, high cargo volumes,
customs delays, and supply chain disruptions.

Respond ONLY with a valid JSON object in exactly this format:
{
  "label": "high" | "moderate" | "low" | "none",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence explanation"
}

Labels:
- high: strong evidence of significant port disruption or congestion
- moderate: some disruption likely, indirect impact on port operations
- low: minor signal, unlikely to cause meaningful congestion
- none: no relevance to port congestion
"""

def call_gemini(text: str, retries: int = 2) -> dict:
    """Call Google Gemini API and return parsed JSON response."""
    if not GOOGLE_AI_KEY:
        return {
            "label": "none",
            "confidence": 0.0,
            "reasoning": "No Google AI API key set — LLM path disabled.",
            "path": "llm_disabled",
        }

    prompt = f"{SYSTEM_PROMPT}\n\nText to analyze:\n{text[:2000]}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 200,
        },
    }

    for attempt in range(retries + 1):
        try:
            r = requests.post(
                GEMINI_URL,
                params={"key": GOOGLE_AI_KEY},
                json=payload,
                timeout=20,
            )
            r.raise_for_status()
            raw = r.json()
            content = raw["candidates"][0]["content"]["parts"][0]["text"]

            # Strip markdown fences if present
            content = content.strip().strip("```json").strip("```").strip()
            result = json.loads(content)
            result["path"] = "llm"
            return result

        except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
            if attempt == retries:
                return {
                    "label": "low",
                    "confidence": 0.3,
                    "reasoning": f"LLM call failed: {e}",
                    "path": "llm_error",
                }
            time.sleep(1.5 ** attempt)

    return {"label": "none", "confidence": 0.0, "reasoning": "Unknown error", "path": "error"}


# Public API

def classify_article(
    title: str,
    description: str = "",
    port: str = "",
) -> dict:
    """
    Classify a news article for port congestion signal.

    Parameters
    ----------
    title       : article headline
    description : article description or summary (optional)
    port        : port name for context (optional)

    Returns
    -------
    dict with keys: label, confidence, reasoning, path
    """
    text = f"{title} {description}"
    if port:
        text = f"[Port: {port}] {text}"

    # try fast path first
    fast_label = fast_classify(text)
    if fast_label is not None:
        confidence = 0.95 if fast_label in ("high", "none") else 0.80
        return {
            "label":      fast_label,
            "confidence": confidence,
            "reasoning":  f"Matched fast-path keyword rule → {fast_label}",
            "path":       "fast",
        }

    # Ambiguous > LLM
    return call_gemini(text)


def classify_crime(
    crime_type: str,
    stolen_value: float = 0,
    port: str = "",
    description: str = "",
) -> dict:
    """
    Classify a crime record for port congestion signal.

    Parameters
    ----------
    crime_type    : type of crime (e.g. "truck theft", "assault")
    stolen_value  : dollar value stolen (for cargo theft)
    port          : port name
    description   : additional context

    Returns
    -------
    dict with keys: label, confidence, reasoning, path
    """
    crime_lower = crime_type.lower()

    # direct high-signal crime types
    for c in HIGH_CRIME_TYPES:
        if c in crime_lower:
            label = "high" if stolen_value > 100_000 else "moderate"
            return {
                "label":      label,
                "confidence": 0.92,
                "reasoning":  f"{crime_type} with ${stolen_value:,.0f} stolen → direct port risk",
                "path":       "fast",
            }

    # moderate crime types
    for c in MODERATE_CRIME_TYPES:
        if c in crime_lower:
            return {
                "label":      "moderate",
                "confidence": 0.75,
                "reasoning":  f"{crime_type} near port → indirect operational risk",
                "path":       "fast",
            }

    # ambiguous crime > LLM
    text = (
        f"Crime type: {crime_type}. "
        f"Stolen value: ${stolen_value:,.0f}. "
        f"Port: {port}. "
        f"Details: {description}"
    )
    return call_gemini(text)


def classify_batch(
    df: pd.DataFrame,
    text_col: str = "title",
    source: str = "news",
    description_col: str = "",
    port_col: str = "port",
    crime_type_col: str = "crime_type",
    stolen_value_col: str = "stolen_value",
    delay: float = 0.3,
) -> pd.DataFrame:
    """
    Classify an entire DataFrame of articles or crime records.

    parameters:
    df              : input DataFrame
    text_col        : column with main text (for news)
    source          : "news" or "crime"
    description_col : optional secondary text column
    port_col        : column with port name
    crime_type_col  : column with crime type (for crime source)
    stolen_value_col: column with stolen value (for crime source)
    delay           : seconds between LLM calls (rate limiting)

    returns
    -------
    original DataFrame with added columns:
        congestion_label, confidence, reasoning, classification_path
    """
    if df.empty:
        return df

    results = []
    for _, row in df.iterrows():
        port = str(row.get(port_col, "")) if port_col in df.columns else ""

        if source == "news":
            title = str(row.get(text_col, ""))
            desc = str(row.get(description_col, "")) if description_col else ""
            result = classify_article(title, desc, port)

        elif source == "crime":
            crime_type = str(row.get(crime_type_col, ""))
            stolen = float(row.get(stolen_value_col, 0) or 0)
            result = classify_crime(crime_type, stolen, port)

        else:
            result = classify_article(str(row.get(text_col, "")), port=port)

        results.append(result)

        # rate limit only LLM calls
        if result.get("path") == "llm":
            time.sleep(delay)

    results_df = pd.DataFrame(results).rename(columns={
        "label":      "congestion_label",
        "confidence": "confidence",
        "reasoning":  "reasoning",
        "path":       "classification_path",
    })

    return pd.concat(
        [df.reset_index(drop=True), results_df.reset_index(drop=True)],
        axis=1,
    )

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Classify port congestion signals.")
    parser.add_argument("--text",  help="Single text to classify")
    parser.add_argument("--crime", help="Single crime type to classify")
    parser.add_argument("--value", type=float, default=0, help="Stolen value for crime")
    parser.add_argument("--port",  default="", help="Port name")
    args = parser.parse_args()

    if args.text:
        result = classify_article(args.text, port=args.port)
        print(json.dumps(result, indent=2))

    elif args.crime:
        result = classify_crime(args.crime, args.value, args.port)
        print(json.dumps(result, indent=2))

    else:
        # Demo
        print(" News article examples ")
        examples = [
            ("Longshoremen strike halts all operations at Port of LA", "Port of Los Angeles"),
            ("Minor theft reported near Port of Seattle parking lot", "Port of Seattle"),
            ("Record cargo volumes processed at Port of Houston this quarter", "Port of Houston"),
            ("Weather delays expected to clear by tomorrow morning", "Port of Miami"),
            ("Organized cargo theft ring dismantled near Port of New York", "Port of New York"),
            ("New USB port standard announced by tech consortium", ""),
        ]
        for text, port in examples:
            r = classify_article(text, port=port)
            print(f"\n  Text   : {text[:60]}")
            print(f"  Label  : {r['label']}  (confidence: {r['confidence']:.2f})")
            print(f"  Path   : {r['path']}")
            print(f"  Reason : {r['reasoning']}")

        print("\n Crime examples ")
        crimes = [
            ("truck theft",  850000, "Port of Houston"),
            ("assault",       0,      "Port of Seattle"),
            ("noise complaint", 0,    "Port of LA"),
        ]
        for crime, value, port in crimes:
            r = classify_crime(crime, value, port)
            print(f"\n  Crime  : {crime} (${value:,.0f})")
            print(f"  Label  : {r['label']}  (confidence: {r['confidence']:.2f})")
            print(f"  Path   : {r['path']}")
            print(f"  Reason : {r['reasoning']}")