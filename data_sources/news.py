from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import requests
from dotenv import load_dotenv

# Load API key from .env if exists
load_dotenv()

# ----------------------------
# Config
# ----------------------------
BASE_URL = "https://newsapi.org/v2/everything"
DEFAULT_LANGUAGE = "en"
DEFAULT_SORT_BY = "publishedAt"
DEFAULT_TIMEOUT = 30
DEFAULT_PAGE_SIZE = 100
PORTS_CSV_PATH = r"C:\Users\gowri\Downloads\sentinel\data_sources\ports.csv"

EXCLUDE_KEYWORDS = [
    "usb port", "charging port", "computer port", "software port",
    "video game port", "port wine", "airport"
]

PORT_WORDS = ["port", "ports", "seaport", "harbor", "harbour",
              "terminal", "container terminal", "dock", "cargo port"]

MARITIME_WORDS = ["maritime", "shipping", "vessel", "ship", "cargo", "freight", "container"]

CRIME_WORDS = ["smuggling", "piracy", "trafficking", "contraband",
               "cargo theft", "customs fraud", "illegal fishing",
               "sanctions evasion", "drug bust", "arms trafficking", "maritime crime"]

TRADE_WORDS = ["trade", "import", "export", "logistics",
               "supply chain", "shipment", "container traffic",
               "port congestion", "customs"]

# ----------------------------
# Exceptions
# ----------------------------
class NewsAPIError(Exception):
    pass

# ----------------------------
# NewsAPI Client
# ----------------------------
@dataclass
class NewsAPIClient:
    api_key: str
    timeout: int = DEFAULT_TIMEOUT

    def fetch_all_news(self, search: str, *, language: str = DEFAULT_LANGUAGE,
                       sort_by: str = DEFAULT_SORT_BY, page_size: int = DEFAULT_PAGE_SIZE,
                       page: int = 1) -> Dict[str, Any]:
        params = {
            "q": search,
            "language": language,
            "sortBy": sort_by,
            "pageSize": int(page_size),
            "page": int(page),
            "apiKey": self.api_key,
        }
        response = requests.get(BASE_URL, params=params, timeout=self.timeout)
        try:
            payload = response.json()
        except ValueError as exc:
            raise NewsAPIError(f"Non-JSON response from API (status {response.status_code}).") from exc
        if not response.ok:
            code = payload.get("code", "unknown_error") if isinstance(payload, dict) else "unknown_error"
            message = payload.get("message", "Unknown API error") if isinstance(payload, dict) else "Unknown API error"
            raise NewsAPIError(f"API request failed ({response.status_code}) [{code}]: {message}")
        if not isinstance(payload, dict) or "articles" not in payload:
            raise NewsAPIError("Unexpected API response format: missing 'articles'.")
        return payload

# ----------------------------
# Utility functions
# ----------------------------
def load_ports(csv_path: str = PORTS_CSV_PATH) -> pd.DataFrame:
    return pd.read_csv(csv_path)

def get_port_info(port_name: str, csv_path: str = PORTS_CSV_PATH) -> Dict[str, Any]:
    ports_df = load_ports(csv_path)
    matches = ports_df[ports_df["port_name"].str.lower() == port_name.lower()]
    if matches.empty:
        raise ValueError(f"Port '{port_name}' not found in {csv_path}")
    return matches.iloc[0].to_dict()

def build_port_news_query(port_name: str) -> str:
    return (
        f'"{port_name}" AND '
        f'("port congestion" OR "container terminal" OR seaport OR harbor OR harbour OR '
        f'"cargo theft" OR smuggling OR piracy OR contraband OR "customs fraud" OR '
        f'"port trade" OR "port exports" OR "port imports" OR "container traffic" OR '
        f'"shipping" OR "maritime" OR "logistics")'
    )

def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if v is not None)
    return str(value).strip()

def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _clean_text(*parts: Any) -> str:
    joined = " ".join(_safe_text(p) for p in parts if _safe_text(p))
    return _normalize_whitespace(joined.replace("\n", " ").replace("\r", " "))

