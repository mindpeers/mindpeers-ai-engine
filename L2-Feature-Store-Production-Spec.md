# L2 Feature Store — Production Specification

**Version:** 2.0.0  
**Status:** Production-ready specification (Part1-complete registry)  
**Layer:** L2 (reads L0 staging; feeds L3 Scoring + L4 ML)  
**Related docs:** [Data-Ingestion-Layer-Production-Spec.md](./Data-Ingestion-Layer-Production-Spec.md), [CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md](./CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md), [final/Engine-Part1-Full-Attribute-Binding-Spec.md](./final/Engine-Part1-Full-Attribute-Binding-Spec.md)  
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

### 7.4 v1 registry summary (`feature_v1.0.0`)

34 columns — see §7.3. Ships in **Phase 1**. Covers Part1 attributes A01–A07, A11, A13, A27–A29, A37, A43 (W1 wave).

### 7.5 Full registry v2.0.0 (`feature_v2.0.0`) — Engine Part1 complete

**Policy:** All 70 Part1 canonical attributes (binding spec A01–A70) must have a target L2 column. v1 columns are **unchanged**; v2 **adds** columns below.

**Version bump:** `feature_v1.0.0` → `feature_v2.0.0` when Phase 5 waves W2–W7 complete.

#### 7.5.1 Assessment & clinical (A01–A10)

| Canonical | Type | Window | Attr ID | Computation |
|-----------|------|--------|---------|-------------|
| `core_om_total_norm` | clinical | latest | A01 | `total_score / max_score` from latest CORE-OM |
| `core_om_functioning` | clinical | latest | A02 | subscale normalized |
| `core_om_problems` | clinical | latest | A03 | subscale normalized |
| `core_om_wellbeing` | clinical | latest | A04 | subscale normalized |
| `core_om_risk` | clinical | latest | A05 | subscale normalized |
| `core_om_delta_30d` | delta | 30d | A06 | norm_total(D) − norm_total(D−30) |
| `gad7_normalized_latest` | clinical | 90d | A07 | `total_score / 21` |
| `phq9_normalized_latest` | clinical | 90d | A08 | `total_score / 27` |
| `trauma_score_latest` | clinical | 90d | A09 | instrument-specific normalize |
| `adhd_score_latest` | clinical | 90d | A10 | ASRS normalize |

#### 7.5.2 Lifestyle & wearable (A11–A20)

| Canonical | Type | Window | Attr ID | Computation |
|-----------|------|--------|---------|-------------|
| `sleep_avg_7d` | continuous | 7d | A11 | mean sleep hours |
| `sleep_slope_7d` | slope | 7d | A11 | OLS on daily sleep |
| `sleep_duration_variance_14d` | variance | 14d | A11 | std dev sleep duration |
| `fatigue_score_7d` | continuous | 7d | A12 | mean fatigue (0–10 → 0–5) |
| `hrv_avg` | continuous | 7d | A13 | mean RMSSD or vendor metric |
| `hrv_trend` | slope | 7d | A13 | OLS on daily HRV |
| `resting_hr_avg` | continuous | 7d | A14 | mean resting HR |
| `resting_hr_trend` | slope | 7d | A14 | OLS on resting HR |
| `exercise_days_7d` | count | 7d | A15 | days with exercise_minutes > 0 |
| `exercise_minutes_7d` | continuous | 7d | A15 | sum minutes / 7 |
| `nutrition_score_7d` | continuous | 7d | A16 | mean quality score 0–5 |
| `hydration_score_7d` | continuous | 7d | A17 | mean glasses vs target |
| `hunger_level_7d` | continuous | 7d | A18 | mean hunger 0–5 |
| `sun_exposure_minutes_7d` | continuous | 7d | A19 | mean minutes outdoors |
| `libido_level_14d` | continuous | 14d | A20 | mean libido 0–5 |

#### 7.5.3 Biomarkers (A21–A26)

