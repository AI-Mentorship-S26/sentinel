"""
Port News Congestion Scorer (UPGRADED)
======================================
Now includes:
✔ FinBERT sentiment
✔ Keyword congestion scoring
✔ Time decay weighting (recent news matters more)
✔ Port-level scoring (weighted avg + volatility + spike)
✔ CSV outputs including final port scores
"""

from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

import re
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import pandas as pd

# ── FinBERT setup ─────────────────────────────────────────────
try:
    from transformers import pipeline as hf_pipeline

    _sentiment_pipe = None

    def get_sentiment_pipe():
        global _sentiment_pipe
        if _sentiment_pipe is None:
            print("Loading FinBERT model...")
            _sentiment_pipe = hf_pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                truncation=True,
                max_length=512,
            )
        return _sentiment_pipe

    FINBERT_AVAILABLE = True

except ImportError:
    FINBERT_AVAILABLE = False
    print("[warn] transformers not installed — keyword-only mode")

# ── KEYWORD MODEL ─────────────────────────────────────────────
CONGESTION_KEYWORDS = {
    "congestion": 10, "backlog": 10, "delay": 8, "strike": 9,
    "walkout": 9, "labor dispute": 9, "backup": 7,
    "anchored": 8, "vessel queue": 9, "port closure": 10,
    "bottleneck": 8, "storm": 6, "hurricane": 8,
    "crime": 3, "smuggling": 4,

    # positive signals (reduce congestion)
    "cleared": -6, "efficient": -4, "resolved": -6,
    "reopened": -4, "back to normal": -7,
}

def keyword_congestion_score(text: str) -> float:
    text = text.lower()
    score = 0.0
    for kw, weight in CONGESTION_KEYWORDS.items():
        if re.search(rf"\b{re.escape(kw)}\b", text):
            score += weight
    return score

# ── SENTIMENT → CONGESTION ───────────────────────────────────
def finbert_to_congestion(label: str, score: float) -> float:
    if label == "negative":
        return score
    elif label == "positive":
        return -score
    return 0.0

# ── TIME DECAY (CRITICAL FOR REAL SIGNALS) ───────────────────
def time_decay_weight(published_date, half_life_days=3):
    """
    Exponential decay:
    Newer articles matter more than older ones.
    """
    if pd.isna(published_date):
        return 1.0

    age_days = (datetime.utcnow() - published_date).days
    return 0.5 ** (age_days / half_life_days)

# ── ARTICLE SCORING ──────────────────────────────────────────
def score_article(title: str, existing_kw_score: float = 0) -> dict:
    kw_score = keyword_congestion_score(title)
    combined_kw = kw_score + (existing_kw_score * 0.3)

    sentiment_score = 0.0
    sentiment_label = "neutral"

    if FINBERT_AVAILABLE:
        try:
            pipe = get_sentiment_pipe()
            result = pipe(title[:512])[0]
            sentiment_label = result["label"]
            sentiment_score = finbert_to_congestion(
                result["label"], result["score"]
            )
        except Exception as e:
            print(f"[warn] FinBERT error: {e}")

    # Normalize scores into 0–100 range
    kw_norm = max(0, min(50, combined_kw * 2.5))
    sent_norm = max(0, min(50, (sentiment_score + 1) * 25))

    congestion_risk = (kw_norm * 0.6) + (sent_norm * 0.4)

    return {
        "sentiment_label": sentiment_label,
        "sentiment_score": round(sentiment_score, 3),
        "congestion_keyword_score": round(kw_score, 1),
        "congestion_risk": round(congestion_risk, 1),
    }

# ── PORT-LEVEL MODEL ─────────────────────────────────────────
def compute_port_score(article_df: pd.DataFrame) -> dict:
    if article_df.empty:
        return {}

    total_weight = article_df["decay_weight"].sum()
    if total_weight == 0:
        return {}

    # Core signal
    weighted_avg = article_df["weighted_risk"].sum() / total_weight

    # Risk characteristics
    volatility = article_df["congestion_risk"].std()
    spike = article_df["congestion_risk"].max() - article_df["congestion_risk"].mean()

    # Final blended score
    port_score = (
        (weighted_avg * 0.7)
        + (min(20, volatility) * 0.2)
        + (min(20, spike) * 0.1)
    )

    return {
        "port_score": round(min(100, port_score), 2),
        "weighted_avg_risk": round(weighted_avg, 2),
        "volatility": round(volatility, 2),
        "spike": round(spike, 2),
    }

# ── MAIN PORT SCORING ────────────────────────────────────────
def score_port(port_name: str, news_df: Optional[pd.DataFrame] = None, max_pages: int = 3):

    if news_df is None:
        sys.path.insert(0, str(Path(__file__).parent))
        from news import get_news

        print(f"Fetching news for {port_name}...")
        news_df = get_news(port_name, max_pages=max_pages)

    if news_df is None or news_df.empty:
        print(f"No articles for {port_name}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

    print(f"Scoring {len(news_df)} articles...")

    scored_rows = []

    for _, row in news_df.iterrows():
        title = str(row.get("title", ""))
        existing_score = float(row.get("score", 0))

        scores = score_article(title, existing_score)

        # ── APPLY TIME DECAY ──
        published = pd.to_datetime(row.get("published"), errors="coerce")
        decay = time_decay_weight(published)

        scores["decay_weight"] = decay
        scores["weighted_risk"] = scores["congestion_risk"] * decay

        scored_rows.append(scores)

    scores_df = pd.DataFrame(scored_rows)
    article_df = pd.concat([news_df.reset_index(drop=True), scores_df], axis=1)

    # Date formatting
    article_df["published"] = pd.to_datetime(article_df["published"], errors="coerce")
    article_df["date"] = article_df["published"].dt.date
    article_df["week"] = article_df["published"].dt.to_period("W").astype(str)

    # ── DAILY ──
    daily_df = article_df.groupby(["port", "date"]).agg(
        avg_congestion_risk=("congestion_risk", "mean"),
        n_articles=("congestion_risk", "count"),
    ).reset_index()

    # ── WEEKLY ──
    weekly_df = article_df.groupby(["port", "week"]).agg(
        avg_congestion_risk=("congestion_risk", "mean"),
        n_articles=("congestion_risk", "count"),
    ).reset_index()

    # ── FINAL PORT SCORE ──
    port_summary = compute_port_score(article_df)

    return article_df, daily_df, weekly_df, port_summary

# ── ALL PORTS ────────────────────────────────────────────────
def score_all_ports(ports_file="CSV Files/ports.csv", max_pages=2):

    ports_df = pd.read_csv(ports_file)
    port_names = ports_df["port_name"].tolist()

    all_articles = []
    all_daily = []
    all_weekly = []
    port_summaries = []

    for port in port_names:
        try:
            a, d, w, summary = score_port(port, max_pages=max_pages)

            if not a.empty:
                all_articles.append(a)
                all_daily.append(d)
                all_weekly.append(w)

                if summary:
                    summary["port"] = port
                    port_summaries.append(summary)

        except Exception as e:
            print(f"[error] {port}: {e}")

    # Save outputs
    if all_articles:
        pd.concat(all_articles).to_csv("articles.csv", index=False)
        pd.concat(all_daily).to_csv("daily.csv", index=False)
        pd.concat(all_weekly).to_csv("weekly.csv", index=False)

    if port_summaries:
        pd.DataFrame(port_summaries).to_csv("port_scores.csv", index=False)

    print("Saved all outputs.")

# ── CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    score_all_ports()

    