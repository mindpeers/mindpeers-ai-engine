#!/usr/bin/env python3
"""Generate Engine POC sample dataset Excel workbook."""

import json

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

OUTPUT = "/Users/apple/Downloads/mp_ai/Engine-POC-Sample-Dataset.xlsx"

HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF")
SECTION_FILL = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
OPTIONAL_FILL = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")

# --- L2: required v1 (34) ---
L2_REQUIRED = [
    ("user_id", "string", "User identifier", "required"),
    ("as_of_date", "date", "Feature row date (UTC)", "required"),
    ("feature_version", "string", "Registry version e.g. feat_v1.0.0", "required"),
    ("days_active", "int", "Calendar days since registration", "required"),
    ("system_type", "int", "1=wearable+app, 0=web-only", "required"),
    ("data_completeness_score", "float", "0-1 completeness for maturity stage", "required"),
    ("mood_avg_14d", "float", "Mean mood 0-5 over 14d (canonical; was avg_mood_14d)", "required"),
    ("mood_slope_7d", "float", "OLS slope mood 7d", "required"),
    ("mood_volatility_14d", "float", "Std mood 14d", "required"),
    ("motivation_avg_14d", "float", "Mean motivation check-in 14d", "required"),
    ("motivation_slope_7d", "float", "OLS slope motivation 7d", "required"),
    ("confidence_avg_14d", "float", "Mean confidence check-in 14d", "required"),
    ("confidence_slope_7d", "float", "OLS slope confidence 7d", "required"),
    ("core_om_wellbeing", "float", "CORE-OM wellbeing 0-1", "required"),
    ("core_om_problems", "float", "CORE-OM problems 0-1 (higher=worse)", "required"),
    ("core_om_functioning", "float", "CORE-OM functioning 0-1", "required"),
    ("core_om_risk", "float", "CORE-OM risk 0-1", "required"),
    ("core_om_delta_30d", "float", "30d delta total CORE-OM normalized", "required"),
    ("gad7_normalized_latest", "float", "Latest GAD-7 0-1", "required"),
    ("engagement_rate_7d", "float", "Active days / 7", "required"),
    ("engagement_slope_7d", "float", "Engagement slope 7d", "required"),
    ("engagement_delta_30d", "float", "Engagement delta 30d", "required"),
    ("therapy_attendance_rate_30d", "float", "Attended / scheduled 30d", "required"),
    ("sleep_avg_7d", "float", "Mean sleep hours 7d", "required"),
    ("sleep_delta_30d", "float", "Sleep delta vs 30d baseline", "required"),
    ("sleep_slope_7d", "float", "Sleep hours slope 7d", "required"),
    ("sleep_persistence_low_days", "int", "Days sleep <6h in 14d", "required"),
    ("resting_hr_relative", "float", "HR relative to 30d baseline", "required"),
    ("activity_slope_7d", "float", "Activity slope 7d", "required"),
    ("cortisol_flag", "int", "0/1 stress/cortisol elevation", "required"),
    ("withdrawal_flag", "int", "0/1 engagement <0.25", "required"),
    ("sleep_mood_coupled_decline", "int", "0/1 coupled decline flag", "required"),
    ("journaling_concern_score_7d", "float", "Journaling concern 7d", "required"),
    ("composite_risk_percentile", "float", "Cohort risk percentile 0-100", "required"),
]

L2_OPTIONAL = [
    ("mood_delta_30d", "float", "Mood delta 30d — L4 / ML", "optional"),
    ("sleep_percentile_cohort", "float", "Sleep cohort percentile 0-100", "optional"),
    ("engagement_percentile_cohort", "float", "Engagement cohort percentile", "optional"),
    ("weeks_in_program", "float", "Legacy; prefer days_active", "optional"),
    ("engagement_persistence_low_days", "int", "Days low engagement 14d", "optional"),
    ("missed_sessions_30d", "int", "Missed therapy sessions 30d", "optional"),
    ("intent_behavior_mismatch_flag", "int", "0/1 intent vs behavior mismatch", "optional"),
    ("mood_persistence_decline_days", "int", "Days mood persistently declining", "optional"),
    ("fatigue_slope_7d", "float", "Fatigue slope 7d — L4 physiological", "optional"),
    ("hydration_slope_7d", "float", "Hydration slope 7d — L4", "optional"),
]

