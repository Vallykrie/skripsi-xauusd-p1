from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

K1_COLUMNS = [
    "return_lag_0",
    "return_lag_1",
    "return_lag_2",
    "return_lag_3",
    "return_lag_4",
    "return_lag_5",
    "log_close_open",
    "log_high_low",
    "sigma_24",
]
K2_COLUMNS = [
    *K1_COLUMNS,
    "rsi_14",
    "macd_line_norm",
    "macd_signal_norm",
    "macd_hist_norm",
]

_OHLC_COLUMNS = ["open", "high", "low", "close"]
_SUPPORTED_THRESHOLD_MULTIPLIERS = (0.25, 0.5, 1.0)
_ONE_HOUR = pd.Timedelta(hours=1)


def label_target_return(target_return: float, threshold: float) -> str:
    """Map a finite return to the proposal's inclusive HOLD boundaries."""
    if not np.isfinite(target_return):
        raise ValueError("target return must be finite")
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError("target threshold must be finite and nonnegative")
    if target_return < -threshold:
        return "SELL"
    if target_return > threshold:
        return "BUY"
    return "HOLD"


def _validate_utc_series(times: pd.Series) -> None:
    if not isinstance(times.dtype, pd.DatetimeTZDtype) or str(times.dt.tz) != "UTC":
        raise ValueError("time must be a timezone-aware UTC datetime column")
    if times.isna().any():
        raise ValueError("time must not contain missing values")
    if times.duplicated().any():
        raise ValueError("time values must be unique")
    if not times.is_monotonic_increasing:
        raise ValueError("time values must be strictly increasing")


