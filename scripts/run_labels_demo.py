#!/usr/bin/env python3
"""Demonstrate §4.3 clinical label rules from CRS spec."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.labels import CoreOmSnapshot, LabelConfig, compute_clinical_labels


def main() -> None:
    cfg = LabelConfig()
    snapshot = date(2025, 1, 1)

    baseline = CoreOmSnapshot(
        occurred_at=snapshot,
        total_score=22,
        wellbeing_norm=0.45,
        problems_norm=0.55,
        functioning_norm=0.50,
        risk_norm=0.20,
    )
    followup_recovery = CoreOmSnapshot(
        occurred_at=date(2025, 1, 31),
        total_score=17,
        wellbeing_norm=0.52,
        problems_norm=0.38,
        functioning_norm=0.55,
        risk_norm=0.15,
    )
    result = compute_clinical_labels(
        "1001",
        snapshot,
        baseline,
        [baseline, followup_recovery],
        cfg,
    )
    print("Recovery example:", result)

    baseline_relapse = CoreOmSnapshot(
        occurred_at=snapshot,
        total_score=18,
        wellbeing_norm=0.50,
        problems_norm=0.40,
        functioning_norm=0.55,
        risk_norm=0.25,
    )
    followup_relapse = CoreOmSnapshot(
        occurred_at=date(2025, 1, 31),
        total_score=19,
        wellbeing_norm=0.48,
        problems_norm=0.42,
        functioning_norm=0.52,
        risk_norm=0.72,
    )
    result2 = compute_clinical_labels(
        "1002",
        snapshot,
        baseline_relapse,
        [baseline_relapse, followup_relapse],
        cfg,
    )
    print("Relapse via risk example:", result2)

    censored = compute_clinical_labels("1003", snapshot, baseline, [baseline], cfg)
    print("Censored example:", censored)


if __name__ == "__main__":
    main()
