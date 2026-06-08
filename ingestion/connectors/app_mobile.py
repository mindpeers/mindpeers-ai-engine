"""App event connector stub — mood, motivation, sessions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator, Optional

from ingestion.connectors.base import BaseConnector, ConnectorConfig
from ingestion.service import IngestionService


class AppMobileConnector(BaseConnector):
    """
    Stub for iOS/Android app events.

    Production: subscribe to Kafka topic raw.app.events.v1 or poll mobile BFF.
    """

    SAMPLE_EVENTS = [
        {
            "event_id": "evt_mood_99102",
            "event_type": "mood_checkin",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-14T08:45:00+05:30",
            "occurred_at_utc": "2025-01-14T03:15:00Z",
            "local_date": "2025-01-14",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:mood_checkin:2025-01-14T08:45:00+05:30",
            "payload": {
                "mood_score": 5.8,
                "scale_min": 0,
                "scale_max": 10,
                "prompt_id": "daily_mood_v2",
                "optional_note_present": False,
            },
        },
        {
            "event_id": "evt_mot_99103",
            "event_type": "motivation_checkin",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-14T09:30:00+05:30",
            "occurred_at_utc": "2025-01-14T04:00:00Z",
            "local_date": "2025-01-14",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:motivation_checkin:2025-01-14T09:30:00+05:30",
            "payload": {"score": 4.0, "scale_min": 0, "scale_max": 5, "prompt_id": "motivation_daily_v1"},
        },
        {
            "event_id": "evt_sess_app_99104",
            "event_type": "app_session",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-14T10:00:00+05:30",
            "occurred_at_utc": "2025-01-14T04:30:00Z",
            "local_date": "2025-01-14",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:app_session:evt_sess_app_99104",
            "payload": {
                "session_duration_sec": 420,
                "screens_viewed": ["home", "engine"],
                "tasks_completed": 1,
                "platform": "ios",
                "app_version": "3.2.1",
            },
        },
    ]

    def __init__(self, ingestion: IngestionService) -> None:
        super().__init__(
            ConnectorConfig(
                connector_id="app_mobile",
                version="0.1.0",
                source_system="app_mobile",
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


def create_app_mobile_connector(ingestion: IngestionService) -> AppMobileConnector:
    return AppMobileConnector(ingestion)
