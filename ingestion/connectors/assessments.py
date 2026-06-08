"""Assessment connector stub — CORE-OM, GAD-7."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator, Optional

from ingestion.connectors.base import BaseConnector, ConnectorConfig
from ingestion.service import IngestionService


class AssessmentsConnector(BaseConnector):
    SAMPLE_EVENTS = [
        {
            "event_id": "evt_core_1001",
            "event_type": "assessment_completed",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-01T10:00:00+00:00",
            "occurred_at_utc": "2025-01-01T10:00:00+00:00",
            "local_date": "2025-01-01",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:assessment_completed:core_1001_20250101",
            "payload": {
                "instrument": "CORE-OM",
                "instrument_version": "1.1",
                "assessment_id": "core_1001_20250101",
                "total_score": 18,
                "max_score": 40,
                "subscales": {
                    "wellbeing": {"raw": 12, "normalized": 0.75},
                    "problems": {"raw": 22, "normalized": 0.28},
                    "functioning": {"raw": 15, "normalized": 0.72},
                    "risk": {"raw": 3, "normalized": 0.15},
                },
            },
        },
        {
            "event_id": "evt_gad7_1001",
            "event_type": "assessment_completed",
            "event_version": "1.0.0",
            "user_id": "1001",
            "occurred_at": "2025-01-01T10:05:00+00:00",
            "occurred_at_utc": "2025-01-01T10:05:00+00:00",
            "local_date": "2025-01-01",
            "timezone": "Asia/Kolkata",
            "idempotency_key": "1001:assessment_completed:gad7_1001_20250101",
            "payload": {
                "instrument": "GAD-7",
                "instrument_version": "1.0",
                "assessment_id": "gad7_1001_20250101",
                "total_score": 9,
                "max_score": 21,
                "normalized": 0.43,
                "severity_band": "moderate",
            },
        },
    ]

    def __init__(self, ingestion: IngestionService) -> None:
        super().__init__(
            ConnectorConfig(
                connector_id="assessments",
                version="0.1.0",
                source_system="assessments",
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
