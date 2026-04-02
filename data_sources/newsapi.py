"""TheNewsAPI data source + preprocessing for port-congestion project.

Usage:
    export THENEWS_API_TOKEN='your_token_here'
    python news_api.py --search 'port congestion OR shipping OR freight' --limit 50 --save-csv processed_news.csv

This file is designed so the team can keep one file per data source.
The main function to call from elsewhere is:
    get_processed_news_data(...)
which returns a pandas DataFrame of standardized, processed news data.
"""
# insert API_TOKEN = "your_real_api_key_here"
#change token = api_token or API_TOKEN or os.getenv("THENEWS_API_TOKEN")


from dotenv import load_dotenv
load_dotenv()
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

token = api_token or os.getenv("THENEWS_API_TOKEN")
BASE_URL = "https://api.thenewsapi.com/v1/news/all"
DEFAULT_SEARCH = (
    '"port congestion" | port | shipping | freight | logistics | container | '
    'vessel | customs | backlog | strike | terminal | harbor'
)
DEFAULT_SEARCH_FIELDS = "title,description,keywords,main_text"
DEFAULT_LANGUAGE = "en"
DEFAULT_CATEGORIES = "business"
DEFAULT_TIMEOUT = 30


class TheNewsAPIError(Exception):
    """Raised when TheNewsAPI returns an error or an invalid response."""


