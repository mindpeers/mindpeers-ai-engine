#!/usr/bin/env python3
"""Demo: L0 staging series → L2 feature row."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from features.pipeline import DailySeries, compute_features


def main() -> None:
    # 14-day synthetic history for user 1001 (mood 0-5 canonical)
    series = DailySeries(
        dates=[f"2025-01-{d:02d}" for d in range(1, 15)],
        mood=[3.6, 3.7, 3.8, 3.8, 3.9, 4.0, 4.0, 4.0, 4.1, 4.0, 4.1, 4.1, 4.2, 4.2],
        sleep_hours=[6.4, 6.5, 6.5, 6.6, 6.6, 6.7, 6.6, 6.8, 6.7, 6.6, 6.7, 6.8, 7.0, 7.25],
        engagement_active=[1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
        resting_hr=[64, 64, 63, 63, 63, 62, 62, 62, 62, 61, 62, 62, 62, 62],
    )

    row = compute_features(
        user_id="1001",
        as_of_date="2025-01-14",
        series=series,
        days_active=45,
        system_type=1,
    )

    print("=== L2 Feature pipeline demo ===\n")
    print(json.dumps(row.to_dict(), indent=2))


if __name__ == "__main__":
    main()
