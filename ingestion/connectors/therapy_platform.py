"""Therapy platform connector stub."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator, Optional

from ingestion.connectors.base import BaseConnector, ConnectorConfig
from ingestion.service import IngestionService


class TherapyPlatformConnector(BaseConnector):
    SAMPLE_EVENTS = [
        {
            "event_id": "evt_sess_44201",
            "event_type": "session_attended",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-14T14:00:00+05:30",
            "occurred_at_utc": "2025-01-14T08:30:00Z",
            "local_date": "2025-01-14",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:session_attended:sess_44201",
            "payload": {
                "session_id": "sess_44201",
                "therapist_id": "th_88",
                "scheduled_duration_min": 50,
                "actual_duration_min": 48,
                "modality": "video",
                "homework_assigned": True,
                "homework_completed": False,
            },
        },
    ]

    def __init__(self, ingestion: IngestionService) -> None:
        super().__init__(
            ConnectorConfig(
                connector_id="therapy_platform",
                version="0.1.0",
                source_system="therapy_platform",
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
