"""Core ingestion types and result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class IngestStatus(str, Enum):
    ACCEPTED = "accepted"
    DUPLICATE_SKIPPED = "duplicate_skipped"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


@dataclass(frozen=True)
class IngestResult:
    status: IngestStatus
    event_id: str
    message: str = ""
    quarantine_reason: Optional[str] = None
    original_ingested_at: Optional[datetime] = None


@dataclass
class RawEvent:
    """Canonical in-memory representation before persistence."""

    event_id: str
    event_type: str
    event_version: str
    source_system: str
    connector_version: str
    user_id: str
    occurred_at: datetime
    occurred_at_utc: datetime
    local_date: str
    timezone: str
    idempotency_key: str
    payload: dict[str, Any]
    organization_id: Optional[str] = None
    ingested_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "source_system": self.source_system,
            "connector_version": self.connector_version,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "occurred_at": self.occurred_at.isoformat(),
            "occurred_at_utc": self.occurred_at_utc.isoformat(),
            "local_date": self.local_date,
            "timezone": self.timezone,
            "idempotency_key": self.idempotency_key,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "payload": self.payload,
        }


@dataclass
class QuarantineRecord:
    quarantine_id: str
    original_event: dict[str, Any]
    quarantine_reason: str
    quarantined_at: datetime
    retry_eligible: bool = False
    review_status: str = "pending"


@dataclass
class StagingDailyRollup:
    """staging.user_daily_activity — one row per user per local_date."""

    user_id: str
    local_date: str
    mood_checkin_count: int = 0
    mood_scores: list[float] = field(default_factory=list)
    motivation_scores: list[float] = field(default_factory=list)
    confidence_scores: list[float] = field(default_factory=list)
    app_sessions: int = 0
    total_session_sec: int = 0
    tasks_completed: int = 0
    sleep_hours: Optional[float] = None
    resting_hr_bpm: Optional[int] = None
    hrv_rmssd_ms: Optional[float] = None
    steps: Optional[int] = None
    therapy_attended: int = 0
    therapy_missed: int = 0
    journal_entries: int = 0
    has_wearable_data: bool = False
    staging_built_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "local_date": self.local_date,
            "mood_checkin_count": self.mood_checkin_count,
            "mood_scores": self.mood_scores,
            "motivation_scores": self.motivation_scores,
            "confidence_scores": self.confidence_scores,
            "app_sessions": self.app_sessions,
            "total_session_sec": self.total_session_sec,
            "tasks_completed": self.tasks_completed,
            "sleep_hours": self.sleep_hours,
            "resting_hr_bpm": self.resting_hr_bpm,
            "hrv_rmssd_ms": self.hrv_rmssd_ms,
            "steps": self.steps,
            "therapy_attended": self.therapy_attended,
            "therapy_missed": self.therapy_missed,
            "journal_entries": self.journal_entries,
            "has_wearable_data": self.has_wearable_data,
            "staging_built_at": self.staging_built_at.isoformat() if self.staging_built_at else None,
        }
