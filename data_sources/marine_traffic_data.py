"""Programmatic ML-focused data access for AIM Port Intelligence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from core import PortIntelligenceService
from data_sources.models import PortQueryRequest, QueryFilters


def get_marine_traffic_data(port_input: str) -> pd.DataFrame:
    """Return compact ML-ready vessel-level DataFrame."""
    if not port_input or not port_input.strip():
        raise ValueError("No port entered.")

    service = PortIntelligenceService()
    request = PortQueryRequest(
        portInput=port_input.strip(),
        timeHorizonHours=48,
        page=1,
        pageSize=50,
        filters=QueryFilters(
            onlyDelayed=False,
            minSeverity="none",
            minConfidence="low",
        ),
    )

    response = service.query_port(request)
    vessels = response.vessels or []
    quality = response.quality
    problems = response.problems or []

    rows: list[dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc)

    for vessel in vessels:
        eta_val = getattr(vessel, "etaUtc", None)
        eta_iso = _safe_value(eta_val)

        eta_hours = None
        if isinstance(eta_val, datetime):
            eta_hours = (eta_val - now_utc).total_seconds() / 3600.0

        rows.append(
            {
                # Port-level risk context
                "problem_count": len(problems),
                "overall_confidence": getattr(quality, "overallConfidence", None),
                "stale_data_warning": getattr(quality, "staleDataWarning", None),
                # Vessel-level predictive features
                "vessel_type": getattr(vessel, "vesselType", None),
                "flag": getattr(vessel, "flag", None),
                "origin_port": getattr(vessel, "originPort", None),
                "status": getattr(vessel, "status", None),
                "confidence": getattr(vessel, "confidence", None),
                "eta_utc": eta_iso,
                "eta_hours_to_arrival": eta_hours,
                # Target (for training delay model)
                "is_delayed": getattr(vessel, "isDelayed", None),
            }
        )

    df = pd.DataFrame(rows)

    # Remove exact duplicates on model-relevant fields
    if not df.empty:
        df = df.drop_duplicates(
            subset=[
                "vessel_type",
                "flag",
                "origin_port",
                "status",
                "confidence",
                "eta_utc",
                "is_delayed",
            ]
        ).reset_index(drop=True)

    # Ensure stable schema even if empty
    required_cols = [
        "problem_count",
        "overall_confidence",
        "stale_data_warning",
        "vessel_type",
        "flag",
        "origin_port",
        "status",
        "confidence",
        "eta_utc",
        "eta_hours_to_arrival",
        "is_delayed",
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.NA

    return df[required_cols]


def _safe_value(value: Any) -> Any:
    """Convert datetime values to ISO-8601 string."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value