L2_ML_LABELS = [
    ("label_dropout_14d", "int", "0/1 dropout label 14d horizon", "ml_label"),
    ("label_regression_30d", "int", "0/1 regression label 30d", "ml_label"),
    ("label_engagement_decay_7d", "int", "0/1 engagement decay 7d", "ml_label"),
    ("label_regression_30d_prob", "float", "ML model output for patterns", "ml_inference"),
    ("label_dropout_14d_prob", "float", "ML dropout probability", "ml_inference"),
]

L2_LEGACY = [
    ("avg_mood_14d", "float", "DEPRECATED — rename to mood_avg_14d", "legacy"),
    ("core_om_normalized_score", "float", "DEPRECATED — use subscales", "legacy"),
]

L2_V11_DEFERRED = [
    ("phq9_normalized_score", "float", "v1.1 — not on Engine v1 report", "v1.1"),
    ("ptsd_normalized_score", "float", "v1.1", "v1.1"),
    ("asrs_partA_normalized", "float", "v1.1", "v1.1"),
    ("asrs_partB_normalized", "float", "v1.1", "v1.1"),
    ("hrv_rmssd_7d", "float", "v1.1 wearable", "v1.1"),
    ("stress_episode_count_7d", "int", "v1.1 wearable / heatmap", "v1.1"),
]

L2_ALL = L2_REQUIRED + L2_OPTIONAL + L2_ML_LABELS + L2_LEGACY + L2_V11_DEFERRED

SNAPSHOT_COLUMNS = [
    ("computed_at", "timestamp", "Batch compute time", "snapshot"),
    ("score_version", "string", "e.g. crs_v1.0.0", "snapshot"),
    ("data_maturity_stage", "enum", "cold_start | early | full", "snapshot"),
    ("cognitive_readiness_score", "float", "CRS 0-100", "snapshot"),
    ("clarity_score", "float", "Pillar 0-100", "snapshot"),
    ("emotional_balance_score", "float", "Pillar 0-100", "snapshot"),
    ("resilience_score", "float", "Pillar 0-100", "snapshot"),
    ("capacity_score", "float", "Pillar 0-100", "snapshot"),
    ("confidence_tier", "enum", "Limited | Moderate | High", "snapshot"),
    ("driver_biological_pct", "int", "Driver % biological", "snapshot"),
    ("driver_behavioral_pct", "int", "Driver % behavioral", "snapshot"),
    ("driver_psychological_pct", "int", "Driver % psychological", "snapshot"),
    ("drivers_visible", "bool", "Show driver section", "snapshot"),
    ("trends_json", "json", "Six trends blob", "snapshot"),
    ("pattern_cards_json", "json", "Pattern cards max 4", "snapshot"),
    ("recommendations_json", "json", "Top recommendations", "snapshot"),
    ("snapshot_stale", "bool", "Batch health flag", "snapshot"),
]

TREND_IDS = [
    "recovery_readiness",
    "stress_load",
    "sleep_consistency",
    "energy_rhythm",
    "emotional_stability",
    "motivation_confidence_momentum",
]

TREND_FLAT = []
for tid in TREND_IDS:
    TREND_FLAT.append((f"trend_{tid}_score", "float", f"{tid} score 0-100", "trend_flat"))
    TREND_FLAT.append((f"trend_{tid}_band", "string", f"{tid} Low|Moderate|High", "trend_flat"))
    TREND_FLAT.append((f"trend_{tid}_direction_7d", "string", f"{tid} improving|stable|declining", "trend_flat"))
    TREND_FLAT.append((f"trend_{tid}_available", "bool", f"{tid} data sufficient", "trend_flat"))

HISTORY_COLUMNS = [
    ("trend_id", "string", "One of six PRD trend ids", "history"),
    ("score", "float", "Trend score that day", "history"),
    ("band", "string", "Band that day", "history"),
    ("baseline", "float", "30d baseline if mature", "history"),
]

