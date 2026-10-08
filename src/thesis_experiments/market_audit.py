"""Frozen, source-specific Phase 4 market gap audit orchestration."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import tomllib
import warnings
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from thesis_experiments.gaps import KnownExceptionInterval, audit_price_gaps
from thesis_experiments.protocol import REQUIRED_MARKET_COLUMNS

_SOURCE_INPUT_KEYS = ("primary", "sensitivity")
_SAFE_SOURCE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_EXPLICIT_UTC = re.compile(r"(?:Z|[+-]00:00)\Z", re.IGNORECASE)
_WINDOWS_RESERVED = re.compile(
    r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z", re.IGNORECASE
)
_GAPS_COLUMNS = (
    "previous_timestamp",
    "next_timestamp",
    "missing_hour_count",
    "classification",
    "reset_state",
    "evidence_identifier",
)
_ROW_POLICY_COLUMNS = (
    "row_index",
    "time",
    "segment_id",
    "target_end_allowed",
)


@dataclass(frozen=True)
class Evidence:
    identifier: str
    url: str
    description: str
    artifact_path: str | None = None
    artifact_sha256: str | None = None


@dataclass(frozen=True)
class SessionRegime:
    """One half-open source session regime selected by bar timestamp."""

    start: pd.Timestamp
    end: pd.Timestamp
    scheduled_weekdays: frozenset[int]
    scheduled_hours_utc: frozenset[int]
    provenance: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ExceptionEvent:
    event: str
    interval: KnownExceptionInterval


@dataclass(frozen=True)
class SourceGapPolicy:
    name: str
    provenance: tuple[str, ...]
    regular_closure_envelope: str
    session_regime_derivation: str
    session_regime_support_min_days: int
    session_regime_support_enforced: bool
    session_regimes: tuple[SessionRegime, ...]
    expected_rows: int
    expected_total_gaps: int
    expected_reset_gaps: int
    expected_segments: int
    expected_unexplained_gaps: int
    exception_events: tuple[ExceptionEvent, ...]

    @property
    def exceptions(self) -> tuple[KnownExceptionInterval, ...]:
        return tuple(event.interval for event in self.exception_events)


@dataclass(frozen=True)
class MarketGapPolicy:
    version: int
    evidence: Mapping[str, Evidence]
    sources: Mapping[str, SourceGapPolicy]


@dataclass(frozen=True)
class _Input:
    name: str
    configured_path: str
    path: Path
    sha256: str
    cutoff: pd.Timestamp | None


@dataclass(frozen=True)
class _PreparedAudit:
    source: str
    summary: dict[str, Any]
    gaps: pd.DataFrame
    row_policy: pd.DataFrame
    holiday_reset_row_policy: pd.DataFrame
    session_regime_support: pd.DataFrame


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_snapshot(path: Path, *, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Unable to read {label} {path}") from exc


def _parse_toml_snapshot(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        return tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"Invalid TOML in {label}") from exc


def _parse_utc(value: object, field: str) -> pd.Timestamp:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be an ISO-8601 UTC string")
    try:
        parsed = pd.Timestamp(datetime.fromisoformat(value))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 UTC string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed.to_pydatetime()):
        raise ValueError(f"{field} must be UTC")
    parsed = parsed.tz_convert("UTC")
    if parsed.minute or parsed.second or parsed.microsecond or parsed.nanosecond:
        raise ValueError(f"{field} must be aligned to an exact hour")
    return parsed


def _validate_sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"Invalid SHA-256 for {field}")
    return value


def _validate_source_name(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not _SAFE_SOURCE_NAME.fullmatch(value)
        or value.endswith((".", " "))
        or _WINDOWS_RESERVED.fullmatch(value)
    ):
        raise ValueError(f"Invalid source name in {field}; a safe basename is required")
    return value


def _validate_ultima_session_artifact(snapshot: bytes, identifier: str) -> None:
    try:
        frame = pd.read_csv(io.BytesIO(snapshot), keep_default_na=False)
    except Exception as exc:
        raise ValueError(f"Evidence artifact {identifier} is not a valid session CSV") from exc
    required = {
        "record_type",
        "requested_symbol",
        "resolved_symbol",
        "server_name",
        "extracted_at_trade_server",
        "extracted_at_gmt",
        "trade_server_minus_gmt_seconds",
        "day_code",
        "session_index",
        "from_seconds_since_midnight",
        "to_seconds_since_midnight",
    }
    if not required.issubset(frame.columns):
        raise ValueError(f"Evidence artifact {identifier} has missing session fields")
    context = frame.loc[frame["record_type"] == "context"]
    if len(context) != 1:
        raise ValueError(f"Evidence artifact {identifier} requires one context row")
    row = context.iloc[0]
    if (
        row["requested_symbol"] != "XAUUSD"
        or row["resolved_symbol"] != "XAUUSD"
        or row["server_name"] != "UltimaMarkets-Demo"
        or str(row["trade_server_minus_gmt_seconds"]) != "0"
        or not str(row["extracted_at_trade_server"]).startswith("2026.09.14T")
        or not str(row["extracted_at_gmt"]).startswith("2026.09.14T")
    ):
        raise ValueError(f"Evidence artifact {identifier} context does not match policy")
    quotes = frame.loc[frame["record_type"] == "quote_session"].copy()
    expected = {1: 86280, 2: 86280, 3: 86280, 4: 86280, 5: 86220}
    try:
        actual = {
            int(item.day_code): (
                int(item.session_index),
                int(item.from_seconds_since_midnight),
                int(item.to_seconds_since_midnight),
            )
            for item in quotes.itertuples()
        }
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Evidence artifact {identifier} has invalid session values") from exc
    if actual != {day: (0, 3600, end) for day, end in expected.items()}:
        raise ValueError(f"Evidence artifact {identifier} quote sessions do not match policy")


def _validated_int_set(
    raw: object,
    *,
    field: str,
    minimum: int,
    maximum: int,
) -> frozenset[int]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"Invalid schedule field {field}")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in raw):
        raise ValueError(f"Invalid schedule field {field}")
    values = frozenset(raw)
    if len(values) != len(raw) or any(value < minimum or value > maximum for value in values):
        raise ValueError(f"Invalid schedule field {field}")
    return values


def _validate_evidence(identifier: str, raw: object) -> Evidence:
    if not isinstance(raw, dict):
        raise TypeError(f"Evidence {identifier} must be a table")
    allowed = {"url", "description", "artifact_path", "artifact_sha256"}
    if not set(raw).issubset(allowed):
        raise ValueError(f"Evidence {identifier} is malformed")
    url = raw.get("url")
    description = raw.get("description")
    if not isinstance(url, str) or not isinstance(description, str) or not description.strip():
        raise ValueError(f"Evidence {identifier} is malformed")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or host == "example.com" or "google." in host:
        raise ValueError(f"Evidence {identifier} must use a direct official HTTPS URL")
    if "/search" in parsed.path.lower() or parsed.query.lower().startswith("q="):
        raise ValueError(f"Evidence {identifier} must not use a search-result URL")
    artifact_path = raw.get("artifact_path")
    artifact_sha256 = raw.get("artifact_sha256")
    if (artifact_path is None) != (artifact_sha256 is None):
        raise ValueError(f"Evidence {identifier} artifact path and SHA-256 must be paired")
    if artifact_path is not None:
        if not isinstance(artifact_path, str) or not artifact_path:
            raise ValueError(f"Evidence {identifier} has an invalid evidence artifact path")
        artifact_sha256 = _validate_sha256(
            artifact_sha256, f"evidence artifact {identifier}"
        )
        artifact = Path(artifact_path)
        artifact_snapshot = _read_snapshot(artifact, label="evidence artifact")
        actual = _digest(artifact_snapshot)
        if actual != artifact_sha256:
            raise ValueError(
                f"SHA-256 mismatch for evidence artifact {artifact}: "
                f"expected {artifact_sha256}, got {actual}"
            )
        if identifier == "ultima-extracted-session-envelope":
            _validate_ultima_session_artifact(artifact_snapshot, identifier)
    return Evidence(
        identifier=identifier,
        url=url,
        description=description.strip(),
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
    )


def _load_exception(
    raw: object,
    *,
    source: str,
    evidence: Mapping[str, Evidence],
) -> ExceptionEvent:
    if not isinstance(raw, dict):
        raise TypeError(f"Exception for {source} must be a table")
    required = {
        "start",
        "end",
        "event",
        "classification",
        "evidence_identifier",
        "normal_market_closure",
    }
    if set(raw) != required:
        raise ValueError(f"Exception for {source} has malformed fields")
    evidence_identifier = raw["evidence_identifier"]
    event = raw["event"]
    if not isinstance(event, str) or not event.strip():
        raise ValueError(f"Exception for {source} requires an event")
    if evidence_identifier not in evidence:
        raise ValueError(f"Exception for {source} references unknown evidence")
    interval = KnownExceptionInterval(
        start=_parse_utc(raw["start"], "exception start"),
        end=_parse_utc(raw["end"], "exception end"),
        classification=str(raw["classification"]),
        evidence_identifier=str(evidence_identifier),
        normal_market_closure=raw["normal_market_closure"],
    )
    if interval.normal_market_closure and interval.classification != "exchange_aligned_observed_closure":
        raise ValueError("Normal market closures must use exchange_aligned_observed_closure")
    if not interval.normal_market_closure and interval.classification != "documented_exchange_outage":
        raise ValueError("Non-normal exceptions must use documented_exchange_outage")
    return ExceptionEvent(event=event.strip(), interval=interval)


def _load_regime(
    raw: object,
    *,
    source: str,
    evidence: Mapping[str, Evidence],
) -> SessionRegime:
    if not isinstance(raw, dict):
        raise TypeError(f"Session regime for {source} must be a table")
    required = {
        "start",
        "end",
        "scheduled_weekdays",
        "scheduled_hours_utc",
        "provenance",
        "description",
    }
    if set(raw) != required:
        raise ValueError(f"Session regime for {source} has malformed fields")
    start = _parse_utc(raw["start"], "session regime start")
    end = _parse_utc(raw["end"], "session regime end")
    if start >= end:
        raise ValueError(f"Session regime for {source} has a reversed range")
    provenance_raw = raw["provenance"]
    if not isinstance(provenance_raw, list) or not provenance_raw:
        raise ValueError(f"Session regime for {source} requires provenance")
    provenance = tuple(str(value) for value in provenance_raw)
    if len(set(provenance)) != len(provenance) or any(
        value not in evidence for value in provenance
    ):
        raise ValueError(f"Session regime for {source} has invalid provenance")
    description = raw["description"]
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"Session regime for {source} requires a description")
    return SessionRegime(
        start=start,
        end=end,
        scheduled_weekdays=_validated_int_set(
            raw["scheduled_weekdays"],
            field="scheduled_weekdays",
            minimum=0,
            maximum=4,
        ),
        scheduled_hours_utc=_validated_int_set(
            raw["scheduled_hours_utc"],
            field="scheduled_hours_utc",
            minimum=0,
            maximum=23,
        ),
        provenance=provenance,
        description=description.strip(),
    )


def _load_source_policy(
    name: str,
    raw: object,
    evidence: Mapping[str, Evidence],
) -> SourceGapPolicy:
    _validate_source_name(name, "policy source")
    if not isinstance(raw, dict):
        raise TypeError(f"Source policy {name} must be a table")
    allowed_fields = {
        "provenance",
        "regular_closure_envelope",
        "session_regime_derivation",
        "session_regime_support_min_days",
        "session_regime_support_enforced",
        "expected_rows",
        "expected_total_gaps",
        "expected_reset_gaps",
        "expected_segments",
        "expected_unexplained_gaps",
        "session_regimes",
        "exceptions",
    }
    if not set(raw).issubset(allowed_fields):
        raise ValueError(f"Source policy {name} has unknown fields")
    provenance_raw = raw.get("provenance")
    envelope = raw.get("regular_closure_envelope")
    derivation = raw.get("session_regime_derivation")
    support_min_days = raw.get("session_regime_support_min_days")
    support_enforced = raw.get("session_regime_support_enforced")
    if not isinstance(provenance_raw, list) or not provenance_raw:
        raise ValueError(f"Source policy {name} requires provenance")
    if not isinstance(envelope, str) or not envelope.strip():
        raise ValueError(f"Source policy {name} requires a regular closure envelope")
    if not isinstance(derivation, str) or not derivation.strip():
        raise ValueError(f"Source policy {name} requires a regime derivation rule")
    if (
        isinstance(support_min_days, bool)
        or not isinstance(support_min_days, int)
        or support_min_days < 2
    ):
        raise ValueError(f"Source policy {name} requires recurrence support")
    if not isinstance(support_enforced, bool):
        raise TypeError(f"Source policy {name} requires support enforcement mode")
    provenance = tuple(str(value) for value in provenance_raw)
    if len(set(provenance)) != len(provenance) or any(
        value not in evidence for value in provenance
    ):
        raise ValueError(f"Source policy {name} has invalid provenance")
    regimes = tuple(
        _load_regime(item, source=name, evidence=evidence)
        for item in raw.get("session_regimes", [])
    )
    if not regimes:
        raise ValueError(f"Source policy {name} requires session regimes")
    for previous, current in pairwise(regimes):
        if current.start < previous.end:
            raise ValueError(f"Session regimes for {name} overlap")
        if current.start > previous.end:
            raise ValueError(f"Session regimes for {name} have a gap")
    exception_events = tuple(
        _load_exception(item, source=name, evidence=evidence)
        for item in raw.get("exceptions", [])
    )
    for previous, current in pairwise(exception_events):
        if current.interval.start < previous.interval.start:
            raise ValueError(f"Exception intervals for {name} must be ordered")
        if current.interval.start < previous.interval.end:
            raise ValueError(f"Exception intervals for {name} overlap")
    expected_fields = (
        "expected_rows",
        "expected_total_gaps",
        "expected_reset_gaps",
        "expected_segments",
        "expected_unexplained_gaps",
    )
    expected = {field: raw.get(field) for field in expected_fields}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in expected.values()
    ):
        raise ValueError(f"Source policy {name} has invalid expected empirical counts")
    rows = expected["expected_rows"]
    segments = expected["expected_segments"]
    if (rows == 0 and segments != 0) or (rows > 0 and segments < 1):
        raise ValueError(f"Source policy {name} has inconsistent expected segments")
    return SourceGapPolicy(
        name=name,
        provenance=provenance,
        regular_closure_envelope=envelope.strip(),
        session_regime_derivation=derivation.strip(),
        session_regime_support_min_days=support_min_days,
        session_regime_support_enforced=support_enforced,
        session_regimes=regimes,
        expected_rows=rows,
        expected_total_gaps=expected["expected_total_gaps"],
        expected_reset_gaps=expected["expected_reset_gaps"],
        expected_segments=segments,
        expected_unexplained_gaps=expected["expected_unexplained_gaps"],
        exception_events=exception_events,
    )


def _load_policy_snapshot(data: bytes) -> MarketGapPolicy:
    raw = _parse_toml_snapshot(data, label="market gap policy")
    if set(raw) != {"version", "evidence", "sources"}:
        raise ValueError("Market gap policy has unknown or missing top-level fields")
    if raw.get("version") != 2:
        raise ValueError("Market gap policy version must be 2")
    evidence_raw = raw.get("evidence")
    sources_raw = raw.get("sources")
    if not isinstance(evidence_raw, dict) or not evidence_raw:
        raise ValueError("Market gap policy requires evidence")
    if not isinstance(sources_raw, dict) or not sources_raw:
        raise ValueError("Market gap policy requires sources")
    evidence = {
        identifier: _validate_evidence(identifier, value)
        for identifier, value in sorted(evidence_raw.items())
    }
    sources = {
        name: _load_source_policy(name, value, evidence)
        for name, value in sorted(sources_raw.items())
    }
    if len({name.casefold() for name in sources}) != len(sources):
        raise ValueError("Market policy source names collide")
    return MarketGapPolicy(version=2, evidence=evidence, sources=sources)


def load_market_gap_policy(path: str | Path) -> MarketGapPolicy:
    """Load and strictly validate the frozen source-specific TOML policy."""
    policy_path = Path(path)
    return _load_policy_snapshot(_read_snapshot(policy_path, label="policy config"))


def _load_inputs_snapshot(data: bytes) -> tuple[_Input, ...]:
    raw = _parse_toml_snapshot(data, label="experiment config")
    allowed_top_level = {"experiment", "inputs", "labels", "features", "evaluation", "models"}
    if not set(raw).issubset(allowed_top_level) or "inputs" not in raw:
        raise ValueError("Experiment config has unknown or missing top-level fields")
    raw_inputs = raw.get("inputs")
    if not isinstance(raw_inputs, dict):
        raise TypeError("Experiment config requires inputs")
    inputs: list[_Input] = []
    for key in _SOURCE_INPUT_KEYS:
        item = raw_inputs.get(key)
        if not isinstance(item, dict):
            raise TypeError(f"Experiment config requires inputs.{key}")
        required_fields = {"name", "path", "sha256"}
        allowed_fields = required_fields | {"cutoff"}
        if not required_fields.issubset(item) or not set(item).issubset(allowed_fields):
            raise ValueError(f"Experiment config inputs.{key} has unknown or missing fields")
        if key == "sensitivity" and "cutoff" not in item:
            raise ValueError("Experiment config inputs.sensitivity requires cutoff")
        name = _validate_source_name(item.get("name"), f"inputs.{key}")
        configured_path = item.get("path")
        if not isinstance(configured_path, str) or not configured_path:
            raise ValueError(f"Invalid input path for {name}")
        checksum = _validate_sha256(item.get("sha256"), name)
        cutoff = _parse_utc(item["cutoff"], "input cutoff") if "cutoff" in item else None
        inputs.append(
            _Input(
                name=name,
                configured_path=configured_path,
                path=Path(configured_path),
                sha256=checksum,
                cutoff=cutoff,
            )
        )
    if len({item.name.casefold() for item in inputs}) != len(inputs):
        raise ValueError("Market input source names must be unique without collisions")
    return tuple(inputs)


def _isoformat(timestamp: pd.Timestamp | None) -> str | None:
    if timestamp is None or pd.isna(timestamp):
        return None
    return timestamp.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_session_regime(
    policy: SourceGapPolicy, timestamp: pd.Timestamp
) -> SessionRegime:
    """Return the unique half-open session regime covering ``timestamp``."""
    if not isinstance(timestamp, pd.Timestamp) or timestamp.tzinfo is None:
        raise ValueError("Session timestamp must be timezone-aware")
    normalized = timestamp.tz_convert("UTC")
    for regime in policy.session_regimes:
        if regime.start <= normalized < regime.end:
            return regime
    raise ValueError(
        f"{policy.name} audit timestamp {_isoformat(normalized)} is not covered "
        "by a session regime"
    )


def _schedule(policy: SourceGapPolicy) -> Callable[[pd.Timestamp], bool]:
    def scheduled(timestamp: pd.Timestamp) -> bool:
        regime = resolve_session_regime(policy, timestamp)
        return (
            timestamp.dayofweek in regime.scheduled_weekdays
            and timestamp.hour in regime.scheduled_hours_utc
        )

    return scheduled


def _validate_measured_counts(policy: SourceGapPolicy, measured: Mapping[str, int]) -> None:
    expected = {
        "expected_rows": policy.expected_rows,
        "expected_total_gaps": policy.expected_total_gaps,
        "expected_reset_gaps": policy.expected_reset_gaps,
        "expected_segments": policy.expected_segments,
        "expected_unexplained_gaps": policy.expected_unexplained_gaps,
    }
    for field, expected_value in expected.items():
        if measured[field] != expected_value:
            raise ValueError(
                f"{policy.name} {field} mismatch: expected {expected_value}, "
                f"measured {measured[field]}"
            )


def _parse_market_snapshot(item: _Input) -> tuple[pd.DataFrame, pd.Series]:
    snapshot = _read_snapshot(item.path, label="market input")
    actual_sha256 = _digest(snapshot)
    if actual_sha256 != item.sha256:
        raise ValueError(
            f"SHA-256 mismatch for {item.path}: expected {item.sha256}, got {actual_sha256}"
        )
    frame = pd.read_csv(io.BytesIO(snapshot))
    missing = sorted(set(REQUIRED_MARKET_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing market columns: {', '.join(missing)}")
    raw_times = frame["time"]
    if raw_times.isna().any() or not raw_times.map(
        lambda value: isinstance(value, str) and bool(_EXPLICIT_UTC.search(value))
    ).all():
        raise ValueError("Every raw market timestamp must use an explicit zero UTC offset")
    times = pd.to_datetime(raw_times, utc=True, errors="raise")
    if (
        (times.dt.minute != 0)
        | (times.dt.second != 0)
        | (times.dt.microsecond != 0)
        | (times.dt.nanosecond != 0)
    ).any():
        raise ValueError("Every market timestamp must be aligned to an exact hour")
    numeric = frame.loc[:, ["open", "high", "low", "close"]].apply(
        pd.to_numeric, errors="coerce"
    )
    invalid_ohlc = (
        (numeric <= 0).any(axis=1)
        | (numeric["high"] < numeric[["open", "close", "low"]].max(axis=1))
        | (numeric["low"] > numeric[["open", "close", "high"]].min(axis=1))
    )
    quality = {
        "duplicate_timestamps": int(times.duplicated().sum()),
        "non_monotonic_timestamps": int(
            (times.diff().dropna() <= pd.Timedelta(0)).sum()
        ),
        "missing_values": int(
            frame.loc[:, REQUIRED_MARKET_COLUMNS].isna().sum().sum()
        ),
        "invalid_ohlc_rows": int(invalid_ohlc.sum()),
    }
    if any(quality.values()):
        raise ValueError(f"{item.name} failed the basic market audit: {quality}")
    return frame, times


def _regime_metadata(regime: SessionRegime) -> dict[str, Any]:
    return {
        "start": _isoformat(regime.start),
        "end": _isoformat(regime.end),
        "scheduled_weekdays": sorted(regime.scheduled_weekdays),
        "scheduled_hours_utc": sorted(regime.scheduled_hours_utc),
        "provenance": list(regime.provenance),
        "description": regime.description,
    }


def _evidence_metadata(evidence: Evidence) -> dict[str, Any]:
    result: dict[str, Any] = {
        "identifier": evidence.identifier,
        "url": evidence.url,
        "description": evidence.description,
    }
    if evidence.artifact_path is not None:
        result["artifact"] = {
            "path": evidence.artifact_path,
            "sha256": evidence.artifact_sha256,
        }
    return result


def _exception_metadata(event: ExceptionEvent) -> dict[str, Any]:
    interval = event.interval
    return {
        "start": _isoformat(interval.start),
        "end": _isoformat(interval.end),
        "event": event.event,
        "classification": interval.classification,
        "evidence_identifier": interval.evidence_identifier,
        "normal_market_closure": bool(interval.normal_market_closure),
    }


def _session_regime_support(
    policy: SourceGapPolicy, times: pd.Series
) -> pd.DataFrame:
    columns = (
        "date",
        "weekday",
        "row_count",
        "hour_00_observed",
        "hour_23_observed",
        "eligible",
        "regime_start",
        "regime_end",
        "scheduled_hours_utc",
        "conforms",
    )
    if times.empty:
        return pd.DataFrame(columns=columns)
    daily = pd.DataFrame({"time": times.to_numpy()})
    daily["date"] = daily["time"].dt.floor("D")
    records: list[dict[str, Any]] = []
    for date, group in daily.groupby("date", sort=True):
        regime = resolve_session_regime(policy, date)
        hours = frozenset(int(value) for value in group["time"].dt.hour)
        eligible = bool(date.dayofweek < 5 and len(group) >= 20)
        conforms = bool(
            eligible
            and ((0 in hours) == (0 in regime.scheduled_hours_utc))
            and ((23 in hours) == (23 in regime.scheduled_hours_utc))
        )
        records.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "weekday": int(date.dayofweek),
                "row_count": len(group),
                "hour_00_observed": 0 in hours,
                "hour_23_observed": 23 in hours,
                "eligible": eligible,
                "regime_start": _isoformat(regime.start),
                "regime_end": _isoformat(regime.end),
                "scheduled_hours_utc": ",".join(
                    str(value) for value in sorted(regime.scheduled_hours_utc)
                ),
                "conforms": conforms,
            }
        )
    support = pd.DataFrame(records, columns=columns)
    for regime in policy.session_regimes:
        if not policy.session_regime_support_enforced:
            break
        selected = support.loc[
            (support["regime_start"] == _isoformat(regime.start))
            & support["eligible"]
        ]
        if len(selected) < policy.session_regime_support_min_days:
            continue
        dates = pd.to_datetime(selected.loc[selected["conforms"], "date"])
        longest = current = 0
        previous: pd.Timestamp | None = None
        for date in dates:
            if previous is not None and date == previous + pd.offsets.BDay(1):
                current += 1
            else:
                current = 1
            longest = max(longest, current)
            previous = date
        if longest < policy.session_regime_support_min_days:
            raise ValueError(
                f"{policy.name} regime {_isoformat(regime.start)} lacks "
                f"{policy.session_regime_support_min_days} consecutive support days"
            )
    return support


def _holiday_reset_policy(
    frame: pd.DataFrame,
    times: pd.Series,
    audited_gaps: Any,
) -> tuple[pd.DataFrame, int, int]:
    segment_ids = np.zeros(len(frame), dtype=np.int64)
    current_segment = 0
    gap_position = 0
    for position in range(1, len(times)):
        if times.iloc[position] - times.iloc[position - 1] > pd.Timedelta(hours=1):
            gap = audited_gaps.gaps[gap_position]
            gap_position += 1
            if gap.reset_state or gap.classification == "exchange_aligned_observed_closure":
                current_segment += 1
        segment_ids[position] = current_segment
    row_policy = pd.DataFrame(
        {
            "row_index": frame.index.to_numpy(dtype=np.int64),
            "time": times.to_numpy(),
            "segment_id": segment_ids,
            "target_end_allowed": audited_gaps.target_end_allowed,
        },
        columns=_ROW_POLICY_COLUMNS,
    )
    row_policy["time"] = pd.to_datetime(row_policy["time"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    return row_policy, current_segment, current_segment + 1 if len(frame) else 0


def _prepare_input(
    item: _Input,
    policy: SourceGapPolicy,
    evidence: Mapping[str, Evidence],
    *,
    experiment_config: Path,
    experiment_sha256: str,
    policy_config: Path,
    policy_sha256: str,
    policy_version: int,
) -> _PreparedAudit:
    frame, times = _parse_market_snapshot(item)
    if item.cutoff is not None:
        keep = times >= item.cutoff
        frame = frame.loc[keep]
        times = times.loc[keep]
    if len(times):
        resolve_session_regime(policy, times.iloc[0])
        resolve_session_regime(policy, times.iloc[-1])
    gaps = audit_price_gaps(
        times.reset_index(drop=True),
        _schedule(policy),
        known_exceptions=policy.exceptions,
    )
    class_counts = dict(
        sorted(Counter(gap.classification for gap in gaps.gaps).items())
    )
    reset_count = sum(gap.reset_state for gap in gaps.gaps)
    segment_count = int(gaps.segment_ids[-1] + 1) if len(frame) else 0
    measured = {
        "expected_rows": len(frame),
        "expected_total_gaps": len(gaps.gaps),
        "expected_reset_gaps": reset_count,
        "expected_segments": segment_count,
        "expected_unexplained_gaps": class_counts.get("unexplained_gap", 0),
    }
    _validate_measured_counts(policy, measured)
    gap_frame = pd.DataFrame(
        [
            {
                "previous_timestamp": _isoformat(gap.previous_bar_time),
                "next_timestamp": _isoformat(gap.next_bar_time),
                "missing_hour_count": gap.missing_hourly_timestamps,
                "classification": gap.classification,
                "reset_state": gap.reset_state,
                "evidence_identifier": gap.evidence_identifier or "",
            }
            for gap in gaps.gaps
        ],
        columns=_GAPS_COLUMNS,
    )
    row_policy = pd.DataFrame(
        {
            "row_index": frame.index.to_numpy(dtype=np.int64),
            "time": times.to_numpy(),
            "segment_id": gaps.segment_ids,
            "target_end_allowed": gaps.target_end_allowed,
        },
        columns=_ROW_POLICY_COLUMNS,
    )
    row_policy["time"] = pd.to_datetime(row_policy["time"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    holiday_reset_rows, holiday_reset_count, holiday_reset_segments = (
        _holiday_reset_policy(frame, times.reset_index(drop=True), gaps)
    )
    regime_support = _session_regime_support(policy, times.reset_index(drop=True))
    selected_evidence = sorted(
        set(policy.provenance)
        | {identifier for regime in policy.session_regimes for identifier in regime.provenance}
        | {
            event.interval.evidence_identifier
            for event in policy.exception_events
        }
    )
    summary: dict[str, Any] = {
        "source": item.name,
        "input": {"path": item.configured_path, "sha256": item.sha256},
        "configs": {
            "experiment": {
                "path": str(experiment_config),
                "sha256": experiment_sha256,
            },
            "policy": {"path": str(policy_config), "sha256": policy_sha256},
        },
        "cutoff": _isoformat(item.cutoff),
        "rows": {
            "count": len(frame),
            "first_timestamp": _isoformat(times.iloc[0]) if len(times) else None,
            "last_timestamp": _isoformat(times.iloc[-1]) if len(times) else None,
        },
        "gap_count": len(gaps.gaps),
        "class_counts": class_counts,
        "reset_gap_count": reset_count,
        "segment_count": segment_count,
        "policy": {
            "version": policy_version,
            "digest": policy_sha256,
            "regular_closure_envelope": policy.regular_closure_envelope,
            "session_regime_derivation": policy.session_regime_derivation,
            "session_regime_support_min_days": policy.session_regime_support_min_days,
            "session_regime_support_enforced": policy.session_regime_support_enforced,
            "session_regimes": [
                _regime_metadata(regime) for regime in policy.session_regimes
            ],
            "evidence": [
                _evidence_metadata(evidence[identifier])
                for identifier in selected_evidence
            ],
            "exceptions": [
                _exception_metadata(event) for event in policy.exception_events
            ],
        },
        "sensitivities": {
            "exchange_aligned_closures_reset": {
                "reset_gap_count": holiday_reset_count,
                "segment_count": holiday_reset_segments,
                "description": (
                    "Conservative policy: exchange-aligned observed closures reset "
                    "state because exchange calendars are not broker-session proof."
                ),
            }
        },
    }
    return _PreparedAudit(
        item.name,
        summary,
        gap_frame,
        row_policy,
        holiday_reset_rows,
        regime_support,
    )


def _sha256(path: Path) -> str:
    return _digest(path.read_bytes())


def _write_generation(
    prepared: tuple[_PreparedAudit, ...], stage: Path
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for audit in prepared:
        source_dir = stage / audit.source
        source_dir.mkdir()
        gaps_path = source_dir / "gaps.csv"
        rows_path = source_dir / "row_policy.parquet"
        sensitivity_path = source_dir / "row_policy_holiday_reset_sensitivity.parquet"
        support_path = source_dir / "session_regime_support.csv"
        audit.gaps.to_csv(gaps_path, index=False, lineterminator="\n")
        audit.row_policy.to_parquet(rows_path, index=False, engine="pyarrow")
        audit.holiday_reset_row_policy.to_parquet(
            sensitivity_path, index=False, engine="pyarrow"
        )
        audit.session_regime_support.to_csv(
            support_path, index=False, lineterminator="\n"
        )
        summary = dict(audit.summary)
        summary["artifacts"] = {
            "gaps.csv": _sha256(gaps_path),
            "row_policy.parquet": _sha256(rows_path),
            "row_policy_holiday_reset_sensitivity.parquet": _sha256(
                sensitivity_path
            ),
            "session_regime_support.csv": _sha256(support_path),
        }
        (source_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        summaries[audit.source] = summary
    return summaries


def _publish_generation(stage: Path, output_dir: Path) -> None:
    parent = output_dir.parent
    backup: Path | None = None
    if output_dir.exists():
        backup = Path(tempfile.mkdtemp(prefix=".price-audit-backup-", dir=parent))
        backup.rmdir()
        os.replace(output_dir, backup)
    try:
        os.replace(stage, output_dir)
    except OSError:
        if backup is not None and backup.exists():
            try:
                os.replace(backup, output_dir)
            except OSError as restore_error:
                raise RuntimeError(
                    "Publication failed and automatic restore also failed; "
                    f"the previous generation is preserved at {backup}"
                ) from restore_error
        raise
    if backup is not None:
        try:
            shutil.rmtree(backup)
        except OSError as exc:
            warnings.warn(
                "New audit generation is committed, but the previous generation "
                f"could not be removed and remains at {backup}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )


def _acquire_publication_lock(output_dir: Path) -> Path:
    lock = output_dir.parent / f".{output_dir.name}.audit.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(f"Audit output is locked by another run: {lock}") from exc
    return lock


def _write_prepared(
    prepared: tuple[_PreparedAudit, ...], output_dir: Path
) -> dict[str, dict[str, Any]]:
    output_parent = output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    lock = _acquire_publication_lock(output_dir)
    stage: Path | None = None
    try:
        stage = Path(tempfile.mkdtemp(prefix=".price-audit-stage-", dir=output_parent))
        summaries = _write_generation(prepared, stage)
        _publish_generation(stage, output_dir)
        return summaries
    except OSError as exc:
        if stage is not None and stage.exists():
            shutil.rmtree(stage)
        raise RuntimeError(
            f"Unable to publish deterministic audit output to {output_dir}"
        ) from exc
    except Exception:
        if stage is not None and stage.exists():
            shutil.rmtree(stage)
        raise
    finally:
        try:
            lock.rmdir()
        except OSError as exc:
            warnings.warn(
                f"Audit publication lock requires manual cleanup at {lock}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )


def _resolved(path: Path) -> Path:
    try:
        return path.resolve(strict=False)
    except OSError as exc:
        raise ValueError(f"Unable to resolve protected path {path}") from exc


def _validate_output_is_separate(
    output_dir: Path,
    *,
    experiment_path: Path,
    policy_path: Path,
    inputs: tuple[_Input, ...],
    evidence: Mapping[str, Evidence],
) -> None:
    output = _resolved(output_dir)
    protected = [_resolved(experiment_path), _resolved(policy_path)]
    protected.extend(_resolved(item.path) for item in inputs)
    protected.extend(
        _resolved(Path(item.artifact_path))
        for item in evidence.values()
        if item.artifact_path is not None
    )
    for path in protected:
        if output == path or output in path.parents or path in output.parents:
            raise ValueError(
                f"Output path {output} overlaps protected input or evidence path {path}"
            )


def run_market_audits(
    experiment_config: str | Path,
    policy_config: str | Path,
    output_dir: str | Path,
) -> dict[str, dict[str, Any]]:
    """Verify, audit, validate frozen counts, and publish deterministic artifacts."""
    experiment_path = Path(experiment_config)
    policy_path = Path(policy_config)
    experiment_snapshot = _read_snapshot(experiment_path, label="experiment config")
    policy_snapshot = _read_snapshot(policy_path, label="policy config")
    inputs = _load_inputs_snapshot(experiment_snapshot)
    policy = _load_policy_snapshot(policy_snapshot)
    unknown = sorted(item.name for item in inputs if item.name not in policy.sources)
    if unknown:
        raise ValueError(f"Unknown source in experiment config: {', '.join(unknown)}")
    output_path = Path(output_dir)
    _validate_output_is_separate(
        output_path,
        experiment_path=experiment_path,
        policy_path=policy_path,
        inputs=inputs,
        evidence=policy.evidence,
    )
    experiment_sha256 = _digest(experiment_snapshot)
    policy_sha256 = _digest(policy_snapshot)
    prepared = tuple(
        _prepare_input(
            item,
            policy.sources[item.name],
            policy.evidence,
            experiment_config=experiment_path,
            experiment_sha256=experiment_sha256,
            policy_config=policy_path,
            policy_sha256=policy_sha256,
            policy_version=policy.version,
        )
        for item in inputs
    )
    return _write_prepared(prepared, output_path)
