from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests


BASE_URL = "https://newsapi.org/v2/everything"
DEFAULT_LANGUAGE = "en"
DEFAULT_SORT_BY = "publishedAt"
DEFAULT_TIMEOUT = 30
DEFAULT_PAGE_SIZE = 100
PORTS_CSV_PATH = "ports.csv"

EXCLUDE_KEYWORDS = [
    "usb port",
    "charging port",
    "computer port",
    "software port",
    "video game port",
    "port wine",
    "airport",
]

PORT_WORDS = [
    "port", "ports", "seaport", "harbor", "harbour",
    "terminal", "container terminal", "dock", "cargo port"
]

MARITIME_WORDS = [
    "maritime", "shipping", "vessel", "ship", "cargo", "freight", "container"
]

CRIME_WORDS = [
    "smuggling", "piracy", "trafficking", "contraband",
    "cargo theft", "customs fraud", "illegal fishing",
    "sanctions evasion", "drug bust", "arms trafficking", "maritime crime"
]

TRADE_WORDS = [
    "trade", "import", "export", "logistics",
    "supply chain", "shipment", "container traffic",
    "port congestion", "customs"
]


class NewsAPIError(Exception):
    pass


@dataclass
class NewsAPIClient:
    api_key: str
    timeout: int = DEFAULT_TIMEOUT

    def fetch_all_news(
        self,
        search: str,
        *,
        language: str = DEFAULT_LANGUAGE,
        sort_by: str = DEFAULT_SORT_BY,
        page_size: int = DEFAULT_PAGE_SIZE,
        page: int = 1,
    ) -> Dict[str, Any]:
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


def load_ports(csv_path: str = PORTS_CSV_PATH) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def get_port_info(port_name: str, csv_path: str = PORTS_CSV_PATH) -> Dict[str, Any]:
    ports_df = load_ports(csv_path)
    matches = ports_df[ports_df["port_name"].str.lower() == port_name.lower()].copy()

    if matches.empty:
        raise ValueError(f"Port '{port_name}' not found in {csv_path}")

    return matches.iloc[0].to_dict()


def build_port_news_query(port_name: str) -> str:
    return (
        f'"{port_name}" AND '
        f'('
        f'"port congestion" OR "container terminal" OR seaport OR harbor OR harbour OR '
        f'"cargo theft" OR smuggling OR piracy OR contraband OR "customs fraud" OR '
        f'"port trade" OR "port exports" OR "port imports" OR "container traffic" OR '
        f'"shipping" OR "maritime" OR "logistics"'
        f')'
    )


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if v is not None)
    return str(value).strip()


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _clean_text_for_model(*parts: Any) -> str:
    joined = " ".join(_safe_text(part) for part in parts if _safe_text(part))
    joined = joined.replace("\n", " ").replace("\r", " ")
    return _normalize_whitespace(joined)


def contains_any(text: str, words: List[str]) -> bool:
    return any(word in text for word in words)


def find_all_matches(text: str, words: List[str]) -> List[str]:
    return [word for word in words if word in text]


def classify_article_strong(text: str) -> List[str]:
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
    port_hits = len(find_all_matches(text, PORT_WORDS))
    maritime_hits = len(find_all_matches(text, MARITIME_WORDS))
    crime_hits = len(find_all_matches(text, CRIME_WORDS))
    trade_hits = len(find_all_matches(text, TRADE_WORDS))

    return (2 * port_hits) + (1 * maritime_hits) + (3 * crime_hits) + (2 * trade_hits)


def _is_excluded(text: str) -> bool:
    return any(keyword in text for keyword in EXCLUDE_KEYWORDS)


def _is_valid_article(article: Dict[str, Any]) -> bool:
    return bool(article.get("title")) and bool(article.get("url")) and bool(
        article.get("description") or article.get("content")
    )