| Canonical | Type | Window | Attr ID | Computation |
|-----------|------|--------|---------|-------------|
| `biomarker_cortisol_latest` | clinical | 90d | A21 | latest normalized vs ref range |
| `biomarker_tsh_latest` | clinical | 90d | A22 | latest normalized |
| `biomarker_glucose_latest` | clinical | 90d | A23 | latest fasting glucose norm |
| `biomarker_vitd_latest` | clinical | 180d | A24 | latest Vit D norm |
| `biomarker_hba1c_latest` | clinical | 365d | A25 | latest HbA1c norm |
| `weight_delta_90d` | delta | 90d | A26 | % change vs 90d ago |

#### 7.5.4 Check-ins & engagement (A27–A29, A37–A42)

| Canonical | Type | Window | Attr ID |
|-----------|------|--------|---------|
| `mood_avg_14d`, `mood_slope_7d`, `mood_volatility_14d` | various | 7–14d | A27 |
| `motivation_avg_14d`, `motivation_slope_7d` | various | 7–14d | A28 |
| `confidence_avg_14d`, `confidence_slope_7d` | various | 7–14d | A29 |
| `engagement_rate_7d`, `engagement_slope_7d` | rate/slope | 7d | A37 |
| `support_seeking_rate_30d` | rate | 30d | A38 |
| `guide_usage_rate_30d` | rate | 30d | A39 |
| `focus_session_rate_7d` | rate | 7d | A40 |
| `task_completion_rate_7d` | rate | 7d | A41 |
| `dropoff_rate_7d` | rate | 7d | A41 |
| `checkin_completion_rate_7d` | rate | 7d | A42 |
| `missed_checkin_days_7d` | count | 7d | A65 |

#### 7.5.5 Games (A30–A32)

| Canonical | Type | Window | Attr ID | Computation |
|-----------|------|--------|---------|-------------|
| `game_memory_score_7d` | continuous | 7d | A30 | mean normalized game score |
| `game_memory_slope_7d` | slope | 7d | A30 | OLS on memory scores |
| `game_connect4_score_7d` | continuous | 7d | A31 | mean normalized |
| `game_whack_score_7d` | continuous | 7d | A32 | mean normalized |
| `game_frustration_proxy` | continuous | 7d | A32 | miss rate or rage-quit proxy |

#### 7.5.6 Journal NLP (A33–A36, A56)

| Canonical | Type | Window | Attr ID |
|-----------|------|--------|---------|
| `journal_sentiment_7d` | continuous | 7d | A33 |
| `journal_stress_theme_flag` | flag | 7d | A33 |
| `journal_blank_slate_sentiment_7d` | continuous | 7d | A34 |
| `journal_letter_self_sentiment_7d` | continuous | 7d | A35 |
| `journal_gratitude_sentiment_7d` | continuous | 7d | A36 |
| `form_self_talk_score` | continuous | 30d | A56 | NLP + form composite |

#### 7.5.7 Therapy & therapist (A43, A66–A70)

| Canonical | Type | Window | Attr ID |
|-----------|------|--------|---------|
| `therapy_attendance_rate_30d` | rate | 30d | A43 |
| `therapy_missed_rate_30d` | rate | 30d | A66 |
| `days_since_last_session` | count | — | A67 |
| `therapist_availability_score` | continuous | latest | A68 |
| `therapy_affordability_score` | continuous | latest | A69 |
| `therapist_match_score` | continuous | latest | A70 |

#### 7.5.8 Forms / intake (A44–A64)

All normalized 0–1 or 0–100 at L2 boundary. Source: latest `intake_form_submitted` within lookback (default 90d) or rolling if form supports updates.

