# L2 Feature Store — Production Specification

**Version:** 1.0.0  
**Status:** Production-ready specification  
**Layer:** L2 (reads L0 staging; feeds L3 Scoring + L4 ML)  
**Related docs:** [Data-Ingestion-Layer-Production-Spec.md](./Data-Ingestion-Layer-Production-Spec.md), [CRS-Calculation-and-Trends-Production-Spec.md](./CRS-Calculation-and-Trends-Production-Spec.md), [ENGINE-POC-COMPLETE-DOCUMENTATION.md](./ENGINE-POC-COMPLETE-DOCUMENTATION.md)  
**Implementation:** [features/](./features/), [scripts/run_feature_pipeline_demo.py](./scripts/run_feature_pipeline_demo.py)  
**Audience:** Engineering, ML, Data Platform  
**Last updated:** 2026-06-05

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Position in the architecture](#2-position-in-the-architecture)
3. [Design principles](#3-design-principles)
4. [Input contract (from L0 staging)](#4-input-contract-from-l0-staging)
5. [Output contract (to L3 / L4)](#5-output-contract-to-l3--l4)
6. [Canonical scale & normalization rules](#6-canonical-scale--normalization-rules)
7. [Feature registry (v1)](#7-feature-registry-v1)
8. [Computation specifications with examples](#8-computation-specifications-with-examples)
9. [Derived flags & cross-domain features](#9-derived-flags--cross-domain-features)
10. [Meta features: maturity & completeness](#10-meta-features-maturity--completeness)
11. [L0 → L2 column lineage (full matrix)](#11-l0--l2-column-lineage-full-matrix)
12. [Cold start, null handling, and imputation](#12-cold-start-null-handling-and-imputation)
13. [Batch pipeline & scheduling](#13-batch-pipeline--scheduling)
14. [Quality assurance & backtesting](#14-quality-assurance--backtesting)
15. [End-to-end walkthroughs](#15-end-to-end-walkthroughs)
16. [Implementation roadmap](#16-implementation-roadmap)
17. [Appendices](#17-appendices)

---

## 1. Executive summary

### 1.1 Purpose

The **L2 Feature Store** transforms **user-day staging rollups** (from L0) into **windowed, deterministic features** used by:

- **L3 Scoring** — CRS, pillars, trend composites  
- **L4 ML** — outcome models (recovery, dropout, relapse, engagement loss)  
- **L4 LLM** — intent context (trends, flags, patterns)

L2 answers: *What measurable signals describe this user's state and trajectory over 7, 14, and 30 days?*

### 1.2 What L2 owns vs does not own

| L2 owns | L2 does NOT own |
|---------|-----------------|
| Window aggregations (avg, std, slope, delta) | Raw event ingestion (L0) |
| Derived flags (`withdrawal_flag`, `sleep_mood_coupled_decline`) | 0–100 pillar/CRS scores (L3) |
| Clinical latest-value lookups | ML inference (L4) |
| `data_completeness_score`, `days_active` | Dashboard UI (L1) |
| Cohort percentiles (optional v1) | Trend band labels (L3) |

### 1.3 One-line flow

```
staging.user_daily_activity (L0) → L2 feature job → user_features_daily → L3 scoring + L4 ML
```

### 1.4 Worked example — output row

**User 1001, `as_of_date = 2025-01-14`, `days_active = 45`:**

```json
{
  "user_id": "1001",
  "as_of_date": "2025-01-14",
  "feature_version": "feat_v1.0.0",
  "days_active": 45,
  "system_type": 1,
  "data_completeness_score": 0.82,
  "data_maturity_stage": "full",
  "mood_avg_14d": 4.1,
  "mood_slope_7d": 0.08,
  "mood_volatility_14d": 0.38,
  "sleep_avg_7d": 6.6,
  "sleep_delta_30d": 0.4,
  "engagement_rate_7d": 0.71,
  "therapy_attendance_rate_30d": 0.80,
  "core_om_functioning": 0.72,
  "gad7_normalized_latest": 0.25,
  "cortisol_flag": 0,
  "withdrawal_flag": 0,
  "sleep_mood_coupled_decline": 0
}
```

This row is the **single input vector** L3 uses to produce CRS = 81.2 (v2) or pillar scores (v1).

---

## 2. Position in the architecture

### 2.1 Layer stack

```
L1 Product Engine
        ↑ snapshot
L3 Scoring (CRS, pillars, trends)
        ↑ user_features_daily
L2 Feature Store  ◄── THIS DOCUMENT
        ↑ staging.user_daily_activity
L0 Data Ingestion
        ↑ raw events
Source systems
```

### 2.2 Daily schedule (UTC)

| Time | Layer | Job |
|------|-------|-----|
| 01:30 | L0 | Staging finalize |
| **02:00** | **L2** | **Feature computation (this layer)** |
| 02:30 | L4 ML | Outcome model inference |
| 02:45 | L3 | Scoring |
| 03:05 | L1 | Snapshot persist |

**Gate:** L2 starts only when L0 watermarks confirm staging complete for `as_of_date`.

### 2.3 Determinism rule

```
Same staging history + same feature_version + same as_of_date → identical L2 output
```

No randomness. No LLM. All formulas versioned in config (`feat_v1.0.0`).

---

## 3. Design principles

| # | Principle | Example |
|---|-----------|---------|
| 1 | **Canonical names only** | `mood_avg_14d` not `avg_mood_14d` |
| 2 | **Explicit nulls** | `null` + `{feature}_missing = 1` when window insufficient |
| 3 | **User-local windows** | 7d mood window = last 7 calendar days in user TZ |
| 4 | **Point-in-time correct** | Features at T use only data ≤ T (no future leakage for ML labels) |
| 5 | **Separation of measurement vs score** | L2 outputs raw-ish features; L3 normalizes to 0–100 |
| 6 | **Wearable-aware** | `system_type=0` → biological features null, not zero |
| 7 | **Version everything** | `feature_version` bump on formula change |

---

## 4. Input contract (from L0 staging)

### 4.1 Primary input table

**Table:** `staging.user_daily_activity`  
**Grain:** `(user_id, local_date)`  
**Spec:** [Data Ingestion §7.3](./Data-Ingestion-Layer-Production-Spec.md)

### 4.2 Required staging fields for L2 v1

| Field | Type | Used for |
|-------|------|----------|
| `user_id` | string | Identity |
| `local_date` | date | Window alignment |
| `mood_scores` | float[] | Daily mood (canonical 0–5 after L0 normalize) |
| `motivation_scores` | float[] | Motivation check-ins |
| `confidence_scores` | float[] | Confidence check-ins |
| `app_sessions` | int | Engagement |
| `tasks_completed` | int | Engagement |
| `sleep_hours` | float | Sleep features |
| `bedtime_local` | string | Sleep consistency (HH:MM) |
| `wake_time_local` | string | Sleep consistency |
| `resting_hr_bpm` | int | HR relative |
| `hrv_rmssd_ms` | float | v1.1 biological |
| `active_minutes` | int | Activity slope |
| `therapy_attended` | int | Attendance numerator |
| `therapy_missed` | int | Attendance denominator |
| `therapy_scheduled` | int | Attendance denominator |
| `journal_concern_scores` | float[] | NLP concern rollup |
| `has_wearable_data` | bool | Completeness |
| `stress_elevation_detected` | bool | `cortisol_flag` proxy |

### 4.3 Secondary inputs

| Source | Table | Purpose |
|--------|-------|---------|
| L0 raw | `raw.assessments` | Latest CORE-OM, GAD-7 subscales |
| L0 raw | `raw.users` | `registration_date`, `timezone`, `system_type` |
| L0 staging | `staging.ingestion_watermarks` | Pipeline gate |

### 4.4 Example — 14 days staging for user 1001

| local_date | mood_daily | sleep_h | engaged | therapy_att |
|------------|-----------|---------|---------|-------------|
| Jan 1 | 3.8 | 6.8 | 1 | 0 |
| Jan 2 | 4.0 | 7.0 | 1 | 0 |
| … | … | … | … | … |
| Jan 14 | 4.2 | 7.25 | 1 | 1 |

L2 at `as_of_date = Jan 14` reads Jan 1–Jan 14 inclusive.

---

## 5. Output contract (to L3 / L4)

### 5.1 Primary output table

**Table:** `features.user_features_daily`  
**Grain:** `(user_id, as_of_date)`  
**Partition:** `as_of_date`

### 5.2 Required columns (v1 — 34 features + meta)

See [§7 Feature registry](#7-feature-registry-v1) and [ENGINE-POC Part 8](./ENGINE-POC-COMPLETE-DOCUMENTATION.md).

### 5.3 Output JSON (API / export shape)

```json
{
  "user_id": "1001",
  "as_of_date": "2025-01-14",
  "feature_version": "feat_v1.0.0",
  "computed_at": "2025-01-15T02:12:00Z",
  "days_active": 45,
  "system_type": 1,
  "data_maturity_stage": "full",
  "data_completeness_score": 0.82,
  "features": {
    "mood_avg_14d": 4.1,
    "mood_slope_7d": 0.08,
    "mood_volatility_14d": 0.38,
    "sleep_avg_7d": 6.6,
    "cortisol_flag": 0,
    "withdrawal_flag": 0
  },
  "missing_flags": {
    "resting_hr_relative_missing": 0,
    "motivation_avg_14d_missing": 0
  }
}
```

### 5.4 Downstream consumers

| Consumer | Reads | Must not |
|----------|-------|----------|
| L3 Scoring | Full feature row | Recompute windows from raw |
| L4 ML training | Feature row + labels | Use future data in features at T |
| L4 LLM context | Subset per intent config | Invent feature values |
| Validation CI | Export CSV/Parquet | Mix legacy column names |

---

## 6. Canonical scale & normalization rules

### 6.1 Mood scale (closed decision)

| Stage | Scale | Rule |
|-------|-------|------|
| **App ingest (L0)** | May send 0–10 | L0 normalizes: `mood_canonical = mood_raw × 0.5` if `scale_max=10` |
| **Staging (L0)** | 0–5 | Store canonical only |
| **L2 features** | 0–5 | All mood formulas use 0–5 |
| **L3 scoring** | 0–100 | L3 maps 0–5 → 0–100 |

**Example:**

```
App sends mood_score=7.6 on 0-10 scale
L0 staging: mood_daily = 3.8
L2 mood_avg_14d = mean([3.6, 3.8, 4.0, ...]) = 4.1
L3 normalized mood contribution = map_0_5_to_100(4.1) ≈ 82
```

### 6.2 Other canonical scales

| Signal | Canonical range | Notes |
|--------|-------------------|-------|
| Motivation / confidence | 0–5 | Daily check-in |
| Engagement rate | 0–1 | Active days / window |
| CORE-OM subscales | 0–1 normalized | Higher functioning = higher wellbeing score |
| GAD-7 | 0–1 normalized | `score / 21` |
| Sleep hours | 0–16 (typical 4–9) | Raw hours |
| Therapy attendance | 0–1 | Rate |

### 6.3 Daily aggregation rules (staging → daily series)

Before window functions, collapse staging to **one value per user per local_date**:

| Series | Daily value rule |
|--------|------------------|
| `mood_daily` | Mean of same-day check-ins (max 20; warn if >5) |
| `motivation_daily` | Mean of same-day check-ins |
| `confidence_daily` | Mean of same-day check-ins |
| `engagement_daily` | `1` if `app_sessions > 0 OR tasks_completed > 0`, else `0` |
| `engagement_score_daily` | `min(1.0, tasks_completed × 0.2 + (1 if sessions else 0) × 0.5)` |
| `sleep_hours_daily` | Primary sleep session duration (longest if multiple) |
| `resting_hr_daily` | From wearable daily summary |
| `active_minutes_daily` | From activity summary |

**Example — engagement_score_daily:**

| Date | sessions | tasks | engagement_daily | engagement_score_daily |
|------|----------|-------|------------------|------------------------|
| Jan 12 | 1 | 2 | 1 | 0.5 + 0.4 = 0.9 |
| Jan 13 | 0 | 0 | 0 | 0.0 |
| Jan 14 | 1 | 1 | 1 | 0.5 + 0.2 = 0.7 |

---

## 7. Feature registry (v1)

### 7.1 Registry rules

- One **canonical name** per concept  
- `feature_version`: `feat_v1.0.0` — bump on breaking formula change  
- CI: export columns ⊆ registry; L3/L4 configs reference canonical names only  

### 7.2 Alias map

| Legacy (reject in new pipelines) | Canonical |
|----------------------------------|-----------|
| `avg_mood_14d` | `mood_avg_14d` |

### 7.3 Full v1 registry

| Canonical | Type | Window | Min days | Used by |
|-----------|------|--------|----------|---------|
| `mood_avg_14d` | continuous | 14d | 7 | L3 pillars, trends; L4 ML |
| `mood_slope_7d` | slope | 7d | 7 | L3, L4 |
| `mood_volatility_14d` | std | 14d | 7 | L3, L4 |
| `mood_delta_30d` | delta | 30d | 30 | L4 optional |
| `motivation_avg_14d` | continuous | 14d | 7 | L3 trends |
| `motivation_slope_7d` | slope | 7d | 7 | L3 trends |
| `confidence_avg_14d` | continuous | 14d | 7 | L3 trends |
| `confidence_slope_7d` | slope | 7d | 7 | L3 trends |
| `core_om_wellbeing` | clinical | latest | 0 | L3 Emotional Balance |
| `core_om_problems` | clinical | latest | 0 | L3 Emotional Balance |
| `core_om_functioning` | clinical | latest | 0 | L3 Clarity, Capacity |
| `core_om_risk` | clinical | latest | 0 | L4 escalation, patterns |
| `core_om_delta_30d` | delta | 30d | 30 | L3 Resilience |
| `gad7_normalized_latest` | clinical | 90d lookback | 0 | L3 Emotional Balance |
| `engagement_rate_7d` | rate | 7d | 0 | L3, L4 |
| `engagement_slope_7d` | slope | 7d | 7 | L3, L4 |
| `engagement_delta_30d` | delta | 30d | 30 | L3 Capacity |
| `therapy_attendance_rate_30d` | rate | 30d | 7 | L3, L4 |
| `sleep_avg_7d` | continuous | 7d | 7 | L3, L4 |
| `sleep_delta_30d` | delta | 30d | 30 | L3, L4 |
| `sleep_slope_7d` | slope | 7d | 7 | L3 |
| `sleep_persistence_low_days` | count | 14d | 7 | L3 |
| `sleep_duration_variance_14d` | variance | 14d | 7 | L3 Sleep Consistency trend |
| `bedtime_variance_14d` | variance | 14d | 7 | L3 Sleep Consistency trend |
| `resting_hr_relative` | relative | 7d vs 30d baseline | 30 | L3 |
| `activity_slope_7d` | slope | 7d | 7 | L3 |
| `cortisol_flag` | flag | 7d | 0 | L3 Stress Load |
| `withdrawal_flag` | flag | 7d | 7 | L4, patterns |
| `sleep_mood_coupled_decline` | flag | 30d | 30 | L4, patterns |
| `journaling_concern_score_7d` | continuous | 7d | 7 | L4 |
| `data_completeness_score` | meta | — | 0 | L3 confidence |
| `days_active` | meta | — | 0 | L3 maturity |
| `system_type` | meta | — | 0 | L3 G15 |

### 7.4 Deferred v1.1

`phq9_*`, `ptsd_*`, `asrs_*`, `hrv_rmssd_7d`, `stress_episode_count_7d`, `composite_risk_percentile` (optional cohort job).

---

## 8. Computation specifications with examples

### 8.1 Window notation

For `as_of_date = D`, window `Wd` means local dates `(D − w + 1) … D` inclusive.

**Example:** 7d window ending Jan 14 = Jan 8–Jan 14.

### 8.2 Continuous averages

**Formula:**

```
mood_avg_14d = mean(mood_daily[d] for d in last 14 days where mood_daily not null)
```

**Null if:** fewer than 3 non-null mood days in 14d.

**Worked example:**

```
Jan 1-14 mood_daily: [3.8, 4.0, null, 4.2, 3.9, 4.1, 4.0, 3.8, 4.2, 4.0, 3.9, 4.1, 4.2, 4.2]
Non-null count = 13 ≥ 3
mood_avg_14d = sum / 13 = 4.05
```

Same pattern for: `motivation_avg_14d`, `confidence_avg_14d`, `sleep_avg_7d`.

### 8.3 OLS slope (7-day)

**Formula:**

```
mood_slope_7d = OLS_slope(x=day_index, y=mood_daily) over last 7 days with ≥4 non-null points
```

**Implementation (simple linear regression):**

```python
def ols_slope(values: list[float | None]) -> float | None:
    pts = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pts) < 4:
        return None
    n = len(pts)
    sx = sum(i for i, _ in pts)
    sy = sum(v for _, v in pts)
    sxx = sum(i * i for i, _ in pts)
    sxy = sum(i * v for i, v in pts)
    denom = n * sxx - sx * sx
    if denom == 0:
        return None
    return (n * sxy - sx * sy) / denom
```

**Worked example:**

| Day | mood |
|-----|------|
| D-6 | 3.6 |
| D-5 | 3.7 |
| D-4 | 3.8 |
| D-3 | 3.9 |
| D-2 | 4.0 |
| D-1 | 4.1 |
| D | 4.2 |

`mood_slope_7d ≈ +0.10` per day → improving.

Apply to: `mood_slope_7d`, `sleep_slope_7d`, `engagement_slope_7d`, `motivation_slope_7d`, `activity_slope_7d`.

### 8.4 Volatility (standard deviation)

```
mood_volatility_14d = std(mood_daily over 14d)
```

**Null if:** fewer than 5 non-null points.

**Example:**

```
mood series: [4.0, 4.2, 3.8, 4.1, 2.0, 4.3, 4.0]  → std ≈ 0.72 (volatile)
mood series: [4.0, 4.1, 3.9, 4.0, 4.1, 3.9, 4.0]  → std ≈ 0.08 (stable)
```

### 8.5 Delta vs baseline (30-day)

**sleep_delta_30d:**

```
sleep_avg_7d_now = mean(sleep last 7 days ending D)
sleep_avg_7d_baseline = mean(sleep on days D-37 .. D-30)  # 7-day block 30 days ago
sleep_delta_30d = sleep_avg_7d_now − sleep_avg_7d_baseline
```

**Null if:** `days_active < 30`.

**Example:**

```
sleep_avg_7d_now = 6.6h
sleep_avg_7d_baseline = 6.2h
sleep_delta_30d = +0.4h  (improving vs personal baseline)
```

**engagement_delta_30d:** same pattern on `engagement_rate_7d`.

**core_om_delta_30d:**

```
core_om_delta_30d = core_om_total_normalized(D) − core_om_total_normalized(D−30)
```

Negative delta = improvement (lower distress).

### 8.6 Rates

**engagement_rate_7d:**

```
engagement_rate_7d = count(days where engagement_daily=1 in last 7d) / 7
```

**Example:** active 5 of 7 days → `0.714`.

**therapy_attendance_rate_30d:**

```
therapy_attendance_rate_30d = attended / (attended + missed + cancelled_no_show)
```

**Example:** 8 attended, 1 missed, 1 cancelled → `8/10 = 0.80`.

**Null if:** no sessions scheduled in 30d.

### 8.7 Count features

**sleep_persistence_low_days:**

```
count(days in last 14d where sleep_hours_daily < 6)
```

**Example:** 2 nights below 6h → `2`.

### 8.8 Sleep consistency (for L3 trend)

**sleep_duration_variance_14d:**

```
variance(sleep_hours_daily over last 14 non-null nights)
```

**bedtime_variance_14d:**

```
Parse bedtime_local to minutes-from-midnight; std dev over 14d
```

**Example:**

| Night | bedtime | sleep_h |
|-------|---------|---------|
| Mon–Fri | 23:15 ± 10 min | 7.0 ± 0.2 |
| Sat–Sun | 01:30 | 8.5 |

Low duration variance but **high bedtime variance** → Sleep Consistency trend penalized.

### 8.9 Resting HR relative

**Formula:**

```
hr_7d_mean = mean(resting_hr_daily last 7d)
hr_30d_baseline = mean(resting_hr_daily on D-37..D-30)
resting_hr_relative = (hr_7d_mean − hr_30d_baseline) / hr_30d_baseline
```

**Null if:** `days_active < 30` OR `system_type = 0` OR no wearable.

**Example:**

```
hr_7d_mean = 62, hr_30d_baseline = 64
resting_hr_relative = (62−64)/64 = −0.031  (favorable)
```

### 8.10 Clinical latest-value

**core_om_wellbeing / problems / functioning / risk:**

```
Latest assessment_completed where instrument=CORE-OM and occurred_at ≤ D
Use subscale normalized values from payload
```

**gad7_normalized_latest:**

```
Latest GAD-7 within 90d lookback from D
gad7_normalized_latest = total_score / 21
```

**Example:**

```
CORE-OM on Jan 1: functioning.normalized = 0.72 → still latest on Jan 14
GAD-7 on Jan 1: score 9 → gad7_normalized_latest = 0.43
```

### 8.11 Journaling concern

**journaling_concern_score_7d:**

```
mean(journal_concern_score from NLP worker over last 7d with ≥1 entry)
```

**Null if:** no journal NLP scores in 7d.

---

## 9. Derived flags & cross-domain features

### 9.1 withdrawal_flag

```
withdrawal_flag = 1 if engagement_rate_7d < 0.25 else 0
```

**Example:** 1 active day in 7 → rate = 0.14 → flag = 1.

### 9.2 sleep_mood_coupled_decline

```
sleep_mood_coupled_decline = 1 if sleep_delta_30d < -1.5 AND mood_slope_7d < -0.3 else 0
```

**Example:**

```
sleep_delta_30d = -1.8 (worsening sleep vs baseline)
mood_slope_7d = -0.35 (declining mood)
→ flag = 1  (pattern card: coupled decline)
```

### 9.3 cortisol_flag (v1 proxy — closed)

No direct cortisol ingest in v1. Derive from staging:

```
cortisol_flag = 1 if ANY of:
  - stress_elevation_detected = true on ≥2 days in last 7d (wearable stress API)
  - resting_hr_relative > 0.10 AND mood_volatility_14d > 0.6
  - self_report stress item on GAD-7 item 3 elevated (optional v1.1)
else 0
```

**Example (HR + volatility proxy):**

```
resting_hr_relative = 0.12
mood_volatility_14d = 0.65
→ cortisol_flag = 1
```

**Web-only user:** use volatility + engagement decline only; document reduced precision in L3.

### 9.4 homework_completion_rate_7d (optional, feeds L3 Motivation trend)

```
homework_completed_count / homework_assigned_count over 7d from therapy events
```

---

## 10. Meta features: maturity & completeness

### 10.1 days_active

```
days_active = (as_of_date − registration_local_date).days + 1
```

From `raw.users.registration_date` + user timezone.

**Example:** registered Dec 1, as_of Jan 14 → `45 days`.

### 10.2 data_maturity_stage

| Stage | Condition |
|-------|-----------|
| `cold_start` | `days_active ≤ 7` |
| `early` | `8 ≤ days_active ≤ 30` |
| `full` | `days_active > 30` |

### 10.3 data_completeness_score

```
required = feature set for current maturity stage (see table below)
populated = count(required features where value is not null)
data_completeness_score = populated / len(required)
```

**Required features by stage:**

| Stage | Required feature count (approx) | Key gates |
|-------|--------------------------------|-----------|
| cold_start | 8 | mood, engagement, registration meta |
| early | 22 | + slopes, sleep, clinical if available |
| full | 28 | + 30d deltas, HR relative, flags |

**Example (full stage, wearable user):**

```
28 required, 23 populated → data_completeness_score = 0.82
```

L3 maps to `confidence_tier` (see CRS / ENGINE-POC L3 §10).

---

## 11. L0 → L2 column lineage (full matrix)

| L2 column | L0 / staging source | Computed in |
|-----------|---------------------|-------------|
| `mood_avg_14d` | `staging.mood_scores` | L2 |
| `mood_slope_7d` | `staging.mood_scores` | L2 |
| `mood_volatility_14d` | `staging.mood_scores` | L2 |
| `motivation_avg_14d` | `staging.motivation_scores` | L2 |
| `confidence_avg_14d` | `staging.confidence_scores` | L2 |
| `engagement_rate_7d` | `app_sessions`, `tasks_completed` | L2 |
| `engagement_slope_7d` | derived daily engagement series | L2 |
| `engagement_delta_30d` | engagement rate now vs D−30 | L2 |
| `sleep_avg_7d` | `staging.sleep_hours` | L2 |
| `sleep_delta_30d` | sleep 7d blocks now vs baseline | L2 |
| `sleep_slope_7d` | `staging.sleep_hours` | L2 |
| `sleep_persistence_low_days` | `staging.sleep_hours` | L2 |
| `sleep_duration_variance_14d` | `staging.sleep_hours` | L2 |
| `bedtime_variance_14d` | `staging.bedtime_local` | L2 |
| `resting_hr_relative` | `staging.resting_hr_bpm` | L2 |
| `activity_slope_7d` | `staging.active_minutes` | L2 |
| `therapy_attendance_rate_30d` | attended / missed / scheduled | L2 |
| `core_om_*` | `raw.assessments` | L2 |
| `gad7_normalized_latest` | `raw.assessments` | L2 |
| `journaling_concern_score_7d` | NLP → `journal_concern_scores` | L2 |
| `cortisol_flag` | stress API + HR + volatility | L2 |
| `withdrawal_flag` | `engagement_rate_7d` | L2 |
| `sleep_mood_coupled_decline` | sleep_delta + mood_slope | L2 |
| `days_active` | `raw.users` | L2 |
| `system_type` | `raw.users` | L0/L2 passthrough |
| `data_completeness_score` | all above | L2 |
| `composite_risk_percentile` | cohort job (optional) | L2 v1.1 |

---

## 12. Cold start, null handling, and imputation

### 12.1 Null policy

| Condition | L2 output | Missing flag |
|-----------|-----------|--------------|
| Insufficient window points | `null` | `{feature}_missing = 1` |
| Web-only, wearable feature | `null` | `{feature}_missing = 1` |
| No assessment ever | clinical `null` | `1` |
| `days_active < 30` for 30d deltas | `null` | `1` |

**L2 never imputes cohort priors** — that is L3's job for scoring display.

### 12.2 Example — cold start user (day 5)

```json
{
  "user_id": "U001",
  "as_of_date": "2025-01-05",
  "days_active": 5,
  "data_maturity_stage": "cold_start",
  "mood_avg_14d": null,
  "mood_avg_14d_missing": 1,
  "engagement_rate_7d": 0.57,
  "sleep_avg_7d": null,
  "data_completeness_score": 0.35
}
```

### 12.3 ML training note

For ML labels at T+30, features at T must use only data ≤ T. L2 backfill jobs must be **point-in-time safe**.

---

## 13. Batch pipeline & scheduling

### 13.1 Pipeline steps

```
1. Wait for L0 watermark (staging complete for D)
2. Load staging.user_daily_activity for user cohort (D-45 .. D)  # history for 30d deltas
3. Load raw.assessments latest-as-of D
4. Load raw.users dimension
5. Compute daily series per user
6. Compute window features at as_of_date = D
7. Compute flags + meta
8. Write features.user_features_daily partition D
9. Emit row count + null rate metrics
```

### 13.2 Incremental recompute (late data)

When L0 backfills date `D−k`:

```
Re-run L2 for dates (D−k) .. D for affected users
Trigger L3 refresh if k ≤ 7
```

### 13.3 Idempotency

Re-running L2 for same `(user_id, as_of_date, feature_version)` **overwrites** partition row (deterministic replace, not append).

---

## 14. Quality assurance & backtesting

### 14.1 CI checks

| Check | Pass criteria |
|-------|---------------|
| Column contract | Export ⊆ registry; required v1 columns present |
| Alias rejection | No `avg_mood_14d` in output |
| Determinism | Same input → same output (unit tests) |
| PIT safety | Feature at T excludes events after T |
| Scale bounds | mood in [0,5], engagement in [0,1] |

### 14.2 Backtest example

```
Golden user U004 from Engine-POC-Sample-Dataset.xlsx
Recompute L2 from synthetic staging
Assert mood_avg_14d within ±0.01 of expected
```

### 14.3 Monitoring

| Metric | Alert |
|--------|-------|
| L2 job duration p95 | > 45 min |
| Null rate spike (sleep_avg_7d) | > 15% WoW |
| Feature row count vs active users | < 95% |
| mood_avg_14d out of [0,5] | any row → pipeline halt |

---

## 15. End-to-end walkthroughs

### 15.1 Walkthrough A — Full user (matches ingestion demo)

**Input:** 14 days staging for user 1001 ending Jan 14 (from L0 demo).

**L2 output (selected):**

| Feature | Value |
|---------|-------|
| mood_avg_14d | 4.05 |
| mood_slope_7d | 0.08 |
| sleep_avg_7d | 6.6 |
| engagement_rate_7d | 0.71 |
| therapy_attendance_rate_30d | 0.80 |
| cortisol_flag | 0 |
| data_completeness_score | 0.82 |

**Downstream:** L3 produces CRS ≈ 81.2 (v2) using these features in ML models.

### 15.2 Walkthrough B — Web-only user

```json
{
  "system_type": 0,
  "sleep_avg_7d": null,
  "resting_hr_relative": null,
  "mood_avg_14d": 3.9,
  "engagement_rate_7d": 0.43,
  "cortisol_flag": 0,
  "data_completeness_score": 0.55
}
```

L3 excludes biological inputs; Stress Load uses proxy weights.

### 15.3 Walkthrough C — Coupled decline pattern

```
sleep_delta_30d = -1.8
mood_slope_7d = -0.35
→ sleep_mood_coupled_decline = 1
```

L4 pattern engine fires `sleep_mood_coupled_decline` rule → Risk Watch card.

---

## 16. Implementation roadmap

| Phase | Deliverable | Validates |
|-------|-------------|-----------|
| **1** | Daily series builder + averages/slopes | mood, sleep, engagement |
| **2** | 30d deltas + HR relative | maturity gates |
| **3** | Clinical latest + flags | CORE-OM, cortisol proxy |
| **4** | Completeness + CI contract tests | Part 8 checklist |
| **5** | Cohort percentiles (optional) | therapist views |
| **6** | Point-in-time backfill for ML | label generation |

**Tooling:**

```bash
python scripts/run_feature_pipeline_demo.py
python scripts/validate_dataset_columns.py Engine-POC-Sample-Dataset.xlsx
```

---

## 17. Appendices

### Appendix A — OLS slope reference implementation

See [features/compute.py](./features/compute.py).

### Appendix B — Related documents

| Document | Role |
|----------|------|
| [Data-Ingestion-Layer-Production-Spec.md](./Data-Ingestion-Layer-Production-Spec.md) | Upstream L0 |
| [CRS-Calculation-and-Trends-Production-Spec.md](./CRS-Calculation-and-Trends-Production-Spec.md) | Downstream L3 |
| [Engine-Architecture-Index.md](./Engine-Architecture-Index.md) | Full stack index |
| [ENGINE-POC-COMPLETE-DOCUMENTATION.md](./ENGINE-POC-COMPLETE-DOCUMENTATION.md) | POC Part 4–5, Part 8 checklist |

### Appendix C — Glossary

| Term | Definition |
|------|------------|
| **as_of_date** | Feature computation date (point-in-time) |
| **Window** | Lookback period in user-local days |
| **OLS slope** | Linear trend coefficient over window |
| **PIT** | Point-in-time (no future leakage) |
| **feature_version** | Formula/config version string |

### Appendix D — Revision history

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-05 | Initial L2 production spec; mood 0–5; cortisol proxy; full lineage |

---

*L2 outputs features, not scores. CRS and pillars are computed in L3.*
