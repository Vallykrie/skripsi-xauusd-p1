"""Causal post-release macro features for the frozen MT5 calendar snapshot."""

from __future__ import annotations

import numpy as np
import pandas as pd

NUMERIC_CODES = (
    "US_CPI_MM", "US_CPI_YY", "US_CORE_CPI_MM", "US_CORE_CPI_YY",
    "US_NFP", "US_UNEMPLOYMENT",
)
EVENT_CODES = (*NUMERIC_CODES, "US_RATE", "US_FOMC")
MACRO_COLUMNS = tuple(
    f"macro_{code.lower()}_{suffix}"
    for code in EVENT_CODES
    for suffix in (("surprise", "age_hours", "expired", "within_1h", "within_6h", "within_24h")
                   if code in NUMERIC_CODES else ("age_hours", "expired", "within_1h", "within_6h", "within_24h"))
)


def add_macro_features(frame: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Attach only events released strictly before each bar decision time."""
    if "decision_time" not in frame or not frame["decision_time"].is_monotonic_increasing:
        raise ValueError("Decision times must be present and chronological")
    required = {"event_code", "event_time_utc", "value_id", "actual", "forecast"}
    if not required.issubset(events.columns):
        raise ValueError("Macro events are missing required snapshot columns")
    if frame["decision_time"].dt.tz is None or events["event_time_utc"].dt.tz is None:
        raise ValueError("Macro join requires timezone-aware UTC timestamps")
    result = frame.copy()
    left = pd.DataFrame({"decision_time": result["decision_time"], "row_index": np.arange(len(result))})
    for code in EVENT_CODES:
        prefix = f"macro_{code.lower()}"
        subset = events.loc[events["event_code"] == code,
                            ["event_time_utc", "value_id", "actual", "forecast"]].copy()
        subset = subset.sort_values(["event_time_utc", "value_id"]).drop_duplicates("event_time_utc", keep="last")
        if code in NUMERIC_CODES:
            subset["surprise"] = pd.to_numeric(subset["actual"], errors="coerce") - pd.to_numeric(subset["forecast"], errors="coerce")
        joined = pd.merge_asof(
            left, subset, left_on="decision_time", right_on="event_time_utc",
            direction="backward", allow_exact_matches=False,
        ).sort_values("row_index")
        age = (joined["decision_time"] - joined["event_time_utc"]).dt.total_seconds() / 3600
        expired = age.ge(168)
        if code in NUMERIC_CODES:
            result[f"{prefix}_surprise"] = joined["surprise"].where(~expired).to_numpy(dtype=float)
        result[f"{prefix}_age_hours"] = age.clip(upper=168).to_numpy(dtype=float)
        result[f"{prefix}_expired"] = expired.astype(int).to_numpy()
        for hours in (1, 6, 24):
            result[f"{prefix}_within_{hours}h"] = ((age > 0) & (age <= hours)).astype(int).to_numpy()
    return result
