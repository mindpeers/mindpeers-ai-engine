"""In-memory event store stub — replace with Postgres/BQ in production."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ingestion.models import IngestResult, IngestStatus, QuarantineRecord, RawEvent
from ingestion.validator import ValidationError, validate_event


class InMemoryEventStore:
    """Append-only raw event store with idempotency index."""

    def __init__(self) -> None:
        self._by_idempotency: dict[str, RawEvent] = {}
        self._events: list[RawEvent] = []
        self._quarantine: list[QuarantineRecord] = []

    def get_by_idempotency(self, key: str) -> Optional[RawEvent]:
        return self._by_idempotency.get(key)

    def list_events(self, user_id: Optional[str] = None) -> list[RawEvent]:
        if user_id is None:
            return list(self._events)
        return [e for e in self._events if e.user_id == user_id]

    @property
    def quarantine(self) -> list[QuarantineRecord]:
        return list(self._quarantine)


class IngestionService:
    """
    Core L0 ingest path: validate → dedupe → persist | quarantine.

    Production: inject EventStore backed by warehouse + async quarantine queue.
    """

    def __init__(self, store: InMemoryEventStore, connector_version: str = "0.1.0") -> None:
        self.store = store
        self.connector_version = connector_version

    def ingest(self, event_dict: dict) -> IngestResult:
        try:
            validate_event(event_dict)
        except ValidationError as exc:
            self._quarantine(event_dict, exc.reason)
            return IngestResult(
                status=IngestStatus.QUARANTINED,
                event_id=str(event_dict.get("event_id", "unknown")),
                message=str(exc),
                quarantine_reason=exc.reason,
            )

        key = event_dict["idempotency_key"]
        existing = self.store.get_by_idempotency(key)
        if existing:
            return IngestResult(
                status=IngestStatus.DUPLICATE_SKIPPED,
                event_id=existing.event_id,
                message="duplicate idempotency_key",
                original_ingested_at=existing.ingested_at,
            )

        now = datetime.now(timezone.utc)
        raw = RawEvent(
            event_id=event_dict["event_id"],
            event_type=event_dict["event_type"],
            event_version=event_dict.get("event_version", "1.0.0"),
            source_system=event_dict["source_system"],
            connector_version=event_dict.get("connector_version", self.connector_version),
            user_id=event_dict["user_id"],
            organization_id=event_dict.get("organization_id"),
            occurred_at=_parse_dt(event_dict["occurred_at"]),
            occurred_at_utc=_parse_dt(event_dict.get("occurred_at_utc", event_dict["occurred_at"])),
            local_date=event_dict["local_date"],
            timezone=event_dict.get("timezone", "UTC"),
            idempotency_key=key,
            payload=event_dict["payload"],
            ingested_at=now,
        )
        self.store._by_idempotency[key] = raw
        self.store._events.append(raw)
        return IngestResult(status=IngestStatus.ACCEPTED, event_id=raw.event_id)

    def _quarantine(self, event_dict: dict, reason: str) -> None:
        qid = f"q_{event_dict.get('event_id', 'unknown')}"
        self.store._quarantine.append(
            QuarantineRecord(
                quarantine_id=qid,
                original_event=event_dict,
                quarantine_reason=reason,
                quarantined_at=datetime.now(timezone.utc),
            )
        )


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)