def contains_any(text: str, words: List[str]) -> bool:
    return any(word in text for word in words)

def find_all_matches(text: str, words: List[str]) -> List[str]:
    return [word for word in words if word in text]

def classify_article(text: str) -> List[str]:
    categories = []
    has_port = contains_any(text, PORT_WORDS)
    has_maritime = contains_any(text, MARITIME_WORDS)
    has_crime = contains_any(text, CRIME_WORDS)
    has_trade = contains_any(text, TRADE_WORDS)
    if has_port and (has_maritime or has_trade):
        categories.append("ports")
    if has_crime and (has_port or has_maritime):
        categories.append("maritime_crime")
    if has_trade and has_port:
        categories.append("trade_at_ports")
    return categories

def relevance_score(text: str) -> int:
    return (2*len(find_all_matches(text, PORT_WORDS)) +
            1*len(find_all_matches(text, MARITIME_WORDS)) +
            3*len(find_all_matches(text, CRIME_WORDS)) +
            2*len(find_all_matches(text, TRADE_WORDS)))

def _is_excluded(text: str) -> bool:
    return any(keyword in text for keyword in EXCLUDE_KEYWORDS)

def standardize_article(article: Dict[str, Any], port_name: str, search_term: str) -> Optional[Dict[str, Any]]:
    if not article.get("title") or not article.get("url"):
        return None
    text = _clean_text(article.get("title"), article.get("description"), article.get("content")).lower()
    if _is_excluded(text):
        return None
    keywords = (find_all_matches(text, PORT_WORDS) +
                find_all_matches(text, MARITIME_WORDS) +
                find_all_matches(text, CRIME_WORDS) +
                find_all_matches(text, TRADE_WORDS))
    categories = classify_article(text)
    score = relevance_score(text)
    if not categories or score < 3:
        return None
    return {
        "port_name": port_name,
        "source": _safe_text(article.get("source", {}).get("name")),
        "author": _safe_text(article.get("author")),
        "title": _safe_text(article.get("title")),
        "description": _safe_text(article.get("description")),
        "content": _safe_text(article.get("content")),
        "url": _safe_text(article.get("url")),
        "image_url": _safe_text(article.get("urlToImage")),
        "published_at": _safe_text(article.get("publishedAt")),
        "search_term": search_term,
        "matched_keywords": keywords,
        "categories": categories,
        "relevance_score": score
    }

def preprocess_articles(raw_articles: List[Dict[str, Any]], port_name: str, search_term: str) -> pd.DataFrame:
    standardized = [standardize_article(a, port_name, search_term) for a in raw_articles]
    df = pd.DataFrame([a for a in standardized if a is not None])
    if not df.empty:
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    return df

# ----------------------------
# Main function
# ----------------------------
def get_news(port_name: str, api_key: Optional[str] = None, page_size: int = 100, max_pages: int = 3) -> pd.DataFrame:
    get_port_info(port_name)  # validate port exists
    key = api_key or os.getenv("NEWS_API_KEY")
    if not key:
        raise ValueError("Missing API key. Set NEWS_API_KEY in .env or pass api_key")
    query = build_port_news_query(port_name)
    client = NewsAPIClient(api_key=key)
    all_articles = []
    for page in range(1, max_pages+1):
        payload = client.fetch_all_news(search=query, page_size=page_size, page=page)
        articles = payload.get("articles", [])
        if not articles:
            break
        all_articles.extend(articles)
        if len(articles) < page_size:
            break
    return preprocess_articles(all_articles, port_name, query)
# this is uspposed to be testing if the code works...
if __name__ == "__main__":
    port = input("Enter port name: ").strip()
    try:
        df = get_news(port)
        if df.empty:
            print("No relevant news found for this port.")
        else:
            print(df[["published_at", "title", "source", "url"]].head(10))
            print(f"\nTotal articles fetched: {len(df)}")
    except Exception as e:
        print("Error:", e)