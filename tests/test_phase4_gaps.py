from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from thesis_experiments.gaps import (
    GapAuditResult,
    GapInterval,
    KnownExceptionInterval,
    audit_price_gaps,
)


def _times(*values: str) -> pd.Series:
    return pd.Series(pd.to_datetime(list(values), utc=True))


def _always_trading(_: pd.Timestamp) -> bool:
    return True


def test_weekend_and_daily_scheduled_closures_continue_indicator_state():
    times = _times(
        "2026-01-02T21:00:00Z",
        "2026-01-04T23:00:00Z",
        "2026-01-05T00:00:00Z",
        "2026-01-05T01:00:00Z",
        "2026-01-05T03:00:00Z",
    )

    def scheduled_to_trade(timestamp: pd.Timestamp) -> bool:
        return not (
            timestamp.dayofweek >= 5
            or (timestamp.dayofweek == 4 and timestamp.hour >= 22)
            or (timestamp.hour == 2 and timestamp.dayofweek < 5)
        )

    result = audit_price_gaps(times, scheduled_to_trade)

    assert [gap.classification for gap in result.gaps] == [
        "scheduled_closure",
        "scheduled_closure",
    ]
    assert [gap.missing_hourly_timestamps for gap in result.gaps] == [49, 1]
    assert not any(gap.reset_state for gap in result.gaps)
    np.testing.assert_array_equal(result.segment_ids, [0, 0, 0, 0, 0])


def test_unexplained_intraday_gap_resets_on_following_row():
    times = _times(
        "2026-01-05T09:00:00Z",
        "2026-01-05T10:00:00Z",
        "2026-01-05T13:00:00Z",
        "2026-01-05T14:00:00Z",
    )

    result = audit_price_gaps(times, _always_trading)

    assert result.gaps == (
        GapInterval(
            previous_bar_time=pd.Timestamp("2026-01-05T10:00:00Z"),
            next_bar_time=pd.Timestamp("2026-01-05T13:00:00Z"),
            missing_hourly_timestamps=2,
            classification="unexplained_gap",
            reset_state=True,
            evidence_identifier=None,
        ),
    )
    np.testing.assert_array_equal(result.segment_ids, [0, 0, 1, 1])
    assert result.segment_ids.dtype == np.dtype("int64")


def test_official_provider_outage_is_explained_but_resets_state():
    times = _times("2026-01-05T09:00:00Z", "2026-01-05T13:00:00Z")
    outage = KnownExceptionInterval(
        start=pd.Timestamp("2026-01-05T10:00:00Z"),
        end=pd.Timestamp("2026-01-05T13:00:00Z"),
        classification="provider_outage",
        evidence_identifier="provider-status-2026-01-05",
        normal_market_closure=False,
    )

    result = audit_price_gaps(times, _always_trading, known_exceptions=[outage])

    assert result.gaps[0].classification == "provider_outage"
    assert result.gaps[0].evidence_identifier == "provider-status-2026-01-05"
    assert result.gaps[0].reset_state
    np.testing.assert_array_equal(result.segment_ids, [0, 1])


def test_explicit_normal_holiday_closure_continues_state():
    times = _times("2026-12-24T20:00:00Z", "2026-12-26T00:00:00Z")
    holiday = KnownExceptionInterval(
        start=pd.Timestamp("2026-12-24T21:00:00Z"),
        end=pd.Timestamp("2026-12-26T00:00:00Z"),
        classification="documented_holiday_closure",
        evidence_identifier="exchange-notice-2026-holiday",
        normal_market_closure=True,
    )

    result = audit_price_gaps(times, _always_trading, known_exceptions=[holiday])

    assert result.gaps[0].classification == "documented_holiday_closure"
    assert not result.gaps[0].reset_state
    np.testing.assert_array_equal(result.segment_ids, [0, 0])


def test_mixed_gap_with_partial_exception_coverage_is_unexplained():
    times = _times("2026-01-05T09:00:00Z", "2026-01-05T14:00:00Z")
    partial = KnownExceptionInterval(
        start=pd.Timestamp("2026-01-05T10:00:00Z"),
        end=pd.Timestamp("2026-01-05T12:00:00Z"),
        classification="provider_outage",
        evidence_identifier="partial-notice",
        normal_market_closure=False,
    )

    def scheduled_to_trade(timestamp: pd.Timestamp) -> bool:
        return timestamp.hour != 11

    result = audit_price_gaps(times, scheduled_to_trade, known_exceptions=[partial])

    assert result.gaps[0].classification == "unexplained_gap"
    assert result.gaps[0].evidence_identifier is None
    assert result.gaps[0].reset_state


def test_target_endpoint_mask_blocks_first_row_after_every_gap_class():
    times = _times(
        "2026-01-02T20:00:00Z",
        "2026-01-02T21:00:00Z",
        "2026-01-04T23:00:00Z",
        "2026-01-05T00:00:00Z",
        "2026-01-05T03:00:00Z",
    )

    def scheduled_to_trade(timestamp: pd.Timestamp) -> bool:
        return timestamp.dayofweek < 5

    result = audit_price_gaps(times, scheduled_to_trade)

    np.testing.assert_array_equal(
        result.target_end_allowed, [True, True, False, True, False]
    )
    assert result.target_end_allowed.dtype == np.dtype("bool")