| Canonical | Attr ID | Part1 form field |
|-----------|---------|------------------|
| `form_therapy_intent_score` | A44 | therapy intent |
| `form_primary_concern_severity` | A45 | primary concern |
| `form_concern_nlp_severity` | A46 | free-text concern NLP |
| `form_work_stress_score` | A47 | work-stress pattern |
| `form_routine_disruption_flag` | A48 | routine disruption |
| `form_checkin_burden_score` | A49 | check-in completion burden |
| `form_overthinking_score` | A50 | overthinking themes |
| `form_decision_fatigue_score` | A51 | decision fatigue |
| `form_brain_fog_score` | A52 | brain fog |
| `form_work_pressure_score` | A53 | work-pressure |
| `form_emotional_triggers_score` | A54 | emotional triggers |
| `form_relationship_stress_score` | A55 | relationship patterns |
| `form_crisis_marker_flag` | A57 | crisis/risk markers |
| `form_coping_improvement_score` | A58 | pattern improvement |
| `form_coping_score` | A59 | coping behaviour |
| `form_trigger_reduction_score` | A60 | trigger reduction |
| `form_burnout_score` | A61 | burnout patterns |
| `form_work_functioning_score` | A62 | work functioning |
| `form_routine_difficulty_score` | A63 | daily routine difficulty |
| `form_overwhelm_score` | A64 | self-reported overwhelm |

#### 7.5.9 Meta & flags (unchanged from v1)

`data_completeness_score`, `days_active`, `system_type`, `withdrawal_flag`, `sleep_mood_coupled_decline`, `cortisol_flag` — see §7.3.

#### 7.5.10 Column count summary

| Version | New columns | Cumulative | Part1 attrs covered |
|---------|-------------|------------|---------------------|
| v1.0.0 | 34 | 34 | 18 (W1) |
| v2.0.0 | +52 | **86** | **70 (100%)** |