# Shared keys for wide sheet (user_id, as_of_date, feature_version on both L2 and snapshot)
SHARED_KEYS = ["user_id", "as_of_date", "feature_version"]

COMPLETE_WIDE_COLS = (
    [(c[0], c[1], c[2], c[3]) for c in L2_ALL]
    + [(c[0], c[1], c[2], c[3]) for c in SNAPSHOT_COLUMNS if c[0] not in ("feature_version",)]
    + [(c[0], c[1], c[2], c[3]) for c in TREND_FLAT]
)

TRENDS_U004 = {
    "recovery_readiness": {"score": 68, "band": "Moderate", "available": True, "direction_7d": "stable"},
    "stress_load": {"score": 22, "band": "Low", "available": True, "direction_7d": "improving"},
    "sleep_consistency": {"score": 74, "band": "High", "available": True, "direction_7d": "improving"},
    "energy_rhythm": {"score": 61, "band": "Moderate", "available": True, "direction_7d": "stable"},
    "emotional_stability": {"score": 65, "band": "Moderate", "available": True, "direction_7d": "improving"},
    "motivation_confidence_momentum": {"score": 72, "band": "High", "available": True, "direction_7d": "improving"},
}


def col_names(defs):
    return [d[0] for d in defs]


def build_l2_row(user_id, as_of_date, values: dict):
    row = []
    for name, *_ in L2_ALL:
        row.append(values.get(name))
    return row


def build_wide_row(values: dict):
    row = []
    for name, *_ in COMPLETE_WIDE_COLS:
        row.append(values.get(name))
    return row


def flat_trends(trends_dict):
    out = {}
    for tid in TREND_IDS:
        t = trends_dict.get(tid, {})
        out[f"trend_{tid}_score"] = t.get("score")
        out[f"trend_{tid}_band"] = t.get("band")
        out[f"trend_{tid}_direction_7d"] = t.get("direction_7d")
        out[f"trend_{tid}_available"] = t.get("available", True)
    return out


U004_L2 = {
    "user_id": "U004",
    "as_of_date": "2026-05-20",
    "feature_version": "feat_v1.0.0",
    "days_active": 52,
    "system_type": 1,
    "data_completeness_score": 0.85,
    "mood_avg_14d": 4.1,
    "mood_slope_7d": 0.08,
    "mood_volatility_14d": 0.38,
    "motivation_avg_14d": 4.0,
    "motivation_slope_7d": 0.05,
    "confidence_avg_14d": 4.2,
    "confidence_slope_7d": 0.1,
    "core_om_wellbeing": 0.75,
    "core_om_problems": 0.28,
    "core_om_functioning": 0.72,
    "core_om_risk": 0.15,
    "core_om_delta_30d": -0.12,
    "gad7_normalized_latest": 0.25,
    "engagement_rate_7d": 0.78,
    "engagement_slope_7d": 0.04,
    "engagement_delta_30d": 0.05,
    "therapy_attendance_rate_30d": 0.9,
    "sleep_avg_7d": 7.6,
    "sleep_delta_30d": 0.4,
    "sleep_slope_7d": 0.08,
    "sleep_persistence_low_days": 0,
    "resting_hr_relative": -0.01,
    "activity_slope_7d": 0.2,
    "cortisol_flag": 0,
    "withdrawal_flag": 0,
    "sleep_mood_coupled_decline": 0,
    "journaling_concern_score_7d": 0.08,
    "composite_risk_percentile": 28,
    "mood_delta_30d": 0.15,
    "sleep_percentile_cohort": 62,
    "engagement_percentile_cohort": 71,
    "weeks_in_program": 7.4,
    "engagement_persistence_low_days": 0,
    "missed_sessions_30d": 1,
    "intent_behavior_mismatch_flag": 0,
    "mood_persistence_decline_days": 0,
    "fatigue_slope_7d": -0.05,
    "hydration_slope_7d": 0.02,
    "label_dropout_14d": 0,
    "label_regression_30d": 0,
    "label_engagement_decay_7d": 0,
    "label_regression_30d_prob": 0.22,
    "label_dropout_14d_prob": 0.18,
    "avg_mood_14d": None,
    "core_om_normalized_score": None,
    "phq9_normalized_score": None,
    "ptsd_normalized_score": None,
    "asrs_partA_normalized": None,
    "asrs_partB_normalized": None,
    "hrv_rmssd_7d": None,
    "stress_episode_count_7d": None,
}

