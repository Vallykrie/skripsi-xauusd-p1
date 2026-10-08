from __future__ import annotations

import pandas as pd

from thesis_experiments.macro_features import add_macro_features


def test_release_at_decision_is_deferred_and_future_is_hidden():
    decisions = pd.DataFrame({"decision_time": pd.to_datetime([
        "2024-01-01T10:00:00Z", "2024-01-01T11:00:00Z", "2024-01-01T12:00:00Z"
    ])})
    events = pd.DataFrame({
        "event_code": ["US_NFP"], "event_time_utc": pd.to_datetime(["2024-01-01T10:00:00Z"]),
        "value_id": [9], "actual": [110.0], "forecast": [100.0],
    })
    result = add_macro_features(decisions, events)
    assert pd.isna(result.loc[0, "macro_us_nfp_surprise"])
    assert result.loc[0, "macro_us_nfp_within_1h"] == 0
    assert result.loc[1, "macro_us_nfp_surprise"] == 10.0
    assert result.loc[1, "macro_us_nfp_age_hours"] == 1.0
    assert result.loc[1, "macro_us_nfp_within_1h"] == 1


def test_missing_forecast_stays_missing_and_event_expires():
    decisions = pd.DataFrame({"decision_time": pd.to_datetime([
        "2024-01-01T11:00:00Z", "2024-01-08T10:00:00Z"
    ])})
    events = pd.DataFrame({
        "event_code": ["US_NFP", "US_RATE"],
        "event_time_utc": pd.to_datetime(["2024-01-01T10:00:00Z", "2024-01-01T10:00:00Z"]),
        "value_id": [9, 10], "actual": [110.0, 5.0], "forecast": [float("nan"), float("nan")],
    })
    result = add_macro_features(decisions, events)
    assert pd.isna(result.loc[0, "macro_us_nfp_surprise"])
    assert "macro_us_rate_surprise" not in result
    assert result.loc[1, "macro_us_nfp_expired"] == 1
    assert pd.isna(result.loc[1, "macro_us_nfp_surprise"])
    assert result.loc[1, "macro_us_nfp_age_hours"] == 168.0


def test_same_time_events_have_stable_value_id_order():
    decisions = pd.DataFrame({"decision_time": pd.to_datetime(["2024-01-01T11:00:00Z"])})
    events = pd.DataFrame({
        "event_code": ["US_NFP", "US_NFP"],
        "event_time_utc": pd.to_datetime(["2024-01-01T10:00:00Z"] * 2),
        "value_id": [2, 1], "actual": [20.0, 100.0], "forecast": [10.0, 80.0],
    })
    first = add_macro_features(decisions, events)
    second = add_macro_features(decisions, events.iloc[::-1].reset_index(drop=True))
    assert first.loc[0, "macro_us_nfp_surprise"] == 10.0
    assert second.loc[0, "macro_us_nfp_surprise"] == 10.0
