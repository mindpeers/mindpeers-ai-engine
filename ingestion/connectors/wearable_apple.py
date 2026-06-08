"""Wearable connector stub — sleep and heart rate daily summaries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator, Optional

from ingestion.connectors.base import BaseConnector, ConnectorConfig
from ingestion.service import IngestionService


class WearableAppleConnector(BaseConnector):
    """
    Stub for Apple HealthKit sync.

    Production: OAuth token per user, scheduled pull every 6h, vendor_session_id dedupe.
    """

    SAMPLE_EVENTS = [
        {
            "event_id": "evt_sleep_88421",
            "event_type": "sleep_session",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-14T07:00:00+05:30",
            "occurred_at_utc": "2025-01-14T01:30:00Z",
            "local_date": "2025-01-14",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:sleep_session:ah_sleep_88271",
            "payload": {
                "sleep_start": "2025-01-13T23:15:00+05:30",
                "sleep_end": "2025-01-14T07:00:00+05:30",
                "duration_hours": 7.25,
                "efficiency": 0.88,
                "awakenings": 2,
                "deep_sleep_min": 95,
                "rem_sleep_min": 110,
                "bedtime_local": "23:15",
                "wake_time_local": "07:00",
                "vendor_session_id": "ah_sleep_88271",
            },
        },
        {
            "event_id": "evt_hr_88422",
            "event_type": "heart_rate_daily",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-14T23:59:00+05:30",
            "occurred_at_utc": "2025-01-14T18:29:00Z",
            "local_date": "2025-01-14",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:heart_rate_daily:2025-01-14",
            "payload": {
                "resting_hr_bpm": 62,
                "hrv_rmssd_ms": 58,
                "hrv_source": "apple_watch",
                "sample_count": 288,
            },
        },
    ]

    def __init__(self, ingestion: IngestionService) -> None:
        super().__init__(
            ConnectorConfig(
                connector_id="wearable_apple",
                version="0.1.0",
                source_system="wearable_apple",
            ),
            ingestion,
        )

    def fetch_events(
        self,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> Iterator[dict[str, Any]]:
        for event in self.SAMPLE_EVENTS:
            if user_id and event["user_id"] != user_id:
                continue
            yield dict(event)
