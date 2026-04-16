from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import requests
from dotenv import load_dotenv

# load API key from .env
load_dotenv()

# ----------------------------
# CONFIG
# ----------------------------
BASE_URL = "https://newsapi.org/v2/everything"

PORT_WORDS = ["port", "ports", "seaport", "harbor", "harbour", "terminal"]
MARITIME_WORDS = ["shipping", "vessel", "cargo", "freight", "container", "logistics"]
CRITICAL_WORDS = ["congestion", "strike", "delay", "smuggling", "sanctions", "trade"]

EXCLUDE_WORDS = ["usb", "software", "gaming", "airport", "wine", "computer"]


# ----------------------------
# API CLIENT
# ----------------------------
@dataclass
class NewsAPIClient:
    api_key: str

    def fetch(self, query: str, page: int = 1, page_size: int = 50):
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "page": page,
            "apiKey": self.api_key,
        }

        res = requests.get(BASE_URL, params=params, timeout=20)

        try:
            data = res.json()
        except Exception:
            raise Exception(f"Bad response from API (status {res.status_code})")

        # API error handling
        if res.status_code != 200:
            raise Exception(data)

        return data.get("articles", [])


# ----------------------------
# TEXT HELPERS
# ----------------------------
def match_words(text: str, words: List[str]) -> List[str]:
    return [w for w in words if re.search(rf"\b{re.escape(w)}\b", text)]


def has_word(text: str, words: List[str]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)


def clean_text(article: Dict[str, Any]) -> str:
    return " ".join([
        str(article.get("title", "")),
        str(article.get("description", "")),
        str(article.get("content", ""))
    ]).lower()


# ----------------------------
# FILTER LOGIC
# ----------------------------
def is_relevant(text: str, port_name: str) -> bool:

    # kill obvious irrelevant topics
    if has_word(text, EXCLUDE_WORDS):
        return False

    # must be at least related to port OR shipping world
    if port_name.lower() not in text and not has_word(text, MARITIME_WORDS):
        return False

    # must contain real logistics context
    if not has_word(text, ["cargo", "container", "vessel", "terminal", "freight"]):
        return False

    return True


def score(text: str) -> int:
    return (
        2 * len(match_words(text, PORT_WORDS)) +
        2 * len(match_words(text, MARITIME_WORDS)) +
        3 * len(match_words(text, CRITICAL_WORDS))
    )


def process_article(article: Dict[str, Any], port_name: str) -> Optional[Dict[str, Any]]:

    if not article.get("title") or not article.get("url"):
        return None

    text = clean_text(article)

    if not is_relevant(text, port_name):
        return None

    relevance = score(text)

    # strict threshold so junk doesn’t pass
    if relevance < 6:
        return None

    return {
        "port": port_name,
        "title": article["title"],
        "source": article.get("source", {}).get("name"),
        "url": article["url"],
        "published": article.get("publishedAt"),
        "score": relevance
    }


# ----------------------------
# QUERY BUILDER
# ----------------------------
def build_query(port_name: str) -> str:
    return (
        f'"{port_name}" AND ('
        f'"cargo" OR "shipping" OR "freight" OR '
        f'"container" OR "logistics" OR "port congestion"'
        f') NOT ("usb" OR "software" OR "gaming" OR "airport")'
    )


# ----------------------------
# MAIN FUNCTION (FIXED PAGING)
# ----------------------------
def get_news(port_name: str, max_pages: int = 3):

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("Missing NEWS_API_KEY in .env")

    client = NewsAPIClient(api_key)
    query = build_query(port_name)

    results = []

    # ----------------------------
    # SAFE PAGING LOOP (OPTION 2 FIX)
    # ----------------------------
    for page in range(1, max_pages + 1):

        try:
            articles = client.fetch(query, page=page, page_size=50)

        except Exception as e:
            print(f"[STOP] API error at page {page}: {e}")
            break

        # no more results → stop early
        if not articles:
            break

        for article in articles:
            processed = process_article(article, port_name)
            if processed:
                results.append(processed)

    df = pd.DataFrame(results)

    if not df.empty:
        df["published"] = pd.to_datetime(df["published"], errors="coerce")

        # best + newest first
        df = df.sort_values(by=["score", "published"], ascending=[False, False])

    return df


# ----------------------------
# TEST RUN
# ----------------------------
if __name__ == "__main__":
    port = input("Enter port name: ").strip()

    df = get_news(port)

    if df.empty:
        print("No relevant news found.")
    else:
        print(df.head(10))
        print(f"\nTotal articles: {len(df)}")


        # ============================
# HOW TO RUN THIS FILE
# ============================

# 1. Open terminal in this folder
#    (make sure you're inside the project directory)

# 2. Install dependencies if you haven't:
#    pip install pandas requests python-dotenv

# 3. Create a .env file in SAME folder as this script:
#    NEWS_API_KEY=your_api_key_here

# 4. Make sure this file exists:
#    data_sources/ports.csv
#    (otherwise the script will crash or behave weirdly)

# 5. Run the script:
#    python your_filename.py

# 6. When prompted:
#    Enter port name: Port of Los Angeles