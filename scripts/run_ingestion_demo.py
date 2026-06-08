"""Run all connector stubs and print ingestion + staging summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.connectors.app_mobile import AppMobileConnector
from ingestion.connectors.assessments import AssessmentsConnector
from ingestion.connectors.therapy_platform import TherapyPlatformConnector
from ingestion.connectors.wearable_apple import WearableAppleConnector
from ingestion.service import InMemoryEventStore, IngestionService
from ingestion.staging import rollups_for_user


def main() -> None:
    store = InMemoryEventStore()
    ingestion = IngestionService(store)

    connectors = [
        AppMobileConnector(ingestion),
        WearableAppleConnector(ingestion),
        TherapyPlatformConnector(ingestion),
        AssessmentsConnector(ingestion),
    ]

    print("=== L0 Ingestion demo (user 1001) ===\n")
    for connector in connectors:
        results = connector.run_sync(user_id="1001")
        accepted = sum(1 for r in results if r.status.value == "accepted")
        dupes = sum(1 for r in results if r.status.value == "duplicate_skipped")
        print(f"{connector.config.connector_id}: accepted={accepted} duplicates={dupes}")

    # Idempotency demo — second sync should skip all
    print("\n--- Second sync (expect all duplicates) ---")
    results2 = connectors[0].run_sync(user_id="1001")
    print(f"app_mobile re-run: {results2[0].status.value}")

    # Invalid event → quarantine
    bad = {
        "event_id": "evt_bad_1",
        "event_type": "mood_checkin",
        "source_system": "app_mobile",
        "user_id": "1001",
        "local_date": "2025-01-14",
        "occurred_at": "2025-01-14T12:00:00+05:30",
        "idempotency_key": "1001:mood_checkin:bad",
        "payload": {"mood_score": 15, "scale_min": 0, "scale_max": 10},
    }
    q = ingestion.ingest(bad)
    print(f"\nInvalid mood (score=15): {q.status.value} reason={q.quarantine_reason}")

    rollups = rollups_for_user(store.list_events(), "1001")
    print("\n=== Staging rollups ===")
    for r in rollups:
        if r.local_date == "2025-01-14":
            print(json.dumps(r.to_dict(), indent=2))

    print(f"\nTotal raw events: {len(store.list_events())}")
    print(f"Quarantined: {len(store.quarantine)}")


if __name__ == "__main__":
    main()