def _validate_inputs(
    frame: pd.DataFrame,
    segment_ids: Sequence[Any],
    threshold_multiplier: float,
    target_end_allowed: Sequence[bool] | None,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    missing = [column for column in ["time", *_OHLC_COLUMNS] if column not in frame]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    _validate_utc_series(frame["time"])

    numeric = frame.loc[:, _OHLC_COLUMNS].apply(pd.to_numeric, errors="coerce")
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("OHLC prices must be finite and positive")
    invalid_shape = (
        (numeric["high"] < numeric[["open", "close"]].max(axis=1))
        | (numeric["low"] > numeric[["open", "close"]].min(axis=1))
        | (numeric["high"] < numeric["low"])
    )
    if invalid_shape.any():
        raise ValueError("OHLC high/low relationships are invalid")

    segments = np.asarray(segment_ids, dtype=object)
    if segments.ndim != 1 or len(segments) != len(frame):
        raise ValueError("segment identifiers must align one-to-one with rows")
    if pd.isna(segments).any():
        raise ValueError("segment identifiers must not be missing")

    multiplier = float(threshold_multiplier)
    if not np.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("threshold multiplier must be finite and positive")
    if multiplier not in _SUPPORTED_THRESHOLD_MULTIPLIERS:
        raise ValueError("threshold multiplier is not supported by the frozen protocol")

    if target_end_allowed is None:
        allowed = np.ones(len(frame), dtype=bool)
    else:
        raw_allowed = np.asarray(target_end_allowed)
        if raw_allowed.ndim != 1 or len(raw_allowed) != len(frame):
            raise ValueError("target end permissions must align one-to-one with rows")
        if pd.isna(raw_allowed).any():
            raise ValueError("target end permissions must not be missing")
        if not all(isinstance(value, (bool, np.bool_)) for value in raw_allowed):
            raise ValueError("target end permissions must be boolean")
        allowed = raw_allowed.astype(bool)
    return numeric, segments, allowed


def _wilder_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    result = np.full(len(closes), np.nan, dtype=float)
    if len(closes) <= period:
        return result

    differences = np.diff(closes)
    gains = np.maximum(differences, 0.0)
    losses = np.maximum(-differences, 0.0)
    average_gain = float(gains[:period].mean())
    average_loss = float(losses[:period].mean())

    def rsi_value(gain: float, loss: float) -> float:
        if gain == 0.0 and loss == 0.0:
            return 50.0
        if loss == 0.0:
            return 100.0
        if gain == 0.0:
            return 0.0
        return 100.0 - 100.0 / (1.0 + gain / loss)

    result[period] = rsi_value(average_gain, average_loss)
    for position in range(period + 1, len(closes)):
        average_gain = (
            (period - 1) * average_gain + gains[position - 1]
        ) / period
        average_loss = (
            (period - 1) * average_loss + losses[position - 1]
        ) / period
        result[position] = rsi_value(average_gain, average_loss)
    return result


def _seeded_ema(values: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(values), np.nan, dtype=float)
    if len(values) < period:
        return result
    result[period - 1] = values[:period].mean()
    alpha = 2.0 / (period + 1.0)
    for position in range(period, len(values)):
        result[position] = alpha * values[position] + (1.0 - alpha) * result[position - 1]
    return result


def _macd(closes: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    line = _seeded_ema(closes, 12) - _seeded_ema(closes, 26)
    signal = np.full(len(closes), np.nan, dtype=float)
    valid_positions = np.flatnonzero(np.isfinite(line))
    if len(valid_positions) >= 9:
        valid_signal = _seeded_ema(line[valid_positions], 9)
        signal[valid_positions] = valid_signal
    return line, signal, line - signal


def _segment_features(numeric: pd.DataFrame) -> pd.DataFrame:
    closes = numeric["close"].to_numpy(dtype=float)
    size = len(numeric)
    returns = np.full(size, np.nan, dtype=float)
    if size > 1:
        returns[1:] = np.log(closes[1:] / closes[:-1])

    features: dict[str, np.ndarray] = {}
    for lag in range(6):
        values = np.full(size, np.nan, dtype=float)
        if lag < size:
            values[lag:] = returns[: size - lag]
        features[f"return_lag_{lag}"] = values
    features["log_close_open"] = np.log(
        closes / numeric["open"].to_numpy(dtype=float)
    )
    features["log_high_low"] = np.log(
        numeric["high"].to_numpy(dtype=float)
        / numeric["low"].to_numpy(dtype=float)
    )
    features["sigma_24"] = (
        pd.Series(returns).rolling(window=24, min_periods=24).std(ddof=1).to_numpy()
    )
    features["rsi_14"] = _wilder_rsi(closes)
    macd_line, macd_signal, macd_hist = _macd(closes)
    features["macd_line_norm"] = macd_line / closes
    features["macd_signal_norm"] = macd_signal / closes
    features["macd_hist_norm"] = macd_hist / closes
    return pd.DataFrame(features)


def build_feature_frame(
    frame: pd.DataFrame,
    segment_ids: Sequence[Any],
    *,
    threshold_multiplier: float = 0.5,
    target_end_allowed: Sequence[bool] | None = None,
) -> pd.DataFrame:
    """Build causal K1/K2 features and one-hour targets without dropping rows.

    Each ``target_end_allowed`` value describes whether the bar at that source
    row may serve as a target endpoint. A decision at row ``t`` therefore uses
    the permission attached to row ``t + 1``.
    """
    numeric, segments, allowed = _validate_inputs(
        frame, segment_ids, threshold_multiplier, target_end_allowed
    )
    result = frame.copy()
    result["segment_id"] = segments
    result["segment_bar_number"] = np.nan
    for column in K2_COLUMNS:
        result[column] = np.nan

    run_starts = np.r_[True, segments[1:] != segments[:-1]] if len(frame) else np.array([])
    run_ids = np.cumsum(run_starts) - 1
    for run_id in np.unique(run_ids):
        positions = np.flatnonzero(run_ids == run_id)
        computed = _segment_features(numeric.iloc[positions].reset_index(drop=True))
        result.iloc[positions, result.columns.get_indexer(K2_COLUMNS)] = computed.to_numpy()
        result.iloc[
            positions, result.columns.get_loc("segment_bar_number")
        ] = np.arange(1, len(positions) + 1)

    feature_values = result.loc[:, K2_COLUMNS].to_numpy(dtype=float)
    result["feature_eligible"] = (
        result["segment_bar_number"].to_numpy(dtype=float) >= 50
    ) & np.isfinite(feature_values).all(axis=1)

    times = frame["time"]
    next_times = times.shift(-1)
    next_closes = numeric["close"].shift(-1)
    result["decision_time"] = times + _ONE_HOUR
    result["target_end_time"] = next_times + _ONE_HOUR
    result["target_return"] = np.log(next_closes / numeric["close"])
    result["target_threshold"] = result["sigma_24"] * float(threshold_multiplier)

    same_segment = pd.Series(segments).shift(-1).eq(pd.Series(segments)).to_numpy()
    exact_hour = (next_times - times).eq(_ONE_HOUR).to_numpy()
    endpoint_allowed = pd.Series(allowed).shift(-1, fill_value=False).to_numpy()
    sigma = result["sigma_24"].to_numpy(dtype=float)
    target_eligible = (
        exact_hour
        & same_segment
        & endpoint_allowed
        & np.isfinite(sigma)
        & (sigma > 0)
    )
    result["target_eligible"] = target_eligible

    labels = np.full(len(result), pd.NA, dtype=object)
    target_returns = result["target_return"].to_numpy(dtype=float)
    thresholds = result["target_threshold"].to_numpy(dtype=float)
    for position in np.flatnonzero(target_eligible):
        labels[position] = label_target_return(
            target_returns[position], thresholds[position]
        )
    result["target_label"] = pd.array(labels, dtype="string")
    return result


def _as_utc_boundary(value: Any, name: str) -> pd.Timestamp:
    boundary = pd.Timestamp(value)
    if boundary.tzinfo is None or str(boundary.tz) != "UTC":
        raise ValueError(f"{name} must be a timezone-aware UTC timestamp")
    return boundary


def evaluation_mask(
    feature_frame: pd.DataFrame,
    interval_start: Any,
    interval_end: Any,
) -> pd.Series:
    """Return rows whose decision and complete target fit a half-open interval."""
    start = _as_utc_boundary(interval_start, "interval start")
    end = _as_utc_boundary(interval_end, "interval end")
    if start >= end:
        raise ValueError("evaluation interval must have positive duration")
    required = {
        "decision_time",
        "target_end_time",
        "feature_eligible",
        "target_eligible",
    }
    missing = sorted(required - set(feature_frame.columns))
    if missing:
        raise ValueError(f"feature frame is missing: {', '.join(missing)}")

    decision = feature_frame["decision_time"]
    target_end = feature_frame["target_end_time"]
    return (
        feature_frame["feature_eligible"].astype(bool)
        & feature_frame["target_eligible"].astype(bool)
        & decision.ge(start)
        & decision.lt(end)
        & target_end.lt(end)
    )
