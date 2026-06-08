#!/usr/bin/env python3
"""
Validate ingestion event JSON files against schemas/ingestion.

Usage:
  python scripts/validate_ingestion_event.py path/to/event.json
  python scripts/validate_ingestion_event.py --sample mood_checkin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ingestion.validator import ValidationError, validate_event

SAMPLES = {
    "mood_checkin": {
        "event_id": "evt_mood_sample",
        "event_type": "mood_checkin",
        "event_version": "1.0.0",
        "source_system": "app_mobile",
        "connector_version": "0.1.0",
        "user_id": "1001",
        "occurred_at": "2025-01-14T08:45:00+05:30",
        "occurred_at_utc": "2025-01-14T03:15:00Z",
        "local_date": "2025-01-14",
        "timezone": "Asia/Kolkata",
        "idempotency_key": "1001:mood_checkin:sample",
        "payload": {"mood_score": 5.8, "scale_min": 0, "scale_max": 10},
    },
    "sleep_session": {
        "event_id": "evt_sleep_sample",
        "event_type": "sleep_session",
        "event_version": "1.0.0",
        "source_system": "wearable_apple",
        "connector_version": "0.1.0",
        "user_id": "1001",
        "occurred_at": "2025-01-14T07:00:00+05:30",
        "occurred_at_utc": "2025-01-14T01:30:00Z",
        "local_date": "2025-01-14",
        "timezone": "Asia/Kolkata",
        "idempotency_key": "1001:sleep_session:sample_vendor",
        "payload": {
            "sleep_start": "2025-01-13T23:15:00+05:30",
            "sleep_end": "2025-01-14T07:00:00+05:30",
            "duration_hours": 7.25,
            "vendor_session_id": "sample_vendor",
        },
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate L0 ingestion events")
    parser.add_argument("path", nargs="?", help="Path to event JSON file")
    parser.add_argument("--sample", choices=list(SAMPLES.keys()), help="Validate built-in sample")
    args = parser.parse_args()

    if args.sample:
        event = SAMPLES[args.sample]
    elif args.path:
        with Path(args.path).open(encoding="utf-8") as f:
            event = json.load(f)
    else:
        parser.print_help()
        return 1

    try:
        validate_event(event)
    except ValidationError as exc:
        print(f"FAIL: {exc.reason}")
        for detail in exc.details:
            print(f"  - {detail}")
        return 1

    print(f"OK: {event.get('event_type')} / {event.get('event_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