Full attribute ID cross-reference: [Appendix E](#appendix-e--part1-attribute--l2-column-matrix).

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

**Scope:** All **86** columns at `feature_v2.0.0` (34 v1 + 52 v2 additive). L0 event specs: [Data Ingestion Appendix F](./Data-Ingestion-Layer-Production-Spec.md#appendix-f--v11-event-specifications-engine-part1-complete). Attribute binding: [Appendix E](#appendix-e--part1-attribute--l2-column-matrix).

**Legend:** `staging.*` = `staging.user_daily_activity` daily rollup unless noted.

### 11.1 v1 core (Phase 1 — W1 attributes)

| L2 column | L0 event(s) | Staging / raw source | Computed in |
|-----------|-------------|----------------------|-------------|
| `mood_avg_14d` | `mood_checkin` | `mood_scores[]` | L2 |
| `mood_slope_7d` | `mood_checkin` | `mood_scores[]` | L2 |
| `mood_volatility_14d` | `mood_checkin` | `mood_scores[]` | L2 |
| `mood_delta_30d` | `mood_checkin` | `mood_scores[]` | L2 |
| `motivation_avg_14d` | `motivation_checkin` | `motivation_scores[]` | L2 |
| `motivation_slope_7d` | `motivation_checkin` | `motivation_scores[]` | L2 |
| `confidence_avg_14d` | `confidence_checkin` | `confidence_scores[]` | L2 |
| `confidence_slope_7d` | `confidence_checkin` | `confidence_scores[]` | L2 |
| `engagement_rate_7d` | `app_session` | `app_sessions`, `tasks_completed` | L2 |
| `engagement_slope_7d` | `app_session` | derived `engagement_daily` | L2 |
| `engagement_delta_30d` | `app_session` | engagement rate now vs D−30 | L2 |
| `sleep_avg_7d` | `sleep_session` | `sleep_hours` | L2 |
| `sleep_delta_30d` | `sleep_session` | `sleep_hours` (30d baseline) | L2 |
| `sleep_slope_7d` | `sleep_session` | `sleep_hours` | L2 |
| `sleep_persistence_low_days` | `sleep_session` | `sleep_hours` | L2 |
| `sleep_duration_variance_14d` | `sleep_session` | `sleep_hours` | L2 |
| `bedtime_variance_14d` | `sleep_session` | `bedtime_local` | L2 |
| `resting_hr_relative` | `heart_rate_daily` | `resting_hr_bpm` | L2 |
| `activity_slope_7d` | `activity_daily` | `active_minutes` | L2 |
| `therapy_attendance_rate_30d` | `session_attended`, `session_missed`, `session_scheduled` | `therapy_attended`, `therapy_missed`, `therapy_scheduled` | L2 |
| `core_om_wellbeing` | `assessment_completed` | `raw.assessments` (CORE-OM) | L2 |
| `core_om_problems` | `assessment_completed` | `raw.assessments` (CORE-OM) | L2 |
| `core_om_functioning` | `assessment_completed` | `raw.assessments` (CORE-OM) | L2 |
| `core_om_risk` | `assessment_completed` | `raw.assessments` (CORE-OM) | L2 |
| `core_om_delta_30d` | `assessment_completed` | `raw.assessments` (CORE-OM) | L2 |
| `gad7_normalized_latest` | `assessment_completed` | `raw.assessments` (GAD-7) | L2 |
| `journaling_concern_score_7d` | `journal_entry`, `journal_features_computed` | `journal_concern_scores[]` | L2 |
| `cortisol_flag` | `heart_rate_daily`, stress API | HR + mood volatility proxy | L2 |
| `withdrawal_flag` | `app_session` | `engagement_rate_7d` (derived) | L2 |
| `sleep_mood_coupled_decline` | `sleep_session`, `mood_checkin` | `sleep_delta_30d` + `mood_slope_7d` | L2 |
| `days_active` | `user_registered`, all events | `raw.users` + first activity | L2 |
| `system_type` | `user_profile_updated` | `raw.users.system_type` | L0/L2 passthrough |
| `data_completeness_score` | all above | coverage over registry | L2 |
| `composite_risk_percentile` | cohort job | optional v1.1 | L2 |

### 11.2 v2 additive — assessment & clinical (A01–A10)

| L2 column | L0 event(s) | Staging / raw source | Phase |
|-----------|-------------|----------------------|-------|
| `core_om_total_norm` | `assessment_completed` | `raw.assessments` latest CORE-OM | 1 |
| `phq9_normalized_latest` | `assessment_completed` (PHQ-9) | `raw.assessments` | 5C |
| `trauma_score_latest` | `assessment_completed` (PTSD) | `raw.assessments` | 5C |
| `adhd_score_latest` | `assessment_completed` (ASRS) | `raw.assessments` | 5C |

*A02–A07 columns overlap v1 registry (`core_om_*`, `gad7_normalized_latest`, `core_om_delta_30d`).*

### 11.3 v2 additive — lifestyle & wearable (A11–A20)

| L2 column | L0 event(s) | Staging source | Phase |
|-----------|-------------|----------------|-------|
| `fatigue_score_7d` | `lifestyle_checkin` | `fatigue_level` | 5A |
| `hrv_avg` | `heart_rate_daily` | `hrv_rmssd_ms` | 1/5 |
| `hrv_trend` | `heart_rate_daily` | `hrv_rmssd_ms` | 5A |
| `resting_hr_avg` | `heart_rate_daily` | `resting_hr_bpm` | 5A |
| `resting_hr_trend` | `heart_rate_daily` | `resting_hr_bpm` | 5A |
| `exercise_days_7d` | `lifestyle_checkin` | `exercise_minutes` | 5A |
| `exercise_minutes_7d` | `lifestyle_checkin` | `exercise_minutes` | 5A |
| `nutrition_score_7d` | `lifestyle_checkin` | `nutrition_quality` | 5A |
| `hydration_score_7d` | `lifestyle_checkin` | `hydration_glasses` | 5A |
| `hunger_level_7d` | `lifestyle_checkin` | `hunger_level` | 5A |
| `sun_exposure_minutes_7d` | `lifestyle_checkin` | `sun_minutes` | 5A |
| `libido_level_14d` | `lifestyle_checkin` | `libido_level` | 5A |

### 11.4 v2 additive — biomarkers (A21–A26)

| L2 column | L0 event(s) | Staging / raw source | Phase |
|-----------|-------------|----------------------|-------|
| `biomarker_cortisol_latest` | `biomarker_result` | `raw.biomarkers` (cortisol) | 5C |
| `biomarker_tsh_latest` | `biomarker_result` | `raw.biomarkers` (tsh) | 5C |
| `biomarker_glucose_latest` | `biomarker_result` | `raw.biomarkers` (glucose) | 5C |
| `biomarker_vitd_latest` | `biomarker_result` | `raw.biomarkers` (vitamin_d) | 5C |
| `biomarker_hba1c_latest` | `biomarker_result` | `raw.biomarkers` (hba1c) | 5C |
| `weight_delta_90d` | `biomarker_result` | `body_weight_kg` series | 5C |

### 11.5 v2 additive — games (A30–A32)

| L2 column | L0 event(s) | Staging source | Phase |
|-----------|-------------|----------------|-------|
| `game_memory_score_7d` | `game_session_completed` (memory_game) | `game_memory_scores[]` | 5A |
| `game_memory_slope_7d` | `game_session_completed` (memory_game) | `game_memory_scores[]` | 5A |
| `game_connect4_score_7d` | `game_session_completed` (connect_four) | `game_connect4_scores[]` | 5A |
| `game_whack_score_7d` | `game_session_completed` (whack_a_mole) | `game_whack_scores[]` | 5A |
| `game_frustration_proxy` | `game_session_completed` | `rage_quit` / miss rate | 5A |

### 11.6 v2 additive — journal NLP (A33–A36, A56)

| L2 column | L0 event(s) | Staging source | Phase |
|-----------|-------------|----------------|-------|
| `journal_sentiment_7d` | `journal_features_computed` | `journal_sentiment_scores[]` | 5D |
| `journal_stress_theme_flag` | `journal_features_computed` | `stress_theme_detected` | 5D |
| `journal_blank_slate_sentiment_7d` | `journal_entry` (blank_slate) + NLP | `journal_blank_sentiment[]` | 5D |
| `journal_letter_self_sentiment_7d` | `journal_entry` (letter_to_self) + NLP | `journal_letter_sentiment[]` | 5D |
| `journal_gratitude_sentiment_7d` | `journal_entry` (gratitude) + NLP | `journal_gratitude_sentiment[]` | 5D |
| `form_self_talk_score` | `intake_form_submitted`, NLP worker | `form_self_talk_score` | 5B/5D |

### 11.7 v2 additive — engagement & check-ins (A38–A42, A65)

| L2 column | L0 event(s) | Staging source | Phase |
|-----------|-------------|----------------|-------|
| `support_seeking_rate_30d` | `app_session`, `content_viewed` | `support_seek_events` | 5D |
| `guide_usage_rate_30d` | `content_viewed` (guides) | `guide_views` | 5D |
| `focus_session_rate_7d` | `app_session` (focus mode) | `focus_sessions` | 5D |
| `task_completion_rate_7d` | `app_session` | `tasks_completed` / `tasks_started` | 5D |
| `dropoff_rate_7d` | `app_session` | `dropoff_events` | 5D |
| `checkin_completion_rate_7d` | `mood_checkin`, `motivation_checkin`, `confidence_checkin` | expected vs actual check-ins | 5D |
| `missed_checkin_days_7d` | check-in events | `missed_checkin_flag` | 5D |

### 11.8 v2 additive — therapy (A43, A66–A67)

| L2 column | L0 event(s) | Staging source | Phase |
|-----------|-------------|----------------|-------|
| `therapy_missed_rate_30d` | `session_missed` | `therapy_missed` | 5E |
| `days_since_last_session` | `session_attended` | `last_session_date` | 5E |

### 11.9 v2 additive — therapist sheet (A68–A70)

| L2 column | L0 event(s) | Staging / raw source | Phase |
|-----------|-------------|----------------------|-------|
| `therapist_availability_score` | `therapist_profile_sync` | `raw.therapist_profiles.availability_score` | 5E |
| `therapy_affordability_score` | `therapist_profile_sync` | `raw.therapist_profiles.affordability_score` | 5E |
| `therapist_match_score` | `therapist_profile_sync` | `raw.therapist_profiles.match_score` | 5E |

### 11.10 v2 additive — intake forms (A44–A64)

All sourced from latest `intake_form_submitted` within 90d lookback → `raw.intake_forms` → L2 latest-value normalize.

| L2 column | Form field (Part1) | Attr |
|-----------|-------------------|------|
| `form_therapy_intent_score` | therapy intent | A44 |
| `form_primary_concern_severity` | primary concern | A45 |
| `form_concern_nlp_severity` | free-text concern NLP | A46 |
| `form_work_stress_score` | work-stress pattern | A47 |
| `form_routine_disruption_flag` | routine disruption | A48 |
| `form_checkin_burden_score` | check-in burden | A49 |
| `form_overthinking_score` | overthinking | A50 |
| `form_decision_fatigue_score` | decision fatigue | A51 |
| `form_brain_fog_score` | brain fog | A52 |
| `form_work_pressure_score` | work pressure | A53 |
| `form_emotional_triggers_score` | emotional triggers | A54 |
| `form_relationship_stress_score` | relationship stress | A55 |
| `form_crisis_marker_flag` | crisis marker | A57 |
| `form_coping_improvement_score` | coping improvement | A58 |
| `form_coping_score` | coping behaviour | A59 |
| `form_trigger_reduction_score` | trigger reduction | A60 |
| `form_burnout_score` | burnout | A61 |
| `form_work_functioning_score` | work functioning | A62 |
| `form_routine_difficulty_score` | routine difficulty | A63 |
| `form_overwhelm_score` | overwhelm | A64 |

**Phase:** 5B for all form columns.

### 11.11 Lineage verification checklist

| Check | Pass criteria |
|-------|---------------|
| Part1 coverage | Every A01–A70 maps to ≥1 L2 column (Appendix E) |
| L0 traceability | Every v2 column maps to ≥1 L0 `event_type` (Data Ingestion F.9) |
| PIT safety | Latest-value features use `occurred_at ≤ as_of_date` |
| Null policy | Missing staging → `null` + `{col}_missing` flag (§12) |

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
| 2.0.0 | 2026-06-05 | §7.5 full Part1 registry (86 cols); Appendix E attribute matrix; §11 full L0→L2 lineage (86 cols) |
| 1.0.0 | 2026-06-05 | Initial L2 production spec; mood 0–5; cortisol proxy; full lineage |

### Appendix E — Part1 attribute → L2 column matrix

Authoritative binding: [final/Engine-Part1-Full-Attribute-Binding-Spec.md](./final/Engine-Part1-Full-Attribute-Binding-Spec.md)

| Attr ID | Part1 name | Primary L2 column(s) | State scores | Trends |
|---------|------------|----------------------|--------------|--------|
| A01 | CORE-OM Overall | `core_om_total_norm` | CRS, Capacity | Stress, Recovery |
| A02 | CORE-OM Functioning | `core_om_functioning` | Clarity, Capacity, Resilience | Cognitive |
| A03 | CORE-OM Problems | `core_om_problems` | CRS, Clarity, Balance, Capacity | Stress |
| A04 | CORE-OM Wellbeing | `core_om_wellbeing` | CRS, Balance | Emotional |
| A05 | CORE-OM Risk | `core_om_risk` | All (risk cap) | — |
| A06 | CORE-OM Delta | `core_om_delta_30d` | Resilience | Recovery |
| A07 | Anxiety (GAD-7) | `gad7_normalized_latest` | CRS, Clarity, Balance | Stress, Emotional |
| A08 | Depression (PHQ-9) | `phq9_normalized_latest` | CRS, Balance | Stress, Emotional |
| A09 | Trauma | `trauma_score_latest` | CRS, Balance | Stress, Emotional |
| A10 | ADHD (ASRS) | `adhd_score_latest` | Clarity | Cognitive |
| A11 | Sleep | `sleep_avg_7d`, `sleep_slope_7d`, `sleep_duration_variance_14d` | All | Recovery, Sleep, Energy |
| A12 | Fatigue | `fatigue_score_7d` | CRS, Clarity, Balance, Capacity | Recovery⁻, Energy, Cognitive⁻ |
| A13 | HRV | `hrv_avg`, `hrv_trend` | CRS, Clarity, Resilience, Capacity | Recovery, Stress |
| A14 | Pulse | `resting_hr_avg`, `resting_hr_trend` | CRS, Clarity, Capacity | Stress |
| A15 | Exercise | `exercise_days_7d`, `exercise_minutes_7d` | CRS, Resilience, Capacity | Recovery, Energy |
| A16 | Nutrition | `nutrition_score_7d` | CRS, Clarity, Resilience, Capacity | Energy |
| A17 | Hydration | `hydration_score_7d` | CRS, Clarity, Resilience, Capacity | Energy |
| A18 | Hunger | `hunger_level_7d` | Clarity, Capacity | Energy |
| A19 | Sun Exposure | `sun_exposure_minutes_7d` | Resilience | Recovery |
| A20 | Libido | `libido_level_14d` | Balance | Emotional |
| A21 | Cortisol | `biomarker_cortisol_latest` | CRS, Balance, Resilience | Stress |
| A22 | Thyroid/TSH | `biomarker_tsh_latest` | CRS, Clarity, Balance, Capacity | Stress, Emotional |
| A23 | Blood Sugar | `biomarker_glucose_latest` | CRS, Clarity, Balance, Capacity | Stress, Energy |
| A24 | Vitamin D | `biomarker_vitd_latest` | Clarity, Resilience | Recovery |
| A25 | HbA1c | `biomarker_hba1c_latest` | Capacity | Energy |
| A26 | Weight Change | `weight_delta_90d` | Capacity | Energy |
| A27 | Mood | `mood_avg_14d`, `mood_slope_7d`, `mood_volatility_14d` | CRS, Balance | Emotional, Stress |
| A28 | Motivation | `motivation_avg_14d`, `motivation_slope_7d` | CRS, Clarity, Resilience, Capacity | Motivation, Energy |
| A29 | Confidence | `confidence_avg_14d`, `confidence_slope_7d` | CRS, Balance, Capacity | Emotional, Motivation |
| A30 | Memory Game | `game_memory_score_7d`, `game_memory_slope_7d` | CRS, Clarity | Cognitive |
| A31 | Connect Four | `game_connect4_score_7d` | CRS, Clarity | Cognitive |
| A32 | Whack A Mole | `game_whack_score_7d`, `game_frustration_proxy` | Balance | Emotional |
| A33 | Journal tone/themes | `journal_sentiment_7d`, `journal_stress_theme_flag` | CRS, Balance | Emotional |
| A34 | Blank Slate Journal | `journal_blank_slate_sentiment_7d` | Balance | Emotional |
| A35 | Letter to Self | `journal_letter_self_sentiment_7d` | Balance | Emotional |
| A36 | Gratitude Journal | `journal_gratitude_sentiment_7d` | Balance, Resilience | Emotional |
| A37 | App engagement | `engagement_rate_7d`, `engagement_slope_7d` | CRS, Resilience, Capacity | Motivation, Energy |
| A38 | Support-seeking | `support_seeking_rate_30d` | Resilience | Motivation |
| A39 | Guides usage | `guide_usage_rate_30d` | Resilience | Motivation |
| A40 | Focus behaviour | `focus_session_rate_7d` | Clarity, Capacity | Cognitive |
| A41 | Completion/drop-off | `task_completion_rate_7d`, `dropoff_rate_7d` | Clarity | Cognitive |
| A42 | Check-in drop-off | `checkin_completion_rate_7d` | Balance | Motivation |
| A43 | Therapy attendance | `therapy_attendance_rate_30d` | CRS, Capacity | Motivation |
| A44–A64 | Forms (21 fields) | `form_*` columns §7.5.8 | Per pillar §3 binding spec | Motivation, Emotional, Cognitive |
| A65 | Missed check-ins | `missed_checkin_days_7d` | Capacity | Motivation |
| A66 | Session missed | `therapy_missed_rate_30d` | CRS, Capacity | Motivation |
| A67 | Days since session | `days_since_last_session` | Capacity | Motivation |
| A68–A70 | Therapist sheet | `therapist_*_score` | All (therapist block) | Engagement |

---

*L2 outputs features, not scores. CRS and pillars are computed in L3.*