U004_SNAP = {
    "computed_at": "2026-05-20T02:15:00Z",
    "score_version": "crs_v1.0.0",
    "data_maturity_stage": "full",
    "cognitive_readiness_score": 71,
    "clarity_score": 68,
    "emotional_balance_score": 74,
    "resilience_score": 71,
    "capacity_score": 70,
    "confidence_tier": "High",
    "driver_biological_pct": 38,
    "driver_behavioral_pct": 34,
    "driver_psychological_pct": 28,
    "drivers_visible": True,
    "trends_json": json.dumps(TRENDS_U004),
    "pattern_cards_json": json.dumps([{"pattern_id": "positive_sleep_up", "type": "positive"}]),
    "recommendations_json": json.dumps([{"content_id": "sleep_hygiene_101", "rank": 1}]),
    "snapshot_stale": False,
    **flat_trends(TRENDS_U004),
}


def style_header(ws, ncol, fill=None):
    f = fill or HEADER_FILL
    for col in range(1, ncol + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = f
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def auto_width(ws, max_row_scan=25):
    for col in range(1, ws.max_column + 1):
        letter = get_column_letter(col)
        max_len = 10
        for row in range(1, min(ws.max_row, max_row_scan) + 1):
            val = ws.cell(row=row, column=col).value
            if val:
                max_len = max(max_len, min(len(str(val)), 45))
        ws.column_dimensions[letter].width = max_len + 2


def write_typed_sheet(wb, name, col_defs, sample_rows):
    """Header row + type row + tier row + data rows."""
    ws = wb.create_sheet(name)
    headers = [c[0] for c in col_defs]
    ws.append(headers)
    ws.append([c[1] for c in col_defs])
    ws.append([c[3] for c in col_defs])  # required | optional | snapshot | etc.
    ws.append([c[2] for c in col_defs])  # description
    for row in sample_rows:
        ws.append(row)
    style_header(ws, len(headers))
    auto_width(ws, 30)
    ws.freeze_panes = "A5"
    return ws


def main():
    wb = Workbook()
    wb.remove(wb.active)

    readme = wb.create_sheet("README", 0)
    readme["A1"] = "Engine POC Sample Dataset — All Columns"
    readme["A1"].font = Font(bold=True, size=14)
    lines = [
        "Version: 1.1 | Date: 2026-05-20",
        "",
        "PRIMARY SHEET FOR COLUMN CONFIRMATION:",
        "  All_Columns_Complete_Sample — every L2 + snapshot + flat trend column (2 users)",
        "",
        "Other sheets:",
        "  All_Columns_Index — master list of every column name",
        "  User_Feature_All_Columns_Sample — full L2 only (required+optional+ML+legacy+v1.1)",
        "  user_engine_snapshot_Sample — L3/L1 output",
        "  user_trend_history_Sample — chart history",
        "  Column_Definitions — same as index by sheet",
        "",
        f"Total unique columns in Complete sheet: {len(COMPLETE_WIDE_COLS)}",
        f"  L2 fields: {len(L2_ALL)}  |  Snapshot: {len(SNAPSHOT_COLUMNS)}  |  Flat trends: {len(TREND_FLAT)}",
    ]
    for i, line in enumerate(lines, start=2):
        readme[f"A{i}"] = line
    readme.column_dimensions["A"].width = 78

    # Master index
    idx = wb.create_sheet("All_Columns_Index")
    idx.append(["column_name", "data_type", "tier", "layer", "description"])
    style_header(idx, 5)
    for c in L2_ALL:
        idx.append([c[0], c[1], c[3], "L2_feature_row", c[2]])
    for c in SNAPSHOT_COLUMNS:
        idx.append([c[0], c[1], c[3], "user_engine_snapshot", c[2]])
    for c in TREND_FLAT:
        idx.append([c[0], c[1], c[3], "snapshot_or_history", c[2]])
    for c in HISTORY_COLUMNS:
        idx.append([c[0], c[1], c[3], "user_trend_history", c[2]])
    idx.append(["user_id", "string", "required", "all_layers", "Shared key"])
    idx.append(["as_of_date", "date", "required", "all_layers", "Shared key"])
    auto_width(idx)

    # Complete wide sample
    wide_u004 = {**U004_L2, **U004_SNAP}
    wide_u001 = {
        **{k: v for k, v in U004_L2.items()},
        "user_id": "U001",
        "days_active": 5,
        "system_type": 0,
        "data_completeness_score": 0.35,
        "motivation_avg_14d": None,
        "confidence_avg_14d": None,
        "resting_hr_relative": None,
        "computed_at": "2026-05-20T02:15:00Z",
        "score_version": "crs_v1.0.0",
        "data_maturity_stage": "cold_start",
        "cognitive_readiness_score": 52,
        "clarity_score": 54,
        "emotional_balance_score": 51,
        "resilience_score": 50,
        "capacity_score": 53,
        "confidence_tier": "Limited",
        "drivers_visible": False,
        "trends_json": "{}",
        "pattern_cards_json": "[]",
        "recommendations_json": "[]",
        "snapshot_stale": False,
        **flat_trends({}),
    }
    write_typed_sheet(
        wb,
        "All_Columns_Complete_Sample",
        COMPLETE_WIDE_COLS,
        [
            build_wide_row(wide_u004),
            build_wide_row(wide_u001),
        ],
    )

    # L2-only all columns
    write_typed_sheet(
        wb,
        "User_Feature_All_Columns_Sample",
        L2_ALL,
        [build_l2_row("U004", "2026-05-20", U004_L2)],
    )

    # Snapshot (original 20)
    snap_defs = [
        ("user_id", "string", "User id", "snapshot"),
        ("as_of_date", "date", "Date", "snapshot"),
    ] + SNAPSHOT_COLUMNS
    write_typed_sheet(
        wb,
        "user_engine_snapshot_Sample",
        snap_defs,
        [
            [
                "U004",
                "2026-05-20",
                U004_SNAP["computed_at"],
                U004_SNAP["score_version"],
                U004_L2["feature_version"],
                U004_SNAP["data_maturity_stage"],
                U004_SNAP["cognitive_readiness_score"],
                U004_SNAP["clarity_score"],
                U004_SNAP["emotional_balance_score"],
                U004_SNAP["resilience_score"],
                U004_SNAP["capacity_score"],
                U004_SNAP["confidence_tier"],
                U004_SNAP["driver_biological_pct"],
                U004_SNAP["driver_behavioral_pct"],
                U004_SNAP["driver_psychological_pct"],
                U004_SNAP["drivers_visible"],
                U004_SNAP["trends_json"],
                U004_SNAP["pattern_cards_json"],
                U004_SNAP["recommendations_json"],
                U004_SNAP["snapshot_stale"],
            ],
        ],
    )

    # Trend history
    hist_defs = [
        ("user_id", "string", "User id", "history"),
        ("as_of_date", "date", "Date", "history"),
    ] + HISTORY_COLUMNS
    hist_rows = []
    for d, score in [(14, 58), (15, 60), (16, 59), (17, 62), (18, 61), (19, 63), (20, 65)]:
        hist_rows.append(["U004", f"2026-05-{d:02d}", "emotional_stability", score, "Moderate", 55])
    write_typed_sheet(wb, "user_trend_history_Sample", hist_defs, hist_rows)

    # Legacy smaller sheet — required L2 columns only
    write_typed_sheet(
        wb,
        "User_Feature_Row_Sample",
        L2_REQUIRED,
        [[U004_L2[c[0]] for c in L2_REQUIRED]],
    )

    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")
    print(f"  All_Columns_Complete_Sample: {len(COMPLETE_WIDE_COLS)} columns")
    print(f"  User_Feature_All_Columns_Sample: {len(L2_ALL)} columns")


if __name__ == "__main__":
    main()
