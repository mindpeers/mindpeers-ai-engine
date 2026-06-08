"""Build staging.user_daily_activity rollups from raw events."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

from ingestion.models import RawEvent, StagingDailyRollup


def build_daily_rollups(events: Iterable[RawEvent]) -> dict[tuple[str, str], StagingDailyRollup]:
    """
    Aggregate raw events into per-user per-local_date staging rows.

    Production: run as daily Spark/SQL job at 01:30 UTC over raw.* partitions.
    """
    buckets: dict[tuple[str, str], StagingDailyRollup] = {}

    for event in events:
        key = (event.user_id, event.local_date)
        if key not in buckets:
            buckets[key] = StagingDailyRollup(user_id=event.user_id, local_date=event.local_date)
        rollup = buckets[key]
        _apply_event(rollup, event)

    built_at = datetime.now(timezone.utc)
    for rollup in buckets.values():
        rollup.staging_built_at = built_at
    return buckets


def _apply_event(rollup: StagingDailyRollup, event: RawEvent) -> None:
    p = event.payload
    et = event.event_type

    if et == "mood_checkin":
        rollup.mood_checkin_count += 1
        rollup.mood_scores.append(float(p["mood_score"]))
    elif et == "motivation_checkin":
        rollup.motivation_scores.append(float(p["score"]))
    elif et == "confidence_checkin":
        rollup.confidence_scores.append(float(p["score"]))
    elif et == "app_session":
        rollup.app_sessions += 1
        rollup.total_session_sec += int(p.get("session_duration_sec", 0))
        rollup.tasks_completed += int(p.get("tasks_completed", 0))
    elif et == "sleep_session":
        rollup.sleep_hours = float(p["duration_hours"])
        rollup.has_wearable_data = True
    elif et == "heart_rate_daily":
        rollup.resting_hr_bpm = int(p["resting_hr_bpm"])
        if p.get("hrv_rmssd_ms") is not None:
            rollup.hrv_rmssd_ms = float(p["hrv_rmssd_ms"])
        rollup.has_wearable_data = True
    elif et == "activity_daily":
        rollup.steps = int(p.get("steps", 0))
        rollup.has_wearable_data = True
    elif et == "session_attended":
        rollup.therapy_attended += 1
    elif et == "session_missed":
        rollup.therapy_missed += 1
    elif et == "journal_entry":
        rollup.journal_entries += 1


def rollups_for_user(
    events: Iterable[RawEvent], user_id: str
) -> list[StagingDailyRollup]:
    all_rollups = build_daily_rollups(events)
    return sorted(
        (r for (uid, _), r in all_rollups.items() if uid == user_id),
        key=lambda r: r.local_date,
    )
