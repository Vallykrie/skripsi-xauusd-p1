"""Conservative, schedule-aware auditing for gaps in hourly price bars."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import pairwise

import numpy as np
import pandas as pd

SchedulePredicate = Callable[[pd.Timestamp], bool]

_ONE_HOUR = pd.Timedelta(hours=1)


def _validate_utc_timestamp(value: object, name: str) -> pd.Timestamp:
    if not isinstance(value, pd.Timestamp):
        raise TypeError(f"{name} must be a pandas Timestamp, not a string")
    if pd.isna(value):
        raise ValueError(f"{name} must not be NaT")
    if value.tzinfo is None or str(value.tz) != "UTC":
        raise ValueError(f"{name} must be timezone-aware UTC")
    return value


def _validate_nonempty_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


@dataclass(frozen=True)
class KnownExceptionInterval:
    """Evidence-backed exception with half-open UTC bounds ``[start, end)``."""

    start: pd.Timestamp
    end: pd.Timestamp
    classification: str
    evidence_identifier: str
    normal_market_closure: bool

    def __post_init__(self) -> None:
        start = _validate_utc_timestamp(self.start, "exception start")
        end = _validate_utc_timestamp(self.end, "exception end")
        if start >= end:
            raise ValueError("exception interval must have positive duration")
        _validate_nonempty_text(self.classification, "exception classification")
        _validate_nonempty_text(
            self.evidence_identifier, "exception evidence identifier"
        )
        if not isinstance(self.normal_market_closure, (bool, np.bool_)):
            raise TypeError("normal_market_closure must be boolean")


@dataclass(frozen=True)
class GapInterval:
    """One open interval between consecutive source bars over one hour apart."""

    previous_bar_time: pd.Timestamp
    next_bar_time: pd.Timestamp
    missing_hourly_timestamps: int
    classification: str
    reset_state: bool
    evidence_identifier: str | None = None


@dataclass(frozen=True)
class GapAuditResult:
    """Gap records and arrays aligned one-to-one with the source rows.

    ``target_end_allowed`` is passed to the feature builder under the same name.
    A false value on the first row after any gap prevents the decision row before
    that gap from using the post-gap row as its target endpoint.
    """

    gaps: tuple[GapInterval, ...]
    segment_ids: np.ndarray
    target_end_allowed: np.ndarray


def _validate_source_times(times: pd.Series) -> None:
    if not isinstance(times, pd.Series):
        raise TypeError("times must be a pandas Series")
    if not isinstance(times.dtype, pd.DatetimeTZDtype) or str(times.dt.tz) != "UTC":
        raise ValueError("times must be a timezone-aware UTC datetime Series")
    if times.isna().any():
        raise ValueError("times must not contain NaT")
    if times.duplicated().any():
        raise ValueError("times must be unique")
    if not times.is_monotonic_increasing:
        raise ValueError("times must be strictly increasing")


def _validate_exceptions(
    known_exceptions: Sequence[KnownExceptionInterval],
) -> tuple[KnownExceptionInterval, ...]:
    exceptions = tuple(known_exceptions)
    for exception in exceptions:
        if not isinstance(exception, KnownExceptionInterval):
            raise TypeError("known exceptions must be KnownExceptionInterval records")
    for previous, current in pairwise(exceptions):
        if current.start < previous.start:
            raise ValueError("known exception intervals must be ordered by start")
        if current.start < previous.end:
            raise ValueError("known exception intervals must not overlap")
    return exceptions


def _scheduled_missing_times(
    missing_times: pd.DatetimeIndex,
    scheduled_to_trade: SchedulePredicate,
) -> tuple[pd.Timestamp, ...]:
    scheduled: list[pd.Timestamp] = []
    for timestamp in missing_times:
        result = scheduled_to_trade(timestamp)
        if not isinstance(result, (bool, np.bool_)):
            raise TypeError("schedule predicate must return a boolean")
        if result:
            scheduled.append(timestamp)
    return tuple(scheduled)


def _covering_exception(
    scheduled_times: tuple[pd.Timestamp, ...],
    exceptions: tuple[KnownExceptionInterval, ...],
) -> KnownExceptionInterval | None:
    for exception in exceptions:
        if all(exception.start <= time < exception.end for time in scheduled_times):
            return exception
    return None


def audit_price_gaps(
    times: pd.Series,
    scheduled_to_trade: SchedulePredicate,
    *,
    known_exceptions: Sequence[KnownExceptionInterval] = (),
) -> GapAuditResult:
    """Audit hourly gaps without embedding a broker-specific trading calendar."""
    _validate_source_times(times)
    if not callable(scheduled_to_trade):
        raise TypeError("scheduled_to_trade must be callable")
    exceptions = _validate_exceptions(known_exceptions)

    segment_ids = np.zeros(len(times), dtype=np.int64)
    target_end_allowed = np.ones(len(times), dtype=bool)
    gaps: list[GapInterval] = []
    current_segment = 0

    for position in range(1, len(times)):
        previous = times.iloc[position - 1]
        following = times.iloc[position]
        if following - previous <= _ONE_HOUR:
            segment_ids[position] = current_segment
            continue

        missing_times = pd.date_range(
            previous + _ONE_HOUR,
            following,
            freq=_ONE_HOUR,
            inclusive="left",
        )
        scheduled = _scheduled_missing_times(missing_times, scheduled_to_trade)
        evidence_identifier: str | None = None
        if not scheduled:
            classification = "scheduled_closure"
            reset_state = False
        else:
            exception = _covering_exception(scheduled, exceptions)
            if exception is None:
                classification = "unexplained_gap"
                reset_state = True
            else:
                classification = exception.classification
                evidence_identifier = exception.evidence_identifier
                reset_state = not bool(exception.normal_market_closure)

        target_end_allowed[position] = False
        if reset_state:
            current_segment += 1
        segment_ids[position] = current_segment
        gaps.append(
            GapInterval(
                previous_bar_time=previous,
                next_bar_time=following,
                missing_hourly_timestamps=len(missing_times),
                classification=classification,
                reset_state=reset_state,
                evidence_identifier=evidence_identifier,
            )
        )

    segment_ids.setflags(write=False)
    target_end_allowed.setflags(write=False)
    return GapAuditResult(
        gaps=tuple(gaps),
        segment_ids=segment_ids,
        target_end_allowed=target_end_allowed,
    )