@dataclass
class TheNewsAPIClient:
    api_token: str
    timeout: int = DEFAULT_TIMEOUT

    def fetch_all_news(
        self,
        search: str = DEFAULT_SEARCH,
        *,
        search_fields: str = DEFAULT_SEARCH_FIELDS,
        language: str = DEFAULT_LANGUAGE,
        categories: Optional[str] = DEFAULT_CATEGORIES,
        exclude_categories: Optional[str] = None,
        locale: Optional[str] = None,
        domains: Optional[str] = None,
        exclude_domains: Optional[str] = None,
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Fetch raw news JSON from TheNewsAPI all-news endpoint."""
        params: Dict[str, Any] = {
            "api_token": self.api_token,
            "search": search,
            "search_fields": search_fields,
            "language": language,
            "limit": int(limit),
            "page": int(page),
        }

        optional_params = {
            "categories": categories,
            "exclude_categories": exclude_categories,
            "locale": locale,
            "domains": domains,
            "exclude_domains": exclude_domains,
            "published_after": published_after,
            "published_before": published_before,
        }
        params.update({k: v for k, v in optional_params.items() if v not in (None, "")})

        response = requests.get(BASE_URL, params=params, timeout=self.timeout)

        try:
            payload = response.json()
        except ValueError as exc:
            raise TheNewsAPIError(f"Non-JSON response from API (status {response.status_code}).") from exc

        if not response.ok:
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            code = error.get("code", "unknown_error")
            message = error.get("message", "Unknown API error")
            raise TheNewsAPIError(f"API request failed ({response.status_code}) [{code}]: {message}")

        if not isinstance(payload, dict) or "data" not in payload:
            raise TheNewsAPIError("Unexpected API response format: missing 'data'.")

        return payload


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


def _standardize_article(article: Dict[str, Any], search_term: str) -> Dict[str, Any]:
    categories = _safe_list(article.get("categories"))
    keywords = _safe_text(article.get("keywords"))

    standardized = {
        "uuid": _safe_text(article.get("uuid")),
        "source": _safe_text(article.get("source")),
        "title": _safe_text(article.get("title")),
        "description": _safe_text(article.get("description")),
        "snippet": _safe_text(article.get("snippet")),
        "keywords": keywords,
        "url": _safe_text(article.get("url")),
        "image_url": _safe_text(article.get("image_url")),
        "language": _safe_text(article.get("language")),
        "locale": _safe_text(article.get("locale")),
        "categories": categories,
        "categories_str": ", ".join(categories),
        "published_at": _safe_text(article.get("published_at")),
        "search_term": search_term,
    }

    standardized["clean_text"] = _clean_text_for_model(
        standardized["title"],
        standardized["description"],
        standardized["snippet"],
        standardized["keywords"],
        standardized["categories_str"],
    )

    return standardized


def preprocess_news_articles(raw_articles: Iterable[Dict[str, Any]], search_term: str) -> pd.DataFrame:
    """Convert raw article JSON into a clean, standardized DataFrame."""
    processed = [_standardize_article(article, search_term) for article in raw_articles]
    df = pd.DataFrame(processed)

    expected_columns = [
        "uuid",
        "source",
        "title",
        "description",
        "snippet",
        "keywords",
        "url",
        "image_url",
        "language",
        "locale",
        "categories",
        "categories_str",
        "published_at",
        "search_term",
        "clean_text",
    ]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = []

    if df.empty:
        return df.reindex(columns=expected_columns)

    # Datetime standardization: API docs say dates are UTC/GMT.
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)

    # Missing values.
    text_columns = [
        "uuid",
        "source",
        "title",
        "description",
        "snippet",
        "keywords",
        "url",
        "image_url",
        "language",
        "locale",
        "categories_str",
        "search_term",
        "clean_text",
    ]
    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).map(_normalize_whitespace)

    df["categories"] = df["categories"].apply(_safe_list)

    # Remove low-quality rows.
    df = df[~((df["title"] == "") & (df["description"] == "") & (df["snippet"] == ""))].copy()

    # Deduplicate articles.
    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"], keep="first")
    if "uuid" in df.columns:
        df = df.drop_duplicates(subset=["uuid"], keep="first")

    # Derived features useful for ML / time series.
    df["has_image"] = df["image_url"].ne("")
    df["title_length"] = df["title"].str.len()
    df["description_length"] = df["description"].str.len()
    df["clean_text_length"] = df["clean_text"].str.len()
    df["category_count"] = df["categories"].apply(len)
    df["published_date"] = df["published_at"].dt.date.astype("string")
    df["published_hour_utc"] = df["published_at"].dt.hour
    df["published_dayofweek_utc"] = df["published_at"].dt.dayofweek

    # Consistent ordering.
    sort_cols = ["published_at", "source", "title"]
    df = df.sort_values(sort_cols, ascending=[False, True, True], na_position="last").reset_index(drop=True)

    return df


def get_processed_news_data(
    api_token: Optional[str] = None,
    *,
    search: str = DEFAULT_SEARCH,
    search_fields: str = DEFAULT_SEARCH_FIELDS,
    language: str = DEFAULT_LANGUAGE,
    categories: Optional[str] = DEFAULT_CATEGORIES,
    exclude_categories: Optional[str] = None,
    locale: Optional[str] = None,
    domains: Optional[str] = None,
    exclude_domains: Optional[str] = None,
    published_after: Optional[str] = None,
    published_before: Optional[str] = None,
    limit: int = 50,
    page: int = 1,
) -> pd.DataFrame:
    """Fetch + preprocess news and return a standardized pandas DataFrame."""
    token = api_token or os.getenv("THENEWS_API_TOKEN")
    if not token:
        raise ValueError(
            "Missing API token. Pass api_token=... or set THENEWS_API_TOKEN in your environment."
        )

    client = TheNewsAPIClient(api_token=token)
    payload = client.fetch_all_news(
        search=search,
        search_fields=search_fields,
        language=language,
        categories=categories,
        exclude_categories=exclude_categories,
        locale=locale,
        domains=domains,
        exclude_domains=exclude_domains,
        published_after=published_after,
        published_before=published_before,
        limit=limit,
        page=page,
    )
    articles = payload.get("data", [])
    return preprocess_news_articles(articles, search_term=search)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and preprocess news from TheNewsAPI.")
    parser.add_argument("--api-token", default=None, help="TheNewsAPI token. Defaults to env var THENEWS_API_TOKEN.")
    parser.add_argument("--search", default=DEFAULT_SEARCH, help="Search query for TheNewsAPI.")
    parser.add_argument("--search-fields", default=DEFAULT_SEARCH_FIELDS, help="Comma-separated search fields.")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Language filter, e.g. en.")
    parser.add_argument("--categories", default=DEFAULT_CATEGORIES, help="Comma-separated categories.")
    parser.add_argument("--exclude-categories", default=None, help="Categories to exclude.")
    parser.add_argument("--locale", default=None, help="Locale filter, e.g. us,gb.")
    parser.add_argument("--domains", default=None, help="Comma-separated source domains to include.")
    parser.add_argument("--exclude-domains", default=None, help="Comma-separated source domains to exclude.")
    parser.add_argument("--published-after", default=None, help="Only include articles published after YYYY-MM-DD.")
    parser.add_argument("--published-before", default=None, help="Only include articles published before YYYY-MM-DD.")
    parser.add_argument("--limit", type=int, default=50, help="Number of articles to request.")
    parser.add_argument("--page", type=int, default=1, help="Page number.")
    parser.add_argument("--save-csv", default=None, help="Optional CSV output path.")
    parser.add_argument("--save-json", default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    df = get_processed_news_data(
        api_token=args.api_token,
        search=args.search,
        search_fields=args.search_fields,
        language=args.language,
        categories=args.categories,
        exclude_categories=args.exclude_categories,
        locale=args.locale,
        domains=args.domains,
        exclude_domains=args.exclude_domains,
        published_after=args.published_after,
        published_before=args.published_before,
        limit=args.limit,
        page=args.page,
    )

    print(f"Fetched and processed {len(df)} articles.")
    if not df.empty:
        print(df.head(10).to_string(index=False))

    if args.save_csv:
        df.to_csv(args.save_csv, index=False)
        print(f"Saved CSV to {args.save_csv}")

    if args.save_json:
        df.to_json(args.save_json, orient="records", indent=2, date_format="iso")
        print(f"Saved JSON to {args.save_json}")


if __name__ == "__main__":
    main()
