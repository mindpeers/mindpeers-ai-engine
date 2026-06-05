# Data Ingestion Layer — Production Specification

**Version:** 1.0.0  
**Status:** Production-ready specification  
**Layer:** L0 (feeds L2 Feature Store)  
**Related docs:** [Engine-Architecture-Index.md](./Engine-Architecture-Index.md), [CRS-Calculation-and-Trends-Production-Spec.md](./CRS-Calculation-and-Trends-Production-Spec.md), [ENGINE-POC-COMPLETE-DOCUMENTATION.md](./ENGINE-POC-COMPLETE-DOCUMENTATION.md)  
**Implementation:** [schemas/ingestion/](./schemas/ingestion/), [ingestion/](./ingestion/), [scripts/run_ingestion_demo.py](./scripts/run_ingestion_demo.py)  
**Audience:** Engineering, Data Platform, Security, Clinical Ops  
**Last updated:** 2026-06-05

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Position in the architecture](#2-position-in-the-architecture)
3. [Design principles](#3-design-principles)
4. [Source systems inventory](#4-source-systems-inventory)
5. [Ingestion modes and schedules](#5-ingestion-modes-and-schedules)
6. [Raw event schemas (by source)](#6-raw-event-schemas-by-source)
7. [Canonical raw data model](#7-canonical-raw-data-model)
8. [Validation, quality gates, and quarantine](#8-validation-quality-gates-and-quarantine)
9. [Idempotency, deduplication, and ordering](#9-idempotency-deduplication-and-ordering)
10. [Channel handling: full vs web-only](#10-channel-handling-full-vs-web-only)
11. [Staging → L2 handoff](#11-staging--l2-handoff)
12. [Label event ingestion (ML training)](#12-label-event-ingestion-ml-training)
13. [Security, privacy, and compliance](#13-security-privacy-and-compliance)
14. [Failure handling and recovery](#14-failure-handling-and-recovery)
15. [Observability and SLAs](#15-observability-and-slas)
16. [End-to-end walkthroughs](#16-end-to-end-walkthroughs)
17. [Implementation roadmap](#17-implementation-roadmap)
18. [Appendices](#18-appendices)

---

## 1. Executive summary

### 1.1 Purpose

The **Data Ingestion Layer (L0)** collects, validates, normalizes, and persists **raw and semi-structured events** from all MindPeers product surfaces into a canonical staging zone. L2 (Feature Store) reads from staging — it never talks directly to source APIs.

Without a disciplined ingestion layer:
- Feature computation becomes inconsistent across environments
- Wearable gaps silently break biological scores
- ML label generation lacks auditable source events
- CRS and trend metrics inherit stale or duplicate data

### 1.2 What ingestion delivers

| Output | Consumer | Example |
|--------|----------|---------|
| Validated raw events | L2 feature pipelines | `raw.mood_checkin` rows |
| User channel metadata | L2, L3 | `system_type = 0` (web-only) |
| Assessment snapshots | L2 clinical features | CORE-OM subscales |
| Therapy session facts | L2 behavioral features | attendance, homework |
| Wearable daily summaries | L2 biological features | sleep, HR, HRV |
| Outcome / label events | ML training pipelines | dropout, CORE-OM delta |

### 1.3 One-line data flow

```
Source systems → Connectors → Validate → Dedupe → raw.* tables → staging.* → L2 Feature Store → L3 Scoring → L1 Engine
```

### 1.4 Worked example — one user, one day

**User 1001 on 2025-01-14** generates these ingested events:

| Time (local) | Source | Event type | Raw record ID |
|--------------|--------|------------|---------------|
| 07:12 | Wearable sync | `sleep_session` | `evt_sleep_88421` |
| 08:45 | App | `mood_checkin` | `evt_mood_99102` |
| 09:30 | App | `motivation_checkin` | `evt_mot_99103` |
| 14:00 | Therapy platform | `session_attended` | `evt_sess_44201` |
| 22:10 | App | `journal_entry` | `evt_jrn_99115` |

By **02:00 UTC on 2025-01-15**, L2 reads staging and produces:

```json
{
  "user_id": "1001",
  "as_of_date": "2025-01-14",
  "sleep_avg_7d": 6.6,
  "mood_avg_14d": 5.8,
  "engagement_rate_7d": 0.71,
  "therapy_attendance_rate_30d": 0.80
}
```

---

## 2. Position in the architecture

### 2.1 Layer stack

```
┌─────────────────────────────────────────────────────────────────────┐
│ L1 — Product Engine (dashboard, patterns, recommendations)          │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↑ reads snapshot
┌───────────────────────────────▼─────────────────────────────────────┐
│ L3 — Scoring Service (CRS, pillars, trends)                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↑ reads features
┌───────────────────────────────▼─────────────────────────────────────┐
│ L2 — Feature Store (windows, slopes, flags, cohort stats)           │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↑ reads staging
┌───────────────────────────────▼─────────────────────────────────────┐
│ L0 — DATA INGESTION LAYER  ◄── THIS DOCUMENT                        │
│  Connectors • validation • raw tables • staging • lineage           │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↑
┌───────────────────────────────▼─────────────────────────────────────┐
│ SOURCE SYSTEMS                                                       │
│ Mobile app • Web • Wearables • Therapy • Assessments • CRM/Auth      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Boundaries

| Layer | Owns | Does NOT own |
|-------|------|--------------|
| **L0 Ingestion** | Event capture, schema validation, dedupe, raw persistence | Feature windows, CRS, ML inference |
| **L2 Feature Store** | Aggregations (7d/14d/30d), slopes, flags | Source API polling |
| **L3 Scoring** | Normalization to 0–100, CRS formula | Raw event repair |

### 2.3 Steady-state schedule (aligned with CRS spec)

| Job | Schedule (UTC) | Layer | Depends on |
|-----|----------------|-------|------------|
| Wearable backfill sync | Every 6h + on-demand | L0 | Vendor API |
| App event stream flush | Continuous → micro-batch 15m | L0 | Kafka/Kinesis |
| Assessment import | On submit + nightly reconcile | L0 | Assessment service |
| Therapy session sync | Hourly | L0 | Scheduling API |
| **L0 → staging finalize** | Daily 01:30 | L0 | All connectors |
| **L2 feature compute** | Daily 02:00 | L2 | L0 staging complete |
| L3 scoring | Daily 02:45 | L3 | L2 |

---

## 3. Design principles

### 3.1 Core principles

| # | Principle | Rationale | Example |
|---|-----------|-----------|---------|
| 1 | **Append-only raw log** | Audit trail for clinical and ML governance | Never UPDATE `raw.mood_checkin`; insert correction event |
| 2 | **Schema-first contracts** | Breaking changes caught in CI, not production | Avro/JSON Schema per event type |
| 3 | **Idempotent ingestion** | Retries and backfills must not duplicate | Same `event_id` → skip second write |
| 4 | **User-local timezone** | Sleep and mood align to calendar days | User in IST: mood at 11pm counts for that local date |
| 5 | **Explicit missingness** | Downstream knows *why* data is absent | `system_type=0` → no wearable rows expected |
| 6 | **Lineage on every row** | Debug feature drift in 10K RPM production | `source_system`, `ingested_at`, `connector_version` |
| 7 | **Fail closed on PII leakage** | Quarantine before warehouse | Journal text stays encrypted; only scores to L2 |

### 3.2 Anti-patterns (do not build)

| Anti-pattern | Why it fails | Correct approach |
|--------------|-------------|------------------|
| L2 polls Fitbit/Apple directly | N+1 APIs, no replay, inconsistent history | L0 connector writes `raw.wearable_daily` |
| Overwrite latest mood in place | Loses history; slopes impossible | Append check-ins; L2 aggregates |
| Ingest CRS or pillar scores | Circular; scores come from L3 | Ingest only raw events + assessments |
| Single schema for all sources | Wearable vendor fields differ wildly | Per-source schema → map to canonical |
| Block ingestion on one bad row | One corrupt journal should not stop sleep sync | Quarantine bad rows; continue batch |

---

## 4. Source systems inventory

### 4.1 Source catalog

| Source ID | System | Domain | Ingestion mode | v1 scope | Feeds L2 features |
|-----------|--------|--------|----------------|----------|-------------------|
| `app_mobile` | iOS/Android app | Behavioral, Psychological | Real-time stream | **Yes** | mood, motivation, confidence, engagement, journal |
| `app_web` | Web client | Behavioral, Psychological | Real-time stream | **Yes** | mood, engagement (no wearable) |
| `wearable_apple` | Apple HealthKit | Biological | Batch sync 6h | **Yes** (proxy v1) | sleep, HR, activity |
| `wearable_google` | Google Fit / Health Connect | Biological | Batch sync 6h | **Yes** (proxy v1) | sleep, HR, activity |
| `wearable_vendor` | Whoop / Oura / Garmin (v1.1) | Biological | Batch sync 6h | v1.1 | HRV, recovery, stress episodes |
| `therapy_platform` | Session scheduling + EHR-lite | Behavioral | Hourly API | **Yes** | attendance, homework, session notes metadata |
| `assessments` | CORE-OM, GAD-7, PHQ-9 (v1.1) | Clinical | On submit | **Yes** (CORE-OM, GAD-7) | clinical subscales |
| `auth_crm` | Registration, org, demographics | Meta | Daily + event | **Yes** | user_id, org, days_active, system_type |
| `content_engagement` | Video, worksheet, exercise views | Behavioral | Stream | Optional v1 | engagement_rate enrichment |
| `cogniart` | Cognitive tasks (future) | Cognitive | Stream | Future | clarity, cognitive momentum |
| `therapist_ratings` | Clinician observations (future) | Clinical | Form submit | Future | clarity, risk escalation |

### 4.2 Source → feature mapping (high level)

```
app_mobile ──────┬── mood_checkin ──────────► mood_avg_14d, mood_slope_7d, mood_volatility_14d
                 ├── motivation_checkin ────► motivation_avg_14d, motivation_slope_7d
                 ├── confidence_checkin ────► confidence_avg_14d, confidence_slope_7d
                 ├── app_session ───────────► engagement_rate_7d, engagement_slope_7d
                 └── journal_entry ─────────► journaling_concern_score_7d (NLP downstream)

wearable_* ──────┬── sleep_session ─────────► sleep_avg_7d, sleep_consistency, sleep_delta_30d
                 ├── heart_rate_summary ────► resting_hr_relative, hrv_avg (v1.1)
                 └── activity_summary ──────► activity_slope_7d

therapy_platform ► session_* ─────────────► therapy_attendance_rate_30d, homework_completion

assessments ─────► core_om_* , gad7_* ─────► core_om_wellbeing, gad7_normalized_latest, labels

auth_crm ────────► user_registered ────────► days_active, system_type, cohort keys
```

### 4.3 Example — source registration record

Every connector registers in config:

```json
{
  "source_id": "wearable_apple",
  "connector_version": "1.3.2",
  "event_types": ["sleep_session", "heart_rate_daily", "activity_daily"],
  "requires_oauth": true,
  "user_consent_scope": ["sleep", "heart_rate", "activity"],
  "default_sync_cadence_hours": 6,
  "schema_registry_subject": "mindpeers.raw.wearable.v1"
}
```

---

## 5. Ingestion modes and schedules

### 5.1 Mode comparison

| Mode | Latency | Use when | Example sources |
|------|---------|----------|-----------------|
| **Streaming** | Seconds–minutes | High-volume, user-initiated | mood check-in, app open |
| **Micro-batch** | 15 minutes | Moderate volume, batch efficiency | journal NLP queue |
| **Scheduled pull** | 1–6 hours | Vendor API rate limits | Apple Health sync |
| **Daily reconcile** | 24 hours | Source of truth correction | therapy attendance finalization |
| **On-demand backfill** | Manual trigger | User reconnects wearable | 90-day history import |

### 5.2 Production schedule

| Connector | Mode | Cadence | SLA (p95 lag) |
|-----------|------|---------|---------------|
| App events | Stream → 15m micro-batch | Continuous | < 5 min |
| Mood/motivation check-ins | Stream | Continuous | < 2 min |
| Wearable sync | Scheduled pull | Every 6h | < 8h |
| Therapy sessions | Scheduled pull | Hourly | < 90 min |
| Assessments | Webhook + reconcile | Immediate + daily | < 1 min submit |
| User registry | CDC stream | Continuous | < 5 min |
| Staging finalize | Batch | Daily 01:30 UTC | Complete by 01:45 |

### 5.3 Example — streaming pipeline

```
Mobile app
    │ POST /events (mood_checkin)
    ▼
API Gateway (auth, rate limit 100 req/min/user)
    ▼
Kafka topic: raw.app.events.v1
    ▼
Flink / Spark streaming (validate schema, enrich user_tz)
    ▼
raw.app_mood_checkin (Parquet / BigQuery / Postgres partition by event_date)
    ▼
[Daily 01:30] staging.user_daily_events rollup
```

---

## 6. Raw event schemas (by source)

All events share a **common envelope** plus type-specific payload.

### 6.1 Common event envelope

```json
{
  "event_id": "evt_mood_99102",
  "event_type": "mood_checkin",
  "event_version": "1.0.0",
  "source_system": "app_mobile",
  "connector_version": "2.1.0",
  "user_id": "1001",
  "organization_id": "org_42",
  "occurred_at": "2025-01-14T08:45:00+05:30",
  "occurred_at_utc": "2025-01-14T03:15:00Z",
  "local_date": "2025-01-14",
  "timezone": "Asia/Kolkata",
  "ingested_at": "2025-01-14T03:15:04Z",
  "idempotency_key": "1001:mood_checkin:2025-01-14T08:45:00+05:30",
  "payload": { }
}
```

**Field rules:**

| Field | Required | Notes |
|-------|----------|-------|
| `event_id` | Yes | UUID v4; globally unique |
| `idempotency_key` | Yes | Stable on retry from client |
| `local_date` | Yes | User calendar date for daily aggregation |
| `source_system` | Yes | From §4.1 catalog |
| `payload` | Yes | Validated per JSON Schema |

---

### 6.2 App — mood check-in

**Event type:** `mood_checkin`

```json
{
  "event_id": "evt_mood_99102",
  "event_type": "mood_checkin",
  "source_system": "app_mobile",
  "user_id": "1001",
  "local_date": "2025-01-14",
  "payload": {
    "mood_score": 5.8,
    "scale_min": 0,
    "scale_max": 10,
    "prompt_id": "daily_mood_v2",
    "optional_note_present": false
  }
}
```

**Validation rules:**

| Rule | Action on fail |
|------|----------------|
| `mood_score` ∈ [0, 10] | Quarantine |
| `scale_max` = 10 (v1 contract) | Reject or normalize |
| Max 20 check-ins per user per local_date | Dedupe keep latest; log warning |
| `user_id` exists in registry | Quarantine until user synced |

**Invalid example (quarantined):**

```json
{
  "payload": { "mood_score": 15, "scale_max": 10 }
}
```
→ `quarantine_reason: "mood_score_out_of_range"`

---

### 6.3 App — motivation and confidence check-ins

**Event types:** `motivation_checkin`, `confidence_checkin`

```json
{
  "event_type": "motivation_checkin",
  "user_id": "1001",
  "local_date": "2025-01-14",
  "payload": {
    "score": 4.0,
    "scale_min": 0,
    "scale_max": 5,
    "prompt_id": "motivation_daily_v1"
  }
}
```

**L2 mapping:** Same window semantics as mood (7d slope, 14d average). Required for trend **Motivation & Confidence Momentum** (G8).

**Example — user with sparse check-ins:**

| local_date | motivation | confidence |
|------------|------------|------------|
| Jan 10 | 4.0 | 3.5 |
| Jan 12 | 3.8 | null |
| Jan 14 | null | 4.2 |

L2 after ingestion: `motivation_avg_14d` computed from 2 points; confidence from 2 points; slopes null until ≥ 4 points in 7d.

---

### 6.4 App — engagement session

**Event type:** `app_session`

```json
{
  "event_type": "app_session",
  "user_id": "1001",
  "local_date": "2025-01-14",
  "payload": {
    "session_duration_sec": 420,
    "screens_viewed": ["home", "engine", "journal"],
    "tasks_completed": 1,
    "platform": "ios",
    "app_version": "3.2.1"
  }
}
```

**Derived for L2:**

```
engagement_rate_7d = count(distinct local_date with session or task) / 7
withdrawal_flag = 1 if engagement_rate_7d < 0.25
```

**Example — engagement loss label input:**

| Week | daily engagement scores | engagement_rate_7d |
|------|------------------------|------------------|
| Week 1 | [0.9, 0.85, 0.9, 0.88, 0.92, 0.87, 0.91] | 0.90 |
| Week 2 | [0.4, 0.35, 0.42, 0.38, 0.30, 0.28, 0.33] | 0.38 |

→ `engagement_loss_label = 1` (drop > 50% vs baseline) for ML training.

---

### 6.5 App — journal entry

**Event type:** `journal_entry`

```json
{
  "event_type": "journal_entry",
  "user_id": "1001",
  "local_date": "2025-01-14",
  "payload": {
    "entry_id": "jrn_5521",
    "word_count": 142,
    "language": "en",
    "text_encrypted_ref": "s3://encrypted-bucket/jrn_5521.enc",
    "text_processing_consent": true
  }
}
```

**Important:** Raw journal **text** does not land in the analytics warehouse. A separate NLP worker reads encrypted ref and writes:

```json
{
  "event_type": "journal_features_computed",
  "payload": {
    "entry_id": "jrn_5521",
    "sentiment_score": 0.62,
    "concern_score": 0.18,
    "coherence_score": 0.71
  }
}
```

Only `concern_score`, `coherence_score` flow to L2 (`journaling_concern_score_7d`).

---

### 6.6 Wearable — sleep session

**Event type:** `sleep_session`

```json
{
  "event_type": "sleep_session",
  "source_system": "wearable_apple",
  "user_id": "1001",
  "local_date": "2025-01-14",
  "payload": {
    "sleep_start": "2025-01-13T23:15:00+05:30",
    "sleep_end": "2025-01-14T07:00:00+05:30",
    "duration_hours": 7.25,
    "efficiency": 0.88,
    "awakenings": 2,
    "deep_sleep_min": 95,
    "rem_sleep_min": 110,
    "bedtime_local": "23:15",
    "wake_time_local": "07:00",
    "vendor_session_id": "ah_sleep_88271"
  }
}
```

**Validation:**

| Rule | Example pass | Example fail |
|------|-------------|--------------|
| `duration_hours` ∈ (0, 16] | 7.25 | 0 or 22 → quarantine |
| `sleep_end` > `sleep_start` | OK | Inverted → quarantine |
| One primary session per local_date per vendor | Second session → merge or flag nap |

**L2 outputs from 7 nights:**

```
sleep_avg_7d = mean(duration_hours) = 6.6
sleep_duration_variance = std(duration_hours) = 0.3  → Sleep Consistency trend
sleep_persistence_low_days = count(duration < 6) in 14d
```

---

### 6.7 Wearable — heart rate daily summary

**Event type:** `heart_rate_daily`

```json
{
  "event_type": "heart_rate_daily",
  "source_system": "wearable_apple",
  "user_id": "1001",
  "local_date": "2025-01-14",
  "payload": {
    "resting_hr_bpm": 62,
    "hrv_rmssd_ms": 58,
    "hrv_source": "apple_watch",
    "sample_count": 288
  }
}
```

**v1 scope (D1 phased):** `resting_hr_relative` used in L2; full HRV (`hrv_rmssd_7d`) deferred to v1.1 unless populated.

**Web-only user:** No rows ingested → L2 sets `resting_hr_relative = null`, `system_type = 0`.

---

### 6.8 Wearable — activity daily summary

**Event type:** `activity_daily`

```json
{
  "event_type": "activity_daily",
  "user_id": "1001",
  "local_date": "2025-01-14",
  "payload": {
    "steps": 8420,
    "active_minutes": 45,
    "calories_burned": 2100,
    "sedentary_minutes": 520
  }
}
```

**L2:** `activity_slope_7d = OLS_slope(active_minutes, 7d)` for Energy Rhythm and Capacity pillars.

---

### 6.9 Therapy platform — session events

**Event types:** `session_scheduled`, `session_attended`, `session_missed`, `session_cancelled`

```json
{
  "event_type": "session_attended",
  "source_system": "therapy_platform",
  "user_id": "1001",
  "occurred_at": "2025-01-14T14:00:00+05:30",
  "payload": {
    "session_id": "sess_44201",
    "therapist_id": "th_88",
    "scheduled_duration_min": 50,
    "actual_duration_min": 48,
    "modality": "video",
    "homework_assigned": true,
    "homework_completed": false
  }
}
```

**L2 computation example:**

```
therapy_attendance_rate_30d = attended / (attended + missed + cancelled_no_show)
                            = 8 / 10 = 0.80
```

---

### 6.10 Assessments — CORE-OM

**Event type:** `assessment_completed`

```json
{
  "event_type": "assessment_completed",
  "source_system": "assessments",
  "user_id": "1001",
  "occurred_at": "2025-01-01T10:00:00Z",
  "payload": {
    "instrument": "CORE-OM",
    "instrument_version": "1.1",
    "total_score": 18,
    "max_score": 40,
    "subscales": {
      "wellbeing": { "raw": 12, "normalized": 0.75 },
      "problems": { "raw": 22, "normalized": 0.28 },
      "functioning": { "raw": 15, "normalized": 0.72 },
      "risk": { "raw": 3, "normalized": 0.15 }
    },
    "assessment_id": "core_1001_20250101"
  }
}
```

**Ingestion rules:**

| Rule | Rationale |
|------|-----------|
| Store full subscales (G7) | Clarity and Emotional Balance need functioning vs wellbeing split |
| Immutable once submitted | Corrections = new `assessment_corrected` event with `supersedes_id` |
| Retain 90d history minimum | GAD-7 `gad7_normalized_latest` requires lookup window |

**Label generation (offline):** Compare `total_score` at T vs T+30d for `recovery_label` / `relapse_label` (see [CRS spec §4.3](./CRS-Calculation-and-Trends-Production-Spec.md)).

---

### 6.11 Assessments — GAD-7

```json
{
  "event_type": "assessment_completed",
  "payload": {
    "instrument": "GAD-7",
    "total_score": 9,
    "max_score": 21,
    "normalized": 0.43,
    "severity_band": "moderate"
  }
}
```

**L2:** `gad7_normalized_latest` = most recent GAD-7 within 90d, normalized 0–1.

---

### 6.12 Auth / CRM — user registry

**Event type:** `user_registered`, `user_profile_updated`

```json
{
  "event_type": "user_registered",
  "source_system": "auth_crm",
  "user_id": "1001",
  "occurred_at": "2024-12-01T09:00:00Z",
  "payload": {
    "organization_id": "org_42",
    "registration_channel": "ios_app",
    "has_wearable_connected": true,
    "system_type": 1,
    "timezone": "Asia/Kolkata",
    "age_band": "25-34",
    "program_id": "prog_standard"
  }
}
```

**`system_type` derivation:**

| Condition | system_type |
|-----------|-------------|
| Wearable connected OR native app with health permissions | `1` (full) |
| Web-only, no wearable | `0` (web-only) |

This drives L3 G15: biological features excluded when `system_type = 0`.

---

## 7. Canonical raw data model

### 7.1 Database / warehouse layout

| Schema | Table | Grain | Partition |
|--------|-------|-------|-----------|
| `raw` | `app_events` | 1 row / event | `local_date` |
| `raw` | `wearable_sleep` | 1 row / session | `local_date` |
| `raw` | `wearable_hr_daily` | 1 row / user / day | `local_date` |
| `raw` | `wearable_activity_daily` | 1 row / user / day | `local_date` |
| `raw` | `therapy_sessions` | 1 row / session | `month` |
| `raw` | `assessments` | 1 row / assessment | `month` |
| `raw` | `users` | 1 row / user (SCD2) | — |
| `staging` | `user_daily_activity` | 1 row / user / local_date | `local_date` |
| `staging` | `ingestion_watermarks` | 1 row / source / user | — |

### 7.2 Example — `raw.app_events` row (flattened)

| Column | Value |
|--------|-------|
| event_id | evt_mood_99102 |
| event_type | mood_checkin |
| user_id | 1001 |
| local_date | 2025-01-14 |
| mood_score | 5.8 |
| source_system | app_mobile |
| ingested_at | 2025-01-14T03:15:04Z |

### 7.3 Example — `staging.user_daily_activity`

Rollup produced at 01:30 UTC:

```json
{
  "user_id": "1001",
  "local_date": "2025-01-14",
  "mood_checkin_count": 1,
  "mood_scores": [5.8],
  "motivation_scores": [4.0],
  "confidence_scores": [],
  "app_sessions": 2,
  "total_session_sec": 680,
  "tasks_completed": 1,
  "sleep_hours": 7.25,
  "resting_hr_bpm": 62,
  "hrv_rmssd_ms": 58,
  "steps": 8420,
  "therapy_attended": 1,
  "journal_entries": 1,
  "has_wearable_data": true,
  "staging_built_at": "2025-01-15T01:32:00Z"
}
```

L2 reads `staging.user_daily_activity` for windowed aggregations.

---

## 8. Validation, quality gates, and quarantine

### 8.1 Validation pipeline stages

```
Event received
    → Schema validation (JSON Schema)
    → Business rules (ranges, enums)
    → Referential integrity (user exists)
    → Duplicate check (idempotency_key)
    → PII scan (journal raw text)
    → PASS → raw.*  |  FAIL → quarantine.*
```

### 8.2 Quality gate summary

| Gate | Pass rate SLA | Action on fail |
|------|--------------|----------------|
| Schema valid | > 99.5% | Quarantine + alert if < 99% |
| User exists | 100% of non-registration events | Hold in pending queue 24h |
| Mood in range | 100% | Quarantine |
| Wearable duration sane | > 99% | Quarantine outlier |
| Assessment subscales present | 100% for CORE-OM | Block assessment write; fix upstream |

### 8.3 Quarantine table schema

```json
{
  "quarantine_id": "q_99102",
  "original_event": { },
  "quarantine_reason": "mood_score_out_of_range",
  "quarantined_at": "2025-01-14T03:15:05Z",
  "retry_eligible": false,
  "review_status": "pending"
}
```

### 8.4 Data quality metrics (daily)

| Metric | Formula | Alert threshold |
|--------|---------|-----------------|
| Ingestion lag p95 | `ingested_at - occurred_at` | > 30 min (app), > 12h (wearable) |
| Quarantine rate | quarantined / total | > 0.5% |
| Duplicate rate | deduped / total | > 5% (investigate client) |
| Users with zero events 7d | count active users | > 10% WoW change |
| Wearable attach rate | users with sleep / active users | Drop > 5% |

---

## 9. Idempotency, deduplication, and ordering

### 9.1 Idempotency key format

```
{user_id}:{event_type}:{stable_business_key}
```

**Examples:**

| Event | Idempotency key |
|-------|-----------------|
| Mood check-in | `1001:mood_checkin:2025-01-14T08:45:00+05:30` |
| Sleep session | `1001:sleep_session:ah_sleep_88271` |
| Assessment | `1001:assessment_completed:core_1001_20250101` |
| Session attended | `1001:session_attended:sess_44201` |

### 9.2 Deduplication behavior

```python
def ingest(event):
    if exists(raw.events, event.idempotency_key):
        return {"status": "duplicate_skipped", "event_id": event.event_id}
    insert(raw.events, event)
    return {"status": "accepted", "event_id": event.event_id}
```

**Example — client retry:**

1. App sends mood check-in → `accepted`
2. Network timeout; app retries same payload → `duplicate_skipped`
3. Raw table still has exactly **one** row

### 9.3 Late-arriving data

Wearable sync may backfill sleep for **3 days ago**:

| Policy | Setting |
|--------|---------|
| Accept late events up to | 30 days |
| Re-run L2 for affected dates | Yes, incremental |
| Re-run L3 snapshot | If `as_of_date` within last 7 days |

**Example:** Sleep for Jan 12 arrives Jan 15 → L2 recomputes Jan 12–Jan 15 features → L3 refreshes snapshots for Jan 12–Jan 15 if within policy window.

---

## 10. Channel handling: full vs web-only

### 10.1 system_type rules

| system_type | Name | Wearable expected | Biological ingestion |
|-------------|------|-------------------|---------------------|
| `1` | Full (app + wearable) | Yes | sleep, HR, activity required when connected |
| `0` | Web-only | No | No wearable tables; do not impute fake HR |

### 10.2 Example — same feature date, two users

**User A (system_type=1):**

```json
{
  "user_id": "1001",
  "local_date": "2025-01-14",
  "sleep_hours": 7.25,
  "resting_hr_bpm": 62,
  "mood_score_avg": 5.8
}
```

**User B (system_type=0):**

```json
{
  "user_id": "2050",
  "local_date": "2025-01-14",
  "sleep_hours": null,
  "resting_hr_bpm": null,
  "mood_score_avg": 5.2
}
```

L2 for User B: biological fields null with `{feature}_missing = 1`; L3 uses proxy formulas (see ENGINE-POC L3 §8.1).

### 10.3 Consent and disconnect events

**Event type:** `wearable_disconnected`

```json
{
  "event_type": "wearable_disconnected",
  "user_id": "1001",
  "payload": {
    "vendor": "apple",
    "disconnected_at": "2025-01-10T12:00:00Z",
    "reason": "user_revoked_consent"
  }
}
```

**Downstream actions:**
1. Set `has_wearable_connected = false`
2. Re-evaluate `system_type` (may remain 1 if app still active)
3. Stop wearable pull jobs for user
4. Do **not** delete historical wearable rows (retain for ML training)

---

## 11. Staging → L2 handoff

### 11.1 Contract

L2 expects **staging** tables finalized for `local_date = D` before compute job starts.

| Checkpoint | Signal |
|------------|--------|
| `staging.user_daily_activity` complete for date D | Watermark row |
| `staging.ingestion_watermarks` all sources ≥ D | L2 job allowed |

**Watermark example:**

```json
{
  "source_system": "wearable_apple",
  "user_id": "1001",
  "last_local_date_synced": "2025-01-14",
  "last_sync_completed_at": "2025-01-15T01:28:00Z"
}
```

### 11.2 L2 input (not L0 responsibility)

L0 delivers staging rollups; **L2 computes**:

| From staging | L2 feature |
|--------------|------------|
| 14 days of mood_scores | `mood_avg_14d`, `mood_volatility_14d` |
| 7 days of mood_scores | `mood_slope_7d` |
| 7 days of sleep_hours | `sleep_avg_7d`, `sleep_slope_7d` |
| 30d sleep baseline | `sleep_delta_30d` |
| therapy attended/scheduled 30d | `therapy_attendance_rate_30d` |

See [ENGINE-POC Part 4 §3](./ENGINE-POC-COMPLETE-DOCUMENTATION.md) for full computation spec.

### 11.3 Handoff failure example

**Scenario:** Therapy platform API down; sessions for Jan 14 missing.

```
staging.user_daily_activity.therapy_attended = null for all users
    → L2 still runs with null attendance
    → data_completeness_score reduced
    → L3 confidence_tier may drop to Moderate
    → L1 shows "Some therapy data unavailable"
```

Ingestion must **not** block entire pipeline; propagate missingness explicitly.

---

## 12. Label event ingestion (ML training)

Outcome labels for CRS v2 models (see [CRS spec §5](./CRS-Calculation-and-Trends-Production-Spec.md)) are derived from ingested facts — not entered manually.

### 12.1 Label sources

| Label | Source events | Horizon |
|-------|--------------|---------|
| `dropout_label` | `user_churned`, last app session + CRM status | 60d |
| `recovery_label` | Two `assessment_completed` CORE-OM | 30d |
| `relapse_label` | Two `assessment_completed` CORE-OM | 30d |
| `engagement_loss_label` | `staging.user_daily_activity` rollups | 14d |

### 12.2 Example — dropout label

**Ingested churn event:**

```json
{
  "event_type": "user_churned",
  "user_id": "1003",
  "occurred_at": "2025-02-01T00:00:00Z",
  "payload": {
    "churn_reason": "voluntary_exit",
    "last_session_date": "2025-01-28"
  }
}
```

**Label job (offline):** For snapshot `2025-01-01`, if user churned before `2025-03-02` → `dropout_label = 1`.

### 12.3 Label table (ML training only)

| user_id | snapshot_date | recovery_label | relapse_label | dropout_label | engagement_loss_label |
|---------|---------------|----------------|---------------|---------------|----------------------|
| 1001 | 2025-01-01 | 1 | 0 | 0 | 0 |
| 1002 | 2025-01-01 | 0 | 0 | 1 | 1 |
| 1003 | 2025-01-01 | 0 | 1 | 0 | 0 |

Written to `ml.training_labels` — separate from L2 inference features (labels excluded at inference time).

---

## 13. Security, privacy, and compliance

### 13.1 Data classification

| Class | Examples | Storage | L2 access |
|-------|----------|---------|-----------|
| **PHI / Sensitive** | Journal text, therapist notes | Encrypted object store; tokenized ref only in warehouse | NLP scores only |
| **Health metrics** | Sleep, HR, HRV, assessments | Encrypted at rest; row-level user isolation | Full |
| **Behavioral** | App sessions, engagement | Standard encryption | Full |
| **Meta** | user_id, org, timezone | Standard encryption | Full |

### 13.2 Access control

| Role | raw.* | staging.* | quarantine.* |
|------|-------|-----------|--------------|
| Ingestion service account | Write | Write | Write |
| L2 pipeline SA | Read | Read | No |
| ML training SA | Read (no journal text) | Read | No |
| Analyst (human) | No direct | Aggregated only | No |
| Support (break-glass) | Audit-logged read | No | Review queue |

### 13.3 Retention

| Data type | Retention | Deletion trigger |
|-----------|-----------|------------------|
| Raw events | 7 years (clinical audit) | User deletion request (GDPR) |
| Quarantine | 90 days | Auto-purge |
| Staging rollups | 3 years | User deletion |
| Encrypted journal blobs | Per consent | Consent withdrawal → delete refs |

### 13.4 User deletion (GDPR)

```
DELETE request for user_id=1001
    → Stop all connectors for user
    → Purge raw.* / staging.* / encrypted blobs
    → Anonymize ML training rows (remove user_id linkage)
    → Log deletion certificate
```

---

## 14. Failure handling and recovery

### 14.1 Failure modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Connector API 5xx | HTTP metrics | Exponential backoff; DLQ after 5 retries |
| Schema drift | Schema registry incompatibility | Block deploy; quarantine new fields until schema bump |
| Kafka lag > 1h | Consumer lag alert | Scale consumers; pause non-critical sources |
| Staging incomplete at 01:45 | Watermark check | Delay L2; page on-call |
| Bulk corrupt batch | Quarantine rate > 5% | Halt source; rollback connector version |

### 14.2 Dead letter queue (DLQ)

```json
{
  "dlq_id": "dlq_4421",
  "source_system": "wearable_apple",
  "failure_reason": "api_rate_limit_exceeded",
  "payload_ref": "s3://dlq/wearable_batch_4421.json",
  "failed_at": "2025-01-15T01:20:00Z",
  "retry_count": 5,
  "next_retry_at": "2025-01-15T07:00:00Z"
}
```

### 14.3 Backfill procedure

**Trigger:** User reconnects Apple Health after 30-day gap.

1. Connector requests vendor history (max 90 days)
2. Events ingested with historical `local_date`
3. Idempotency prevents overlap duplicates
4. Incremental L2 recompute for affected date range
5. L3 snapshot refresh for last 7 days
6. Audit log: `backfill_job_id`, row counts

**Example log:**

```
backfill_job_id: bf_8821
user_id: 1001
dates_affected: 2024-12-15 .. 2025-01-14
events_inserted: 47
events_skipped_duplicate: 3
l2_features_recomputed: 31 days
duration_sec: 124
```

---

## 15. Observability and SLAs

### 15.1 SLAs (production targets at 10K+ RPM)

| Metric | Target |
|--------|--------|
| App event ingestion availability | 99.9% |
| End-to-end lag (app event → raw table) p95 | < 5 min |
| Daily staging complete | By 01:45 UTC |
| Data loss (accepted events not persisted) | 0% |
| RPO (recovery point objective) | 1 hour |
| RTO (recovery time objective) | 4 hours |

### 15.2 Dashboards

| Dashboard | Key panels |
|-----------|------------|
| Ingestion health | Events/sec by source, error rate, lag |
| Quarantine | Top reasons, trend, unresolved count |
| Coverage | % users with mood/sleep/therapy per day |
| Connector version | Deployed versions vs expected |
| L0→L2 handoff | Watermark completeness, L2 start delay |

### 15.3 Example alert

```
ALERT: wearable_apple quarantine_rate = 2.3% (threshold 0.5%)
Top reason: duration_hours_out_of_range (84%)
Started: 2025-01-15T06:12:00Z after connector v1.3.3 deploy
Action: Rollback connector to v1.3.2 or patch validation rule
```

---

## 16. End-to-end walkthroughs

### 16.1 Walkthrough A — New user (cold start, day 5)

**Day 1:** Registration ingested → `users` row, `days_active=1`, `system_type=0` (web).

**Day 3:** First mood check-in + GAD-7 assessment.

**Day 5:** Two mood entries, one therapy session scheduled.

**Staging day 5 rollup:**

```json
{
  "user_id": "U001",
  "local_date": "2025-01-05",
  "mood_scores": [3.2, 3.8],
  "mood_checkin_count": 2,
  "sleep_hours": null,
  "therapy_attended": 0
}
```

**L2 output:** `mood_avg_14d = null` (< 3 points); `days_active = 5`; `data_completeness_score = 0.35`.

**L3:** `confidence_tier = Limited`; CRS may be suppressed; pillars use cohort prior 50.

**Product copy:** *"We're still learning about your patterns."*

---

### 16.2 Walkthrough B — Full user with wearable (day 45)

**Jan 14 events ingested:** (see §1.4 table)

**Jan 15 01:30 staging finalized.**

**Jan 15 02:00 L2 features:**

```json
{
  "user_id": "1001",
  "as_of_date": "2025-01-14",
  "days_active": 45,
  "system_type": 1,
  "data_completeness_score": 0.82,
  "mood_avg_14d": 5.8,
  "sleep_avg_7d": 6.6,
  "engagement_rate_7d": 0.71,
  "therapy_attendance_rate_30d": 0.80,
  "resting_hr_relative": -0.02,
  "core_om_functioning": 0.72
}
```

**Jan 15 02:45 L3 CRS (v2):** 81.2 (from outcome models).

---

### 16.3 Walkthrough C — Engagement loss detection

**Week 1–2 ingested engagement:**

| Date | app_sessions | tasks_completed |
|------|-------------|-----------------|
| Jan 1–7 | 6/7 days active | 5 |
| Jan 8–14 | 3/7 days active | 1 |

L2: `engagement_rate_7d` drops from 0.86 → 0.43 → `engagement_slope_7d` strongly negative.

L3: Motivation Momentum trend `direction_7d = declining`.

ML: `engagement_loss_probability = 0.55`.

Pattern engine: Warning card *"Engagement momentum declining"* despite Clarity still at 78.

---

## 17. Implementation roadmap

| Phase | Scope | Delivers | Depends on |
|-------|-------|----------|------------|
| **0** | User registry + app mood stream | `raw.app_events`, `users` | Auth service |
| **1** | Engagement + therapy + assessments | Behavioral + clinical staging | Phase 0 |
| **2** | Apple/Google wearable (sleep, HR, activity) | Biological staging | OAuth, D1 proxy decision |
| **3** | Staging finalize + L2 handoff watermarks | Reliable daily batch | Phase 1–2 |
| **4** | Journal NLP sidecar | `journaling_concern_score_7d` | Encrypted blob store |
| **5** | Label generation jobs | ML training tables | 30–60d history |
| **6** | v1.1 wearables (HRV, stress episodes) | Full biological PRD | Vendor partnerships |
| **7** | CogniArt + therapist ratings | Cognitive Momentum inputs | Product launch |

**Validation tooling:** Use [`scripts/validate_dataset_columns.py`](./scripts/validate_dataset_columns.py) against L2 exports to verify ingestion → feature pipeline completeness.

---

## 18. Appendices

### Appendix A — Event type catalog

| event_type | source_system | v1 |
|------------|---------------|-----|
| `user_registered` | auth_crm | Yes |
| `user_profile_updated` | auth_crm | Yes |
| `user_churned` | auth_crm | Yes |
| `mood_checkin` | app_mobile, app_web | Yes |
| `motivation_checkin` | app_mobile, app_web | Yes |
| `confidence_checkin` | app_mobile, app_web | Yes |
| `app_session` | app_mobile, app_web | Yes |
| `journal_entry` | app_mobile | Yes |
| `journal_features_computed` | nlp_worker | Yes |
| `sleep_session` | wearable_* | Yes |
| `heart_rate_daily` | wearable_* | Yes |
| `activity_daily` | wearable_* | Yes |
| `wearable_disconnected` | wearable_* | Yes |
| `session_scheduled` | therapy_platform | Yes |
| `session_attended` | therapy_platform | Yes |
| `session_missed` | therapy_platform | Yes |
| `assessment_completed` | assessments | Yes |
| `assessment_corrected` | assessments | Yes |
| `content_viewed` | content_engagement | Optional |
| `cogniart_task_completed` | cogniart | Future |

### Appendix B — Connector configuration template

```yaml
connector:
  id: wearable_apple
  version: 1.3.2
  enabled: true
  schedule:
    cron: "0 */6 * * *"
    timezone: UTC
  rate_limit:
    requests_per_minute: 120
    per_user_per_hour: 4
  retry:
    max_attempts: 5
    backoff_seconds: [30, 60, 300, 900, 3600]
  schema:
    registry_url: https://schema.internal/mindpeers
    subject: mindpeers.raw.wearable.v1
  output:
    table: raw.wearable_sleep
    format: parquet
    partition: local_date
```

### Appendix C — Sample ingestion API (app events)

**POST** `/v1/events`

```http
POST /v1/events HTTP/1.1
Authorization: Bearer {user_token}
Content-Type: application/json
Idempotency-Key: 1001:mood_checkin:2025-01-14T08:45:00+05:30

{
  "event_type": "mood_checkin",
  "occurred_at": "2025-01-14T08:45:00+05:30",
  "timezone": "Asia/Kolkata",
  "payload": {
    "mood_score": 5.8,
    "scale_min": 0,
    "scale_max": 10
  }
}
```

**Response 202:**

```json
{
  "status": "accepted",
  "event_id": "evt_mood_99102",
  "ingested_at": "2025-01-14T03:15:04Z"
}
```

**Response 409 (duplicate):**

```json
{
  "status": "duplicate_skipped",
  "event_id": "evt_mood_99102",
  "original_ingested_at": "2025-01-14T03:15:04Z"
}
```

### Appendix D — Related documents and code

| Artifact | Relationship |
|----------|--------------|
| [Engine-Architecture-Index.md](./Engine-Architecture-Index.md) | Master index — all layers and quick start |
| [CRS-Calculation-and-Trends-Production-Spec.md](./CRS-Calculation-and-Trends-Production-Spec.md) | Downstream consumer of L2 features and labels |
| [ENGINE-POC-COMPLETE-DOCUMENTATION.md](./ENGINE-POC-COMPLETE-DOCUMENTATION.md) | L2 registry, L3 scoring, dataset checklist (Part 8) |
| [schemas/ingestion/](./schemas/ingestion/) | JSON Schema — envelope + 9 event payloads + registry |
| [ingestion/](./ingestion/) | Python stubs: connectors, validator, staging rollup |
| [scripts/run_ingestion_demo.py](./scripts/run_ingestion_demo.py) | Runnable L0 demo (ingest → staging) |
| [scripts/validate_ingestion_event.py](./scripts/validate_ingestion_event.py) | CLI schema validation |
| [Engine-POC-Sample-Dataset.xlsx](./Engine-POC-Sample-Dataset.xlsx) | Target L2 column contract after ingestion |
| [scripts/validate_dataset_columns.py](./scripts/validate_dataset_columns.py) | CI validation for L2 exports |

### Appendix E — Glossary

| Term | Definition |
|------|------------|
| **L0** | Data Ingestion Layer (this document) |
| **Raw table** | Append-only event store before aggregation |
| **Staging** | User-day rollups ready for L2 |
| **Connector** | Service that pulls or receives events from one source |
| **Watermark** | Pointer to last successfully synced date per source/user |
| **Quarantine** | Holding area for invalid events pending review |
| **system_type** | 1 = full (wearable capable), 0 = web-only |
| **local_date** | Calendar date in user's timezone for daily aggregation |
| **Idempotency key** | Stable key ensuring at-most-once semantic writes |

### Appendix F — Revision history

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-05 | Initial production spec |

---

*This document defines Layer 0 (Data Ingestion). Feature computation remains in L2; scoring in L3. Do not compute CRS, pillars, or trends in the ingestion layer.*