def test_empty_and_contiguous_series_have_no_gaps():
    empty = pd.Series([], dtype="datetime64[ns, UTC]")
    contiguous = pd.Series(pd.date_range("2026-01-01T00:00:00Z", periods=3, freq="h"))

    empty_result = audit_price_gaps(empty, _always_trading)
    contiguous_result = audit_price_gaps(contiguous, _always_trading)

    assert empty_result.gaps == ()
    assert empty_result.segment_ids.dtype == np.dtype("int64")
    assert empty_result.target_end_allowed.dtype == np.dtype("bool")
    assert empty_result.segment_ids.size == empty_result.target_end_allowed.size == 0
    assert contiguous_result.gaps == ()
    np.testing.assert_array_equal(contiguous_result.segment_ids, [0, 0, 0])
    np.testing.assert_array_equal(
        contiguous_result.target_end_allowed, [True, True, True]
    )


@pytest.mark.parametrize(
    ("times", "message"),
    [
        (pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"])), "UTC"),
        (pd.Series(["2026-01-01T00:00:00Z"]), "UTC"),
        (
            pd.Series(
                pd.date_range(
                    "2026-01-01T00:00:00", periods=2, freq="h", tz="Asia/Jakarta"
                )
            ),
            "UTC",
        ),
        (
            pd.Series(pd.to_datetime(["2026-01-01", None], utc=True)),
            "NaT",
        ),
        (
            _times("2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
            "unique",
        ),
        (
            _times("2026-01-01T01:00:00Z", "2026-01-01T00:00:00Z"),
            "strictly increasing",
        ),
    ],
)
def test_invalid_source_timestamp_series_is_rejected(times: pd.Series, message: str):
    with pytest.raises(ValueError, match=message):
        audit_price_gaps(times, _always_trading)


def test_non_boolean_schedule_result_is_rejected():
    times = _times("2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z")

    with pytest.raises(TypeError, match="boolean"):
        audit_price_gaps(times, lambda _: 1)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "start": "2026-01-01T00:00:00Z",
            "end": pd.Timestamp("2026-01-02T00:00:00Z"),
            "classification": "holiday",
            "evidence_identifier": "notice",
            "normal_market_closure": True,
        },
        {
            "start": pd.Timestamp("2026-01-01T00:00:00"),
            "end": pd.Timestamp("2026-01-02T00:00:00Z"),
            "classification": "holiday",
            "evidence_identifier": "notice",
            "normal_market_closure": True,
        },
        {
            "start": pd.Timestamp("2026-01-02T00:00:00Z"),
            "end": pd.Timestamp("2026-01-01T00:00:00Z"),
            "classification": "holiday",
            "evidence_identifier": "notice",
            "normal_market_closure": True,
        },
        {
            "start": pd.Timestamp("2026-01-01T00:00:00Z"),
            "end": pd.Timestamp("2026-01-02T00:00:00Z"),
            "classification": " ",
            "evidence_identifier": "notice",
            "normal_market_closure": True,
        },
        {
            "start": pd.Timestamp("2026-01-01T00:00:00Z"),
            "end": pd.Timestamp("2026-01-02T00:00:00Z"),
            "classification": "holiday",
            "evidence_identifier": "",
            "normal_market_closure": True,
        },
        {
            "start": pd.Timestamp("2026-01-01T00:00:00Z"),
            "end": pd.Timestamp("2026-01-02T00:00:00Z"),
            "classification": "holiday",
            "evidence_identifier": "notice",
            "normal_market_closure": "yes",
        },
    ],
)
def test_malformed_exception_metadata_is_rejected(kwargs: dict[str, object]):
    with pytest.raises((TypeError, ValueError)):
        KnownExceptionInterval(**kwargs)


def test_exception_intervals_must_be_ordered_and_non_overlapping():
    first = KnownExceptionInterval(
        start=pd.Timestamp("2026-01-01T00:00:00Z"),
        end=pd.Timestamp("2026-01-02T00:00:00Z"),
        classification="holiday",
        evidence_identifier="notice-1",
        normal_market_closure=True,
    )
    overlapping = KnownExceptionInterval(
        start=pd.Timestamp("2026-01-01T12:00:00Z"),
        end=pd.Timestamp("2026-01-03T00:00:00Z"),
        classification="holiday",
        evidence_identifier="notice-2",
        normal_market_closure=True,
    )
    later = KnownExceptionInterval(
        start=pd.Timestamp("2026-01-03T00:00:00Z"),
        end=pd.Timestamp("2026-01-04T00:00:00Z"),
        classification="holiday",
        evidence_identifier="notice-3",
        normal_market_closure=True,
    )
    times = _times("2026-01-01T00:00:00Z")

    with pytest.raises(ValueError, match="ordered"):
        audit_price_gaps(times, _always_trading, known_exceptions=[later, first])
    with pytest.raises(ValueError, match="overlap"):
        audit_price_gaps(times, _always_trading, known_exceptions=[first, overlapping])


def test_gap_and_audit_records_are_frozen():
    result = audit_price_gaps(
        _times("2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z"),
        _always_trading,
    )

    assert isinstance(result, GapAuditResult)
    with pytest.raises(FrozenInstanceError):
        result.gaps = ()
    with pytest.raises(FrozenInstanceError):
        result.gaps[0].classification = "scheduled_closure"
