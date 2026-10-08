"""Snapshot-bound timestamp check with the Bab 3 vintage limitation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from thesis_experiments.protocol import Phase4Protocol

ANCHORS = (
    ("US_NFP", "2020-01-10T13:30:00Z"),
    ("US_CPI_MM", "2020-01-14T13:30:00Z"),
    ("US_NFP", "2020-07-02T12:30:00Z"),
    ("US_CPI_MM", "2020-07-14T12:30:00Z"),
    ("US_NFP", "2020-11-06T13:30:00Z"),
    ("US_CPI_MM", "2020-11-12T13:30:00Z"),
    ("US_FOMC", "2024-01-31T19:00:00Z"),
    ("US_NFP", "2024-07-05T12:30:00Z"),
    ("US_CPI_MM", "2024-07-11T12:30:00Z"),
    ("US_FOMC", "2024-07-31T18:00:00Z"),
)


def audit_macro_snapshot(root: Path, protocol: Phase4Protocol) -> tuple[pd.DataFrame, dict]:
    settings = protocol.inputs["macro"]
    path = root / settings.path
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != settings.sha256:
        raise ValueError("Macro snapshot differs from the frozen SHA-256")
    frame = pd.read_csv(path)
    if frame["value_id"].duplicated().any():
        raise ValueError("Duplicate macro value_id")
    if not (frame["server_name"] == "MetaQuotes-Demo").all() or not (frame["terminal_build"] == 6104).all():
        raise ValueError("Macro snapshot provenance changed")
    derived = frame.copy()
    derived["event_time_utc"] = pd.to_datetime(
        derived["event_time_server"], format="%Y.%m.%dT%H:%M:%S", utc=True, errors="raise"
    )
    checks = []
    for code, expected in ANCHORS:
        when = pd.Timestamp(expected)
        matched = derived.loc[(derived["event_code"] == code) & (derived["event_time_utc"] == when)]
        checks.append({"event_code": code, "expected_utc": expected, "matches": len(matched), "passed": len(matched) == 1})
    anchors_pass = all(check["passed"] for check in checks)
    report = {
        "snapshot_sha256": actual_hash,
        "rows": len(derived),
        "timestamp_rule": "event_time_utc = UTC-localized event_time_server, snapshot-specific",
        "timestamp_status": "PASS" if anchors_pass else "FAIL",
        "anchors": checks,
        "vintage_status": "LIMITATION: retrospective snapshot is not point-in-time",
        "vintage_reason": "Independent first-release and pre-release forecast history is unavailable; Bab 3 adopts the frozen MT5 forecast as an operational assumption",
        "k3_status": "ELIGIBLE" if anchors_pass else "NOT TESTED",
    }
    return derived, report
