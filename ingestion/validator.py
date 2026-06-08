"""JSON Schema validation for ingestion events (stdlib-only fallback)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

SCHEMA_ROOT = Path(__file__).resolve().parent.parent / "schemas" / "ingestion"

# Optional: jsonschema if installed in venv
try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class ValidationError(Exception):
    def __init__(self, reason: str, details: Optional[list[str]] = None):
        super().__init__(reason)
        self.reason = reason
        self.details = details or []


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_registry() -> dict[str, Any]:
    return _load_json(SCHEMA_ROOT / "registry.json")


def load_envelope_schema() -> dict[str, Any]:
    return _load_json(SCHEMA_ROOT / "common" / "envelope.v1.json")


def load_payload_schema(event_type: str) -> dict[str, Any]:
    registry = load_registry()
    entry = registry.get("events", {}).get(event_type)
    if not entry:
        raise ValidationError(f"unknown_event_type:{event_type}")
    rel = entry["payload_schema"]
    return _load_json(SCHEMA_ROOT / rel)


def validate_event(event: dict[str, Any]) -> None:
    """Validate full envelope + payload. Raises ValidationError on failure."""
    event_type = event.get("event_type")
    if not event_type:
        raise ValidationError("missing_event_type")

    if HAS_JSONSCHEMA:
        jsonschema.validate(event, load_envelope_schema())
        jsonschema.validate(event.get("payload", {}), load_payload_schema(event_type))
        return

    _validate_envelope_minimal(event)
    _validate_payload_minimal(event_type, event.get("payload", {}))


def _validate_envelope_minimal(event: dict[str, Any]) -> None:
    required = [
        "event_id",
        "event_type",
        "source_system",
        "user_id",
        "local_date",
        "idempotency_key",
        "payload",
    ]
    missing = [k for k in required if k not in event or event[k] in (None, "")]
    if missing:
        raise ValidationError("missing_required_fields", missing)


def _validate_payload_minimal(event_type: str, payload: dict[str, Any]) -> None:
    if event_type == "mood_checkin":
        score = payload.get("mood_score")
        if score is None or not (0 <= float(score) <= 10):
            raise ValidationError("mood_score_out_of_range")
    elif event_type == "sleep_session":
        duration = payload.get("duration_hours")
        if duration is None or not (0 < float(duration) <= 16):
            raise ValidationError("duration_hours_out_of_range")
    elif event_type == "assessment_completed":
        if payload.get("instrument") == "CORE-OM":
            sub = payload.get("subscales") or {}
            for key in ("wellbeing", "problems", "functioning", "risk"):
                if key not in sub:
                    raise ValidationError("core_om_subscales_missing")