def _standardize_article(article: Dict[str, Any], port_name: str, search_term: str) -> Optional[Dict[str, Any]]:
    if not _is_valid_article(article):
        return None

    source_name = _safe_text(article.get("source", {}).get("name"))
    title = _safe_text(article.get("title"))
    description = _safe_text(article.get("description"))
    content = _safe_text(article.get("content"))
    author = _safe_text(article.get("author"))

    clean_text = _clean_text_for_model(title, description, content)
    lowered_text = clean_text.lower()

    if _is_excluded(lowered_text):
        return None

    matched_keywords = (
        find_all_matches(lowered_text, PORT_WORDS)
        + find_all_matches(lowered_text, MARITIME_WORDS)
        + find_all_matches(lowered_text, CRIME_WORDS)
        + find_all_matches(lowered_text, TRADE_WORDS)
    )

    assigned_categories = classify_article_strong(lowered_text)
    score = relevance_score(lowered_text)

    if not assigned_categories or score < 3:
        return None

    return {
        "port_name": port_name,
        "source": source_name,
        "author": author,
        "title": title,
        "description": description,
        "content": content,
        "url": _safe_text(article.get("url")),
        "image_url": _safe_text(article.get("urlToImage")),
        "published_at": _safe_text(article.get("publishedAt")),
        "search_term": search_term,
        "matched_keywords": matched_keywords,
        "matched_keywords_str": ", ".join(matched_keywords),
        "categories": assigned_categories,
        "categories_str": ", ".join(assigned_categories),
        "relevance_score": score,
        "clean_text": clean_text,
    }


def preprocess_news_articles(
    raw_articles: Iterable[Dict[str, Any]],
    *,
    port_name: str,
    search_term: str,
) -> pd.DataFrame:
    processed = []
    for article in raw_articles:
        standardized = _standardize_article(article, port_name=port_name, search_term=search_term)
        if standardized is not None:
            processed.append(standardized)

    df = pd.DataFrame(processed)

    expected_columns = [
        "port_name",
        "source",
        "author",
        "title",
        "description",
        "content",
        "url",
        "image_url",
        "published_at",
        "search_term",
        "matched_keywords",
        "matched_keywords_str",
        "categories",
        "categories_str",
        "relevance_score",
        "clean_text",
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = []

    if df.empty:
        return df.reindex(columns=expected_columns)

    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)

    text_columns = [
        "port_name",
        "source",
        "author",
        "title",
        "description",
        "content",
        "url",
        "image_url",
        "search_term",
        "matched_keywords_str",
        "categories_str",
        "clean_text",
    ]

    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).map(_normalize_whitespace)

    df["matched_keywords"] = df["matched_keywords"].apply(_safe_list)
    df["categories"] = df["categories"].apply(_safe_list)

    df = df.drop_duplicates(subset=["url"], keep="first").reset_index(drop=True)

    return df


def get_news_data(
    port_name: str,
    api_key: Optional[str] = None,
    *,
    page_size: int = 100,
    max_pages: int = 3,
) -> pd.DataFrame:
    """
    Main standardized method for the team.
    Input: port name
    Output: pandas DataFrame of processed port-related news
    """
    _ = get_port_info(port_name)  # validates that port exists in ports.csv

    key = api_key or os.getenv("NEWS_API_KEY")
    if not key:
        raise ValueError("Missing API key. Pass api_key=... or set NEWS_API_KEY in your environment.")

    query = build_port_news_query(port_name)
    client = NewsAPIClient(api_key=key)

    all_articles = []

    for page in range(1, max_pages + 1):
        payload = client.fetch_all_news(
            search=query,
            page_size=page_size,
            page=page,
        )
        articles = payload.get("articles", [])
        if not articles:
            break

        all_articles.extend(articles)

        if len(articles) < page_size:
            break

    return preprocess_news_articles(
        all_articles,
        port_name=port_name,
        search_term=query,
    )

#from news_api import get_news_data
#df = get_news_data("Port of Houston")
#print(df.head())