from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_MARKET_COLUMNS = (
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
)

EXPECTED_FEATURES = {
    "K1": (
        "return_lag_0",
        "return_lag_1",
        "return_lag_2",
        "return_lag_3",
        "return_lag_4",
        "return_lag_5",
        "log_close_open",
        "log_high_low",
        "sigma_24",
    ),
    "K2": (
        "return_lag_0",
        "return_lag_1",
        "return_lag_2",
        "return_lag_3",
        "return_lag_4",
        "return_lag_5",
        "log_close_open",
        "log_high_low",
        "sigma_24",
        "rsi_14",
        "macd_line_norm",
        "macd_signal_norm",
        "macd_hist_norm",
    ),
}


@dataclass(frozen=True)
class ExperimentSettings:
    name: str
    branch: str
    timezone: str
    seed: int


@dataclass(frozen=True)
class InputSettings:
    name: str
    path: Path
    sha256: str
    cutoff: datetime | None = None
    gate_status: str | None = None


@dataclass(frozen=True)
class LabelSettings:
    horizon_hours: int
    volatility_window: int
    threshold_multipliers: tuple[float, ...]
    class_order: tuple[str, ...]


@dataclass(frozen=True)
class FeatureSettings:
    warmup_bars: int
    k1: tuple[str, ...]
    k2: tuple[str, ...]


@dataclass(frozen=True)
class OuterFold:
    name: str
    test_start: datetime
    test_end: datetime


@dataclass(frozen=True)
class Phase4Protocol:
    experiment: ExperimentSettings
    inputs: dict[str, InputSettings]
    labels: LabelSettings
    features: FeatureSettings
    outer_folds: tuple[OuterFold, ...]
    inner_validation_months: int
    inner_block_months: int
    purge_bars: int
    models: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class MarketAudit:
    path: Path
    sha256: str
    row_count: int
    first_timestamp: pd.Timestamp | None
    last_timestamp: pd.Timestamp | None
    duplicate_timestamps: int
    non_monotonic_timestamps: int
    missing_values: int
    invalid_ohlc_rows: int


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"Timestamp must be UTC: {value}")
    return parsed.astimezone(UTC)


def _load_input(raw: dict[str, Any]) -> InputSettings:
    checksum = str(raw["sha256"])
    if len(checksum) != 64 or any(char not in "0123456789abcdef" for char in checksum):
        raise ValueError(f"Invalid SHA-256 for input {raw['name']}")
    return InputSettings(
        name=str(raw["name"]),
        path=Path(raw["path"]),
        sha256=checksum,
        cutoff=_parse_utc(raw["cutoff"]) if "cutoff" in raw else None,
        gate_status=raw.get("gate_status"),
    )


def load_protocol(path: str | Path) -> Phase4Protocol:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    experiment = ExperimentSettings(**raw["experiment"])
    labels = LabelSettings(
        horizon_hours=int(raw["labels"]["horizon_hours"]),
        volatility_window=int(raw["labels"]["volatility_window"]),
        threshold_multipliers=tuple(float(value) for value in raw["labels"]["threshold_multipliers"]),
        class_order=tuple(raw["labels"]["class_order"]),
    )
    features = FeatureSettings(
        warmup_bars=int(raw["features"]["warmup_bars"]),
        k1=tuple(raw["features"]["k1"]),
        k2=tuple(raw["features"]["k2"]),
    )
    evaluation = raw["evaluation"]
    folds = tuple(
        OuterFold(
            name=fold["name"],
            test_start=_parse_utc(fold["test_start"]),
            test_end=_parse_utc(fold["test_end"]),
        )
        for fold in evaluation["outer_folds"]
    )
    protocol = Phase4Protocol(
        experiment=experiment,
        inputs={name: _load_input(value) for name, value in raw["inputs"].items()},
        labels=labels,
        features=features,
        outer_folds=folds,
        inner_validation_months=int(evaluation["inner_validation_months"]),
        inner_block_months=int(evaluation["inner_block_months"]),
        purge_bars=int(evaluation["purge_bars"]),
        models=raw["models"],
    )
    _validate_frozen_contract(protocol)
    return protocol


def _validate_frozen_contract(protocol: Phase4Protocol) -> None:
    if protocol.experiment.branch != "research/phase-4-experiments":
        raise ValueError("Phase 4 branch differs from the frozen protocol")
    if protocol.experiment.timezone != "UTC" or protocol.experiment.seed != 42:
        raise ValueError("Timezone or seed differs from the frozen protocol")
    if (
        protocol.labels.horizon_hours != 1
        or protocol.labels.volatility_window != 24
        or protocol.labels.threshold_multipliers != (0.5, 0.25, 1.0)
        or protocol.labels.class_order != ("SELL", "HOLD", "BUY")
    ):
        raise ValueError("Label settings differ from the frozen protocol")
    if (
        protocol.features.warmup_bars != 50
        or protocol.features.k1 != EXPECTED_FEATURES["K1"]
        or protocol.features.k2 != EXPECTED_FEATURES["K2"]
    ):
        raise ValueError("Feature settings differ from the frozen protocol")
    if len(protocol.outer_folds) != 7:
        raise ValueError("Exactly seven outer folds are required")
    if protocol.inner_validation_months != 18 or protocol.inner_block_months != 6:
        raise ValueError("Inner validation must contain three six-month blocks")
    if protocol.purge_bars < protocol.labels.horizon_hours:
        raise ValueError("Purge must cover the label horizon")
    for previous, current in zip(protocol.outer_folds, protocol.outer_folds[1:]):
        if previous.test_end != current.test_start:
            raise ValueError("Outer folds must be contiguous")
    if any(fold.test_start >= fold.test_end for fold in protocol.outer_folds):
        raise ValueError("Every outer fold must have a positive duration")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_market_input(path: str | Path, expected_sha256: str) -> MarketAudit:
    market_path = Path(path)
    actual_sha256 = _sha256(market_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"SHA-256 mismatch for {market_path}: expected {expected_sha256}, got {actual_sha256}"
        )

    frame = pd.read_csv(market_path)
    missing_columns = sorted(set(REQUIRED_MARKET_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Missing market columns: {', '.join(missing_columns)}")

    times = pd.to_datetime(frame["time"], utc=True, errors="raise")
    numeric = frame.loc[:, ["open", "high", "low", "close"]].apply(
        pd.to_numeric, errors="coerce"
    )
    invalid_ohlc = (
        (numeric <= 0).any(axis=1)
        | (numeric["high"] < numeric[["open", "close", "low"]].max(axis=1))
        | (numeric["low"] > numeric[["open", "close", "high"]].min(axis=1))
    )
    return MarketAudit(
        path=market_path,
        sha256=actual_sha256,
        row_count=len(frame),
        first_timestamp=times.min() if len(times) else None,
        last_timestamp=times.max() if len(times) else None,
        duplicate_timestamps=int(times.duplicated().sum()),
        non_monotonic_timestamps=int((times.diff().dropna() <= pd.Timedelta(0)).sum()),
        missing_values=int(frame.loc[:, REQUIRED_MARKET_COLUMNS].isna().sum().sum()),
        invalid_ohlc_rows=int(invalid_ohlc.sum()),
    )
