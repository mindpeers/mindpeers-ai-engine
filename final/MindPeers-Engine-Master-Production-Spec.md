# MindPeers Cognitive Readiness Engine
## Master Production Specification — Complete Program Document

---

| Field | Value |
|-------|-------|
| **Document ID** | MP-ENGINE-MASTER-001 |
| **Version** | 1.0.0 |
| **Status** | For review — production-ready specification stack |
| **Date** | 2026-06-05 |
| **Classification** | Internal — Engineering, Data Platform, ML, Product, Clinical |
| **Supersedes** | Individual POC docs for implementation decisions |
| **Authoritative depth** | Layer-specific specs linked in [Appendix H](#appendix-h--source-document-index) remain normative for implementation detail |

---

### PDF export

From the repository root:

```bash
pandoc final/MindPeers-Engine-Master-Production-Spec.md \
  -o final/MindPeers-Engine-Master-Production-Spec.pdf \
  --toc --toc-depth=3 \
  -V geometry:margin=1in \
  -V documentclass=report \
  --metadata title="MindPeers Cognitive Readiness Engine — Master Production Spec"
```

Alternative: open this file in VS Code / Cursor → Markdown PDF extension, or paste into Notion / Confluence for styled export.

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Program requirements](#2-program-requirements)
3. [Architecture overview](#3-architecture-overview)
4. [Three-layer product model](#4-three-layer-product-model)
5. [Layer 0 — Data ingestion](#5-layer-0--data-ingestion)
6. [Layer 2 — Feature store](#6-layer-2--feature-store)
7. [Layer 4 — ML labels and outcome models](#7-layer-4--ml-labels-and-outcome-models)
8. [Layer 3 — Scoring engine](#8-layer-3--scoring-engine)
9. [Layer 1 — API, patterns, and narrative](#9-layer-1--api-patterns-and-narrative)
10. [Implementation phases](#10-implementation-phases)
11. [Engine Part1 attribute binding](#11-engine-part1-attribute-binding)
12. [Security, operations, and governance](#12-security-operations-and-governance)
- [Appendix A — Canonical data tables](#appendix-a--canonical-data-tables)
- [Appendix B — L0 event type catalog](#appendix-b--l0-event-type-catalog)
- [Appendix C — L2 feature registry summary](#appendix-c--l2-feature-registry-summary)
- [Appendix D — Clinical label rules summary](#appendix-d--clinical-label-rules-summary)
- [Appendix E — Version and audit fields](#appendix-e--version-and-audit-fields)
- [Appendix F — Glossary](#appendix-f--glossary)
- [Appendix G — Acceptance checklist](#appendix-g--acceptance-checklist)
- [Appendix H — Source document index](#appendix-h--source-document-index)

---

<!-- pagebreak -->

## 1. Executive summary

### 1.1 What we are building

The **MindPeers Cognitive Readiness Engine** transforms raw behavioural, clinical, wearable, and therapy data into a unified mental-health report:

| Output | Question answered | Layer |
|--------|-------------------|-------|
| **CRS (Cognitive Readiness Score)** | Where is the user heading in therapy and daily functioning? | L3 + L4 |
| **Four pillars** | Where am I right now? (Clarity, Emotional Balance, Resilience, Capacity) | L3 |
| **Seven trends** | Which direction is each domain moving? | L3 |
| **Five narrative blocks** | Where / Why / Aware / Risk / Next | L1 |

### 1.2 Three architectural layers (do not merge)

| Layer | Type | Primary formula | When used |
|-------|------|-----------------|-----------|
| **State** | Same-day snapshot | Engine Part1 rule-based weights | Pillars + `crs_readiness_score` |
| **Trajectory** | Time-series + ML | CRS v2 composite + 7 trends | Headline CRS when mature |
| **Narrative** | Deterministic text | Pattern engine + driver attribution | L1 API |

**Critical rule:** `crs_v2_score` and `crs_readiness_score` use **different formulas**. Never merge them. Expose both during shadow period; set `crs_primary` when cutover criteria met.

### 1.3 Dual CRS model

**CRS v2 (ML composite — primary at maturity):**

```
CRS = 0.40 × P(recovery)
    + 0.20 × (1 − P(dropout))
    + 0.20 × (1 − P(engagement_loss))
    + 0.20 × (1 − P(relapse))
```

Scaled to **0–100**. Probabilities from four supervised outcome models (L4).

**CRS readiness (Part1 rule-based — cold start + explainability):**

```
crs_readiness = 0.30×Assessment + 0.30×Lifestyle + 0.15×Tools + 0.15×Forms + 0.10×Therapist
```

Renormalize category weights when blocks have no data. Cohort prior 50 for cold start.

### 1.4 Coverage commitment

| Dimension | Target | Status in spec |
|-----------|--------|----------------|
| Engine Part1 attributes | 70/70 (A01–A70) | Binding spec + L2 v2 registry |
| L2 feature columns | 86 at `feature_v2.0.0` | L2 §7.5 |
| L0 event traceability | Every attribute → event_type | Data Ingestion Appendix F |
| State + trajectory binding | Every attribute → pillar and/or trend | Binding spec §3–§4 |
| Implementation waves | Phase 1 (~18 attrs) → Phase 5 (100%) | Phase TRDs |

### 1.5 Recommended dashboard layout

```
┌─────────────────────────────────────────────────────────────┐
│  CURRENT STATE (Pillars)          │  TRAJECTORY (Trends)    │
├───────────────────────────────────┼─────────────────────────┤
│  CRS ...................... 81    │  Recovery Readiness  ↑  │
│  Clarity .................. 78    │  Stress Load ........ ↓  │
│  Emotional Balance ........ 72    │  Sleep Consistency .. ↑  │
│  Resilience ............... 80    │  Energy Rhythm ...... →  │
│  Capacity ................. 74    │  Emotional Stability .. ↑  │
│                                   │  Motivation Momentum .. ↓  │
│                                   │  Cognitive Momentum ... ↑  │
└───────────────────────────────────┴─────────────────────────┘
```

### 1.6 Daily batch pipeline (UTC)

| Time | Layer | Job |
|------|-------|-----|
| Continuous | L0 | App event stream → raw |
| Every 6h | L0 | Wearable sync |
| **01:30** | L0 | Staging finalize (`user_daily_activity`) |
| **02:00** | L2 | Feature computation |
| **02:15** | L4 | Label generation (training batch) |
| **02:30** | L4 | Outcome model inference |
| **02:45** | L3 | CRS, pillars, trends |
| **03:00** | L1 | Pattern evaluation |
| **03:05** | L1 | Persist `user_engine_snapshot` |

**SLA:** Full pipeline complete by **03:30 UTC**. API reads snapshot only (no on-request scoring).

---

<!-- pagebreak -->

## 2. Program requirements

### 2.1 Business objectives

| Objective | Success metric |
|-----------|----------------|
| Unified mental health report | CRS + 4 pillars + 7 trends on dashboard |
| Auditable data lineage | ≥95% snapshots traceable to L0 events |
| Trajectory prediction | Recovery model AUC-PR ≥ 0.65 on holdout |
| Clinical safety | Risk cap when `core_om_risk ≥ 0.70`; escalation documented |
| Deterministic scoring | Same inputs + versions → identical batch = API output |
| Cold start | Scores from day 1 with confidence tier |

### 2.2 Scope

**In scope:** L0 ingestion, L2 features, L4 labels + 4 outcome models, L3 scoring (dual CRS, pillars, trends, risk cap), L1 snapshot API + narrative.

**Out of scope:** Mobile UI, real-time streaming scores, LLM intent router productionization, CogniArt full NLP (Phase 5 partial).

### 2.3 Cross-phase functional requirements

| ID | Requirement | Phase |
|----|-------------|-------|
| FR-001 | Ingest all v1 event types (Appendix B) | 1 |
| FR-002 | Produce `staging.user_daily_activity` at `(user_id, local_date)` | 1 |
| FR-003 | Compute 34 L2 v1 features deterministically | 1 |
| FR-004 | Compute 4 pillar scores (Part1 category weights) | 1 |
| FR-005 | Compute CRS readiness (Part1 5-category weights) | 1 |
| FR-006 | Compute 7 trend metrics with `direction_7d` | 1 |
| FR-007 | Apply CORE-OM risk cap (≥0.70 → cap 40) | 1 |
| FR-008 | Generate clinical labels §4.3 (R1–R4, L1–L5) | 2 |
| FR-009 | Train 4 outcome models; register in model registry | 2 |
| FR-010 | Run inference: P(recovery), P(relapse), P(dropout), P(engagement_loss) | 2–5 |
| FR-011 | Compute CRS v2 composite | 3 |
| FR-012 | Shadow CRS v2 alongside readiness; expose both in API | 3 |
| FR-013 | Generate narrative blocks (Where/Why/Aware/Risk/Next) | 3 |
| FR-014 | Set `crs_primary = v2` when maturity rules met | 4 |
| FR-015 | Persist `user_engine_snapshot` for L1 API GA | 4 |
| FR-016 | Ingest v1.1 events: games, forms, biomarkers, lifestyle, therapist sync | 5 |

### 2.4 Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | Batch pipeline completion | By 03:30 UTC daily |
| NFR-002 | API p99 latency (snapshot read) | < 200ms |
| NFR-003 | Ingestion availability | 99.9% |
| NFR-004 | Determinism | Bit-identical batch vs API path |
| NFR-005 | Auditability | `score_version`, `label_version`, `model_bundle_version` on every snapshot |
| NFR-006 | Data retention | Per privacy policy; raw events ≥ 24 months |
| NFR-007 | Throughput design | 10,000 API RPM; 500K users batch |
| NFR-008 | Idempotent ingestion | Duplicate events do not double-count |
| NFR-009 | Censoring transparency | `label_censored_reason` stored for ML rows |
| NFR-010 | No diagnosis copy | Narrative uses probabilistic language only |

### 2.5 Stakeholders

| Role | Responsibility |
|------|----------------|
| Product | Score meanings, five questions, band copy |
| Clinical lead | MCID thresholds, risk cap, escalation |
| Engineering | L0–L3 services, API |
| Data Platform | Warehouse, batch orchestration |
| ML | Labels, models, monitoring |
| Security / Legal | PHI, consent, retention |

---

<!-- pagebreak -->

## 3. Architecture overview

### 3.1 Layer map

```
Source systems (app, wearable, therapy, assessments, CRM)
        ↓
┌───────────────────────────────────────────────────────────┐
│ L0 — Data Ingestion                                       │
│ Connectors → Validate → Dedupe → raw.* → staging.*        │
└─────────────────────────────┬─────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────┐
│ L2 — Feature Store                                        │
│ 7d/14d/30d windows, slopes, flags → features.user_*       │
└──────────────┬────────────────────────────┬───────────────┘
               ↓                            ↓
┌──────────────────────────┐   ┌────────────────────────────┐
│ L4 — ML                  │   │ L3 — Scoring               │
│ Labels + 4 outcome models│   │ CRS v2 + readiness         │
│ Inference probabilities  │   │ Pillars + trends + risk cap│
└──────────────┬───────────┘   └─────────────┬──────────────┘
               └──────────────┬───────────────┘
                              ↓
┌───────────────────────────────────────────────────────────┐
│ L1 — Product Engine                                       │
│ Patterns → Narrative → user_engine_snapshot → REST API    │
└───────────────────────────────────────────────────────────┘
```

### 3.2 Layer responsibilities

| Layer | Runtime | Input | Output |
|-------|---------|-------|--------|
| L0 | Stream + batch | Source APIs / webhooks | `staging.*` |
| L2 | Batch 02:00 UTC | Staging | Feature row per user-day |
| L4 labels | Batch 02:15 UTC | Raw assessments + events | `ml.training_labels` |
| L4 inference | Batch 02:30 UTC | Features + models | Probabilities |
| L3 | Batch 02:45 UTC | Features + probabilities | `scoring.user_scores_daily` |
| L1 | Batch 03:00–03:05 UTC | L3 output | Snapshot + API |

### 3.3 Technology stack (recommended)

| Concern | Recommendation |
|---------|----------------|
| Event bus | Kafka / Kinesis |
| Raw store | PostgreSQL + object storage |
| Warehouse | BigQuery / Snowflake / Redshift |
| Feature store | Warehouse tables (v1); Feast optional v2 |
| ML training | Python + XGBoost/LightGBM |
| Model registry | MLflow / cloud ML |
| Scoring | Python batch job → SQL |
| API | FastAPI / Go + Redis cache |
| Secrets | Vault / cloud secrets |
| Orchestrator | Airflow / Dagster |

### 3.4 Environments

| Environment | Purpose | Data |
|-------------|---------|------|
| dev | Feature development | Synthetic |
| staging | Integration + shadow | Anonymized subset |
| prod | Live users | Full PHI controls |

Blue/green for API; batch jobs versioned by `score_version`.

---

<!-- pagebreak -->

## 4. Three-layer product model

### 4.1 State layer — pillars and CRS readiness

**Question:** *Where am I right now?*

| Pillar | Meaning |
|--------|---------|
| **Clarity** | Mental sharpness, focus, cognitive organisation |
| **Emotional Balance** | Emotional steadiness, distress load, regulation |
| **Resilience** | Recovery capacity, adaptability, coping strength |
| **Capacity** | Functional bandwidth for daily demands |

Each pillar uses **five Part1 input categories** with explicit weights (Tools, Lifestyle, Assessment, Forms, Therapist). Missing data → renormalize within category block.

**CRS readiness** aggregates five top-level categories (Assessment 30%, Lifestyle+Biomarker 30%, Tools 15%, Forms 15%, Therapist 10%).

### 4.2 Trajectory layer — CRS v2 and trends

**Question:** *Where am I heading?*

| Output | Mechanism |
|--------|-----------|
| **CRS v2** | Weighted composite of four outcome probabilities |
| **7 trends** | Time-series constructs: level, slope, volatility over windows |

A user can have high Clarity (80) but negative Motivation Momentum (−25): *currently healthy, but deteriorating* — a clinically critical signal.

### 4.3 Narrative layer — five report questions

| Question | API field | Source |
|----------|-----------|--------|
| Where am I now? | `narrative.where_now` | Pillars + CRS band |
| Why is it like this? | `narrative.why_summary` | SHAP drivers + Part1 categories |
| What should I be aware of? | `narrative.awareness_flags` | Trend deltas, pattern rules |
| What is my risk? | `narrative.risk` | `core_om_risk`, relapse probability |
| What should I do next? | `narrative.next_actions` | Pattern engine recommendations |

**Rule:** Narrative never invents scores — references precomputed snapshot only.

### 4.4 Risk cap (clinical safety)

```
IF core_om_risk >= 0.70:
    cap ALL display scores (CRS, pillars, trends) at 40
    set risk_elevated = true
    override narrative with escalation copy
```

Independent of CRS formula. Applies before API output.

---

<!-- pagebreak -->

## 5. Layer 0 — Data ingestion

**Normative detail:** [Data-Ingestion-Layer-Production-Spec.md](../Data-Ingestion-Layer-Production-Spec.md) v1.1.0

### 5.1 Responsibilities

1. Receive events from connectors (app, wearable, therapy, assessments, CRM)
2. Validate against JSON Schema + business rules
3. Deduplicate via `idempotency_key`
4. Persist append-only to `raw.events`
5. Roll up to `staging.user_daily_activity` at `(user_id, local_date)`
6. Never compute CRS, pillars, or trends in L0

### 5.2 Event envelope (all events)

```json
{
  "event_id": "evt_uuid",
  "event_type": "mood_checkin",
  "user_id": "1001",
  "occurred_at": "2025-01-14T08:45:00+05:30",
  "timezone": "Asia/Kolkata",
  "source_system": "app_mobile",
  "idempotency_key": "1001:mood_checkin:2025-01-14T08:45:00+05:30",
  "schema_version": "1.0.0",
  "payload": { }
}
```

### 5.3 Validation pipeline

```
Event received
  → Schema validation (JSON Schema)
  → Business rules (ranges, enums)
  → Referential integrity (user exists)
  → Duplicate check (idempotency_key)
  → PII scan (journal raw text)
  → PASS → raw.*  |  FAIL → quarantine.*
```

### 5.4 Staging rollup example

```json
{
  "user_id": "1001",
  "local_date": "2025-01-14",
  "mood_checkin_count": 1,
  "mood_scores": [2.9],
  "motivation_scores": [4.0],
  "app_sessions": 2,
  "tasks_completed": 1,
  "sleep_hours": 7.25,
  "resting_hr_bpm": 62,
  "hrv_rmssd_ms": 58,
  "therapy_attended": 1,
  "has_wearable_data": true,
  "staging_built_at": "2025-01-15T01:32:00Z"
}
```

**v1.1 additive staging fields:** `fatigue_level`, `exercise_minutes`, `game_sessions_count`, `form_submitted_flag`, `biomarker_updated_flag`, `therapist_sync_at`.

### 5.5 Scale normalization at L0

| Signal | App may send | L0 stores |
|--------|--------------|-----------|
| Mood | 0–10 | Canonical 0–5 (`mood × 0.5` if scale_max=10) |
| Motivation / confidence | 0–5 or 0–10 | Canonical per instrument config |

### 5.6 v1.1 event payloads (summary)

| Event | Attributes | Key payload fields |
|-------|------------|-------------------|
| `lifestyle_checkin` | A12, A15–A20 | fatigue, exercise, nutrition, hydration, hunger, libido, sun |
| `game_session_completed` | A30–A32 | game_id, score, accuracy, rage_quit |
| `intake_form_submitted` | A44–A64 | 21 form fields + crisis_marker |
| `biomarker_result` | A21–A26 | marker_type, value, unit, reference_range |
| `therapist_profile_sync` | A68–A70 | availability, affordability, match scores |

Full JSON examples: Data Ingestion **Appendix F**.

### 5.7 L0 → L2 handoff contract

| Checkpoint | Requirement |
|------------|-------------|
| Staging complete for date D | Watermark row per source |
| All sources ≥ D | L2 job allowed at 02:00 UTC |
| Late data backfill | Re-run L2 for affected users/dates |

---

<!-- pagebreak -->

## 6. Layer 2 — Feature store

**Normative detail:** [L2-Feature-Store-Production-Spec.md](../L2-Feature-Store-Production-Spec.md) v2.0.0

### 6.1 Output contract

| Field | Value |
|-------|-------|
| Table | `features.user_features_daily` |
| Grain | `(user_id, as_of_date)` |
| Partition | `as_of_date` |
| Version | `feature_v1.0.0` (Phase 1) → `feature_v2.0.0` (Phase 5) |

### 6.2 Feature version roadmap

| Version | Columns | Part1 attrs | Phase |
|---------|---------|-------------|-------|
| `feature_v1.0.0` | 34 | 18 (W1 wave) | 1 |
| `feature_v2.0.0` | 86 (+52) | 70 (100%) | 5 |

### 6.3 v1 core features (Phase 1)

| Domain | Features |
|--------|----------|
| Mood | `mood_avg_14d`, `mood_slope_7d`, `mood_volatility_14d` |
| Motivation / confidence | `motivation_avg_14d`, `motivation_slope_7d`, `confidence_avg_14d`, `confidence_slope_7d` |
| Engagement | `engagement_rate_7d`, `engagement_slope_7d`, `engagement_delta_30d` |
| Sleep | `sleep_avg_7d`, `sleep_delta_30d`, `sleep_slope_7d`, `sleep_persistence_low_days`, `sleep_duration_variance_14d`, `bedtime_variance_14d` |
| Wearable | `resting_hr_relative`, `activity_slope_7d` |
| Clinical | `core_om_*`, `gad7_normalized_latest`, `core_om_delta_30d` |
| Therapy | `therapy_attendance_rate_30d` |
| Flags | `cortisol_flag`, `withdrawal_flag`, `sleep_mood_coupled_decline` |
| Meta | `days_active`, `system_type`, `data_completeness_score` |

### 6.4 v2 additive domains (Phase 5)

| Domain | Example columns |
|--------|-----------------|
| Extended clinical | `phq9_normalized_latest`, `trauma_score_latest`, `adhd_score_latest` |
| Lifestyle | `fatigue_score_7d`, `exercise_*`, `nutrition_score_7d`, `hydration_score_7d` |
| Biomarkers | `biomarker_cortisol_latest`, `biomarker_tsh_latest`, `weight_delta_90d` |
| Games | `game_memory_score_7d`, `game_connect4_score_7d`, `game_frustration_proxy` |
| Journal NLP | `journal_sentiment_7d`, `journal_gratitude_sentiment_7d` |
| Forms | `form_work_stress_score`, `form_burnout_score`, … (21 columns) |
| Therapy extended | `therapy_missed_rate_30d`, `days_since_last_session` |
| Therapist | `therapist_availability_score`, `therapist_match_score` |

### 6.5 Computation principles

| Rule | Policy |
|------|--------|
| Windows | 7d, 14d, 30d user-local days |
| Slopes | OLS linear coefficient |
| Null handling | `null` + `{feature}_missing = 1`; L2 never imputes cohort priors |
| PIT safety | Features at T exclude events after T |
| Idempotency | Re-run overwrites same `(user_id, as_of_date, feature_version)` |
| Web-only | Wearable features `null` when `system_type = 0` |

### 6.6 Lineage

Full **86-column** L0 → staging → L2 matrix: L2 **§11**. Quick reference:

| L2 column | L0 event | Staging source |
|-----------|----------|----------------|
| `mood_avg_14d` | `mood_checkin` | `mood_scores[]` |
| `fatigue_score_7d` | `lifestyle_checkin` | `fatigue_level` |
| `game_memory_score_7d` | `game_session_completed` | `game_memory_scores[]` |
| `form_burnout_score` | `intake_form_submitted` | `raw.intake_forms` |
| `biomarker_cortisol_latest` | `biomarker_result` | `raw.biomarkers` |
| `therapist_match_score` | `therapist_profile_sync` | `raw.therapist_profiles` |

---

<!-- pagebreak -->

## 7. Layer 4 — ML labels and outcome models

**Normative detail:** [CRS Unified v3 §4–§5](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)

### 7.1 Four outcome models

| Model | Label | Question | Training target |
|-------|-------|----------|-----------------|
| Recovery | `recovery_label` | Clinically meaningful improvement? | Binary / censored |
| Relapse | `relapse_label` | Meaningful worsening or risk elevation? | Binary / censored |
| Dropout | `dropout_label` | User churned or inactive 30d+? | Binary |
| Engagement loss | `engagement_loss_label` | Engagement dropped >50% vs baseline? | Binary |

CRS is **not** an ML target. It is a deterministic composite of these four model outputs.

### 7.2 Label design principles

| Principle | Requirement |
|-----------|-------------|
| Clinical ground truth | Labels from assessments + program events, not CRS |
| Subscale-aware | Use CORE-OM subscales, not total only |
| Sparse-safe | No follow-up → `null` (censored), never default 0 |
| Mutually exclusive | Relapse evaluated before recovery |
| Point-in-time | Label at T uses only data ≤ T + horizon |
| Auditable | Store `label_version`, thresholds, assessment IDs |

### 7.3 Key configuration constants

| Constant | Default | Description |
|----------|---------|-------------|
| `CORE_OM_MCID_TOTAL` | 5 | Min meaningful total score change |
| `CORE_OM_MCID_SUBSCALE_NORM` | 0.10 | Min normalized subscale change |
| `GAD7_MCID` | 4 | Min GAD-7 change |
| `CORE_OM_RISK_RELAPSE_THRESHOLD` | 0.70 | Risk subscale relapse signal |
| `ASSESSMENT_HORIZON_DAYS` | 30 | Target follow-up period |
| `ASSESSMENT_WINDOW_MIN/MAX` | 21 / 45 | Valid follow-up window |
| `DROPOUT_INACTIVE_DAYS` | 30 | Inactivity threshold |
| `ENGAGEMENT_LOSS_RELATIVE_DROP` | 0.50 | 50% engagement drop |
| `LABEL_VERSION` | `label_v2.0.0` | Bump on rule change |

### 7.4 Recovery rules (summary)

**R1 — Total improvement:** CORE-OM total decreases by ≥ MCID within window.  
**R2 — Subscale improvement:** ≥2 subscales improve by ≥ MCID (problems↓, functioning↑, wellbeing↑).  
**R3 — Risk reduction:** `core_om_risk` decreases meaningfully.  
**R4 — GAD-7 confirmer:** GAD-7 improves ≥ MCID when CORE-OM follow-up sparse.

**Safety guard:** `core_om_risk ≥ 0.70` at follow-up → recovery = 0.

### 7.5 Relapse rules (summary)

**L1 — Total worsening:** CORE-OM total increases ≥ MCID.  
**L2 — Subscale worsening:** Problems↑ or functioning↓ or wellbeing↓ ≥ MCID.  
**L3 — Risk elevation:** `core_om_risk ≥ 0.70`.  
**L4 — GAD-7 worsening:** GAD-7 increases ≥ MCID.  
**L5 — Engagement collapse:** `engagement_loss_label = 1` with clinical signal.

Evaluate relapse **before** recovery. At most one positive clinical label per snapshot.

### 7.6 Dropout and engagement loss

**Dropout:** `user_churned` event OR no app activity for `DROPOUT_INACTIVE_DAYS` within `DROPOUT_HORIZON_DAYS`.

**Engagement loss:** `engagement_rate_7d` at T+14 < 50% of 30-day baseline engagement rate.

### 7.7 Model training and inference

| Stage | Schedule | Output |
|-------|----------|--------|
| Label job | 02:15 UTC (training batches) | `ml.training_labels` |
| Training | Weekly / on drift | Registered models in `ml.model_registry` |
| Inference | 02:30 UTC daily | `recovery_probability`, etc. |

**Targets:** Recovery AUC-PR ≥ 0.65; monitor weekly for >5% AUC drop.

---

<!-- pagebreak -->

## 8. Layer 3 — Scoring engine

**Normative detail:** [CRS Unified v3 §6–§8, §11](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)

### 8.1 CRS v2 calculation

**Given predictions:**

```json
{
  "recovery_probability": 0.82,
  "dropout_probability": 0.25,
  "engagement_loss_probability": 0.18,
  "relapse_probability": 0.15
}
```

| Term | Calculation | Value |
|------|-------------|-------|
| Recovery Potential | 0.40 × 82 | 32.8 |
| Retention | 0.20 × (1−0.25) × 100 | 15.0 |
| Engagement Stability | 0.20 × (1−0.18) × 100 | 16.4 |
| Relapse Avoidance | 0.20 × (1−0.15) × 100 | 17.0 |
| **CRS** | Sum | **81.2** |

### 8.2 CRS bands

| Band | Range | Label |
|------|-------|-------|
| Low | 0–33 | Limited readiness |
| Moderate | 34–66 | Developing readiness |
| High | 67–100 | Strong readiness |

### 8.3 CRS readiness (Part1)

**Category weights:**

| Category | Weight | Parameters |
|----------|--------|------------|
| Assessment | 30% | A01–A10 |
| Lifestyle + Biomarker | 30% | A11–A18, A21–A23 |
| Tools / Behavioural | 15% | A27–A29, A30–A31, A37 |
| Forms | 15% | A44–A49 |
| Therapist / Session | 10% | A43, A66–A70 |

```
block_score = mean(normalized non-null parameters in block)
crs_readiness = weighted sum (renormalize if block missing)
```

### 8.4 Headline selection

| Condition | `cognitive_readiness_score` | Also expose |
|-----------|------------------------------|-------------|
| Full maturity + models | CRS v2 | `crs_readiness_score`, `crs_v2_score` |
| Cold start | `crs_readiness_score` | `crs_v2_score = null` |
| Shadow period | Both | `crs_primary` indicates headline |

### 8.5 Pillar category weights (summary)

**Clarity:** Tools 30%, Lifestyle 25%, Assessment 20%, Forms 15%, Therapist 10%  
**Emotional Balance:** Assessment 35%, Forms 20%, Tools 20%, Lifestyle 20%, Therapist 5%  
**Resilience:** Lifestyle 30%, Assessment 25%, Forms 20%, Tools 15%, Therapist 10%  
**Capacity:** Assessment 30%, Lifestyle 30%, Forms 20%, Therapist 10%, Tools 10%

Full attribute lists per pillar: [Engine-Part1-Full-Attribute-Binding-Spec.md §3](./Engine-Part1-Full-Attribute-Binding-Spec.md).

### 8.6 Seven trend metrics

| # | Trend ID | Pillar domain | Key question |
|---|----------|---------------|--------------|
| 1 | `recovery_readiness` | Biological | How restored is the body? |
| 2 | `stress_load` | Biological | How much physiological strain? |
| 3 | `sleep_consistency` | Biological + Behavioral | How regular is sleep? |
| 4 | `energy_rhythm` | Behavioral | Is daily energy stable? |
| 5 | `emotional_stability` | Psychological | Are emotions stabilizing? |
| 6 | `motivation_momentum` | Psychological + Behavioral | Growth or withdrawal? |
| 7 | `cognitive_momentum` | Cognitive | Is thinking clarifying? |

Each trend outputs: `score` (0–100), `band`, `direction_7d` (↑ improving / ↓ declining / → stable), `available`, `top_inputs`.

### 8.7 Trend formula upgrade rule

| `feature_version` | Trend bindings |
|-------------------|----------------|
| `feature_v1.0.0` | Minimal v1 features (Phase 1) |
| `feature_v2.0.0` | **Full Part1 attribute bindings** (Phase 5) |

Example — **Motivation Momentum** at v2 uses: A28 motivation slope, A37–A39 engagement/guides, A42 check-in drop-off, A61 burnout forms.

### 8.8 Cold start and confidence

| `days_active` | `data_maturity_stage` | Policy |
|---------------|----------------------|--------|
| 0–6 | `cold_start` | Cohort prior 50; confidence Limited |
| 7–29 | `developing` | Partial blocks; confidence Moderate |
| 30+ | `full` | Full formulas; confidence High if completeness ≥ 0.7 |

**Web-only (`system_type = 0`):** Exclude biological blocks; renormalize remaining pillar weights.

### 8.9 Data maturity gates

| Feature class | Min days active |
|---------------|-----------------|
| 7d windows | 7 |
| 14d windows | 7 (partial OK) |
| 30d deltas | 30 |
| HR relative | 30 + wearable |

---

<!-- pagebreak -->

## 9. Layer 1 — API, patterns, and narrative

### 9.1 Primary endpoint

**GET** `/users/{user_id}/engine/report?date={YYYY-MM-DD}`

### 9.2 Response structure (abbreviated)

```json
{
  "user_id": "1001",
  "as_of_date": "2025-01-15",
  "score_version": "crs_v3.0.0",
  "model_bundle_version": "outcome_models_v1.2.0",
  "confidence_tier": "High",
  "crs_primary": "v2",
  "cognitive_readiness_score": 81.2,
  "crs_v2_score": 81.2,
  "crs_readiness_score": 74.5,
  "crs_band": "High",
  "risk_elevated": false,
  "pillars": {
    "clarity_score": 73,
    "emotional_balance_score": 69,
    "resilience_score": 68,
    "capacity_score": 59
  },
  "outcome_probabilities": {
    "recovery_probability": 0.82,
    "relapse_probability": 0.15,
    "dropout_probability": 0.25,
    "engagement_loss_probability": 0.18
  },
  "trends": [
    { "trend_id": "recovery_readiness", "score": 85, "direction_7d": "improving" },
    { "trend_id": "stress_load", "score": 28, "direction_7d": "declining" }
  ],
  "narrative": {
    "where_now": "…",
    "why_summary": "…",
    "awareness_flags": [],
    "risk": { "risk_elevated": false },
    "next_actions": []
  }
}
```

### 9.3 Narrative — five questions

| Field | Content |
|-------|---------|
| `where_now` | CRS band + pillar summary |
| `why_summary` | Top drivers mapped to Part1 categories |
| `awareness_flags` | Trend warnings (severity: info / warning / critical) |
| `risk` | `core_om_risk`, relapse probability, escalation flag |
| `next_actions` | Prioritized recommendations from pattern engine |

**Risk-elevated override:** When `core_om_risk ≥ 0.70`, narrative switches to escalation copy; scores capped at 40.

### 9.4 Pattern engine (L1)

Evaluates rules against L3 output:

| Pattern example | Trigger |
|-----------------|---------|
| `sleep_mood_coupled_decline` | `sleep_mood_coupled_decline = 1` |
| Motivation warning | Motivation Momentum delta < −15 in 7d |
| Capacity below baseline | Capacity < 30d average − threshold |

Patterns feed `awareness_flags` and `next_actions` — never recompute scores.

---

<!-- pagebreak -->

## 10. Implementation phases

### 10.1 Phase overview

| Phase | Weeks | Deliverable | Exit criteria |
|-------|-------|-------------|---------------|
| **1 — Foundation** | 1–4 | L0 + L2 + L3 rule-based | Pillars + readiness + trends in DB |
| **2 — ML Labels** | 5–8 | Labels + 4 trained models | Models in registry; AUC targets |
| **3 — Shadow** | 9–10 | CRS v2 shadow + narrative | Dual scores in API; narrative QA |
| **4 — Cutover** | 11+ | Production GA | `crs_primary=v2`; L1 API GA |
| **5 — v1.1 Expansion** | Ongoing | 70/70 Part1 attrs | `feature_v2.0.0` deployed |

```
Phase 1 → Phase 2 → Phase 3 → Phase 4
    ↓
Phase 5 (parallel after Phase 1 L0 patterns stable)
```

### 10.2 Phase 1 — Foundation (weeks 1–4)

**Layers:** L0, L2, L3 (rule-based only)

| Component | Scope |
|-----------|-------|
| L0 | v1 connectors: app, wearable, therapy, assessments, CRM |
| L0 | 34 staging fields; mood 0–10 → 0–5 |
| L2 | 34 v1 features; job at 02:00 UTC |
| L3 | 4 pillars + CRS readiness + 7 trends |
| L3 | Risk cap; `crs_primary = readiness` |

**Part1 attrs (~18):** A01–A07, A11, A13, A27–A29, A37, A43.

**Detailed TRD/HLD:** [Phase-01-Foundation/](./Phase-01-Foundation/)

### 10.3 Phase 2 — ML labels and training (weeks 5–8)

| Component | Scope |
|-----------|-------|
| L4 | Label job per §4.3 (R1–R4, L1–L5) |
| L4 | Train recovery, relapse, dropout, engagement_loss models |
| L4 | Model registry; point-in-time safe features |
| L4 | Inference stub (not yet headline CRS) |

**Detailed TRD/HLD:** [Phase-02-ML-Labels-Training/](./Phase-02-ML-Labels-Training/)

### 10.4 Phase 3 — CRS v2 shadow and narrative (weeks 9–10)

| Component | Scope |
|-----------|-------|
| L3 | CRS v2 composite live |
| L3 | Shadow: expose `crs_v2_score` alongside readiness |
| L1 | Five narrative questions §10.4 |
| L1 | Pattern engine v1 |

**Detailed TRD/HLD:** [Phase-03-CRS-v2-Shadow-Narrative/](./Phase-03-CRS-v2-Shadow-Narrative/)

### 10.5 Phase 4 — Production cutover (week 11+)

| Component | Scope |
|-----------|-------|
| L3 | `crs_primary = v2` when maturity rules met |
| L1 | `user_engine_snapshot` GA |
| L1 | API load test 10K RPM |
| Ops | Runbooks: ingestion fail, batch retry, model rollback |

**Detailed TRD/HLD:** [Phase-04-Production-Cutover/](./Phase-04-Production-Cutover/)

### 10.6 Phase 5 — v1.1 expansion (ongoing)

| Wave | Events | Attributes |
|------|--------|------------|
| 5A | lifestyle_checkin, game_session_completed | A12, A15–A20, A30–A32 |
| 5B | intake_form_submitted | A44–A64 |
| 5C | biomarker_result, PHQ-9/PTSD/ASRS | A08–A10, A21–A26 |
| 5D | journal NLP, app behaviour | A33–A42, A56 |
| 5E | therapist_profile_sync, session metrics | A66–A70 |

**Exit:** `feature_v2.0.0` + full §8.9 trend bindings.

**Detailed TRD/HLD:** [Phase-05-v1.1-Expansion/](./Phase-05-v1.1-Expansion/)

### 10.7 Phase-to-component matrix

| Component | P1 | P2 | P3 | P4 | P5 |
|-----------|----|----|----|----|-----|
| L0 connectors v1 | ● | | | | |
| L2 feature job v1 | ● | | | | |
| L3 pillars + readiness | ● | | | | |
| Label job + training | | ● | | | |
| ML inference | | ● | ● | ● | ● |
| CRS v2 composite | | | ● | ● | ● |
| Narrative API | | | ● | ● | ● |
| `crs_primary=v2` | | | | ● | |
| L0 v1.1 + L2 v2 | | | | | ● |

---

<!-- pagebreak -->

## 11. Engine Part1 attribute binding

**Normative detail:** [Engine-Part1-Full-Attribute-Binding-Spec.md](./Engine-Part1-Full-Attribute-Binding-Spec.md)

### 11.1 Binding policies

| Rule | Requirement |
|------|-------------|
| P1 | Every Part1 attribute → ≥1 state score (CRS readiness and/or pillar) |
| P2 | Trajectory-relevant attrs → ≥1 trend metric |
| P3 | Missing data → renormalize weights within block |
| P4 | `core_om_risk` → risk cap on all display scores |
| P5 | Spec = 100% coverage day one; implementation phased |

### 11.2 Complete attribute registry

| ID | Part1 name | L0 event | L2 feature | Phase |
|----|------------|----------|------------|-------|
| A01 | CORE-OM Overall | `assessment_completed` | `core_om_total_norm` | 1 |
| A02 | CORE-OM Functioning | `assessment_completed` | `core_om_functioning` | 1 |
| A03 | CORE-OM Problems | `assessment_completed` | `core_om_problems` | 1 |
| A04 | CORE-OM Wellbeing | `assessment_completed` | `core_om_wellbeing` | 1 |
| A05 | CORE-OM Risk | `assessment_completed` | `core_om_risk` | 1 |
| A06 | CORE-OM Delta | `assessment_completed` | `core_om_delta_30d` | 1 |
| A07 | Anxiety (GAD-7) | `assessment_completed` | `gad7_normalized_latest` | 1 |
| A08 | Depression (PHQ-9) | `assessment_completed` | `phq9_normalized_latest` | 5 |
| A09 | Trauma | `assessment_completed` | `trauma_score_latest` | 5 |
| A10 | ADHD (ASRS) | `assessment_completed` | `adhd_score_latest` | 5 |
| A11 | Sleep | `sleep_session` | `sleep_avg_7d`, `sleep_slope_7d` | 1 |
| A12 | Fatigue | `lifestyle_checkin` | `fatigue_score_7d` | 5 |
| A13 | HRV | `heart_rate_daily` | `hrv_avg`, `hrv_trend` | 1 |
| A14 | Pulse | `heart_rate_daily` | `resting_hr_avg`, `resting_hr_trend` | 5 |
| A15 | Exercise | `lifestyle_checkin` | `exercise_days_7d`, `exercise_minutes_7d` | 5 |
| A16 | Nutrition | `lifestyle_checkin` | `nutrition_score_7d` | 5 |
| A17 | Hydration | `lifestyle_checkin` | `hydration_score_7d` | 5 |
| A18 | Hunger | `lifestyle_checkin` | `hunger_level_7d` | 5 |
| A19 | Sun Exposure | `lifestyle_checkin` | `sun_exposure_minutes_7d` | 5 |
| A20 | Libido | `lifestyle_checkin` | `libido_level_14d` | 5 |
| A21 | Cortisol | `biomarker_result` | `biomarker_cortisol_latest` | 5 |
| A22 | Thyroid/TSH | `biomarker_result` | `biomarker_tsh_latest` | 5 |
| A23 | Blood Sugar | `biomarker_result` | `biomarker_glucose_latest` | 5 |
| A24 | Vitamin D | `biomarker_result` | `biomarker_vitd_latest` | 5 |
| A25 | HbA1c | `biomarker_result` | `biomarker_hba1c_latest` | 5 |
| A26 | Weight Change | `biomarker_result` | `weight_delta_90d` | 5 |
| A27 | Mood | `mood_checkin` | `mood_avg_14d`, `mood_slope_7d`, `mood_volatility_14d` | 1 |
| A28 | Motivation | `motivation_checkin` | `motivation_avg_14d`, `motivation_slope_7d` | 1 |
| A29 | Confidence | `confidence_checkin` | `confidence_avg_14d`, `confidence_slope_7d` | 1 |
| A30 | Memory Game | `game_session_completed` | `game_memory_score_7d`, `game_memory_slope_7d` | 5 |
| A31 | Connect Four | `game_session_completed` | `game_connect4_score_7d` | 5 |
| A32 | Whack A Mole | `game_session_completed` | `game_whack_score_7d`, `game_frustration_proxy` | 5 |
| A33 | Journal tone/themes | `journal_features_computed` | `journal_sentiment_7d`, `journal_stress_theme_flag` | 5 |
| A34 | Blank Slate Journal | `journal_entry` | `journal_blank_slate_sentiment_7d` | 5 |
| A35 | Letter to Self | `journal_entry` | `journal_letter_self_sentiment_7d` | 5 |
| A36 | Gratitude Journal | `journal_entry` | `journal_gratitude_sentiment_7d` | 5 |
| A37 | App engagement | `app_session` | `engagement_rate_7d`, `engagement_slope_7d` | 1 |
| A38 | Support-seeking | `app_session`, therapy | `support_seeking_rate_30d` | 5 |
| A39 | Guides usage | `content_viewed` | `guide_usage_rate_30d` | 5 |
| A40 | Focus behaviour | `app_session` | `focus_session_rate_7d` | 5 |
| A41 | Completion/drop-off | `app_session` | `task_completion_rate_7d`, `dropoff_rate_7d` | 5 |
| A42 | Check-in drop-off | check-in events | `checkin_completion_rate_7d` | 5 |
| A43 | Therapy attendance | `session_attended` | `therapy_attendance_rate_30d` | 1 |
| A44 | Therapy intent | `intake_form_submitted` | `form_therapy_intent_score` | 5 |
| A45 | Primary concern | `intake_form_submitted` | `form_primary_concern_severity` | 5 |
| A46 | Free-text concern | `intake_form_submitted` | `form_concern_nlp_severity` | 5 |
| A47 | Work-stress | `intake_form_submitted` | `form_work_stress_score` | 5 |
| A48 | Routine disruption | `intake_form_submitted` | `form_routine_disruption_flag` | 5 |
| A49 | Check-in burden | `intake_form_submitted` | `form_checkin_burden_score` | 5 |
| A50 | Overthinking | `intake_form_submitted` | `form_overthinking_score` | 5 |
| A51 | Decision fatigue | `intake_form_submitted` | `form_decision_fatigue_score` | 5 |
| A52 | Brain fog | `intake_form_submitted` | `form_brain_fog_score` | 5 |
| A53 | Work pressure | `intake_form_submitted` | `form_work_pressure_score` | 5 |
| A54 | Emotional triggers | `intake_form_submitted` | `form_emotional_triggers_score` | 5 |
| A55 | Relationship stress | `intake_form_submitted` | `form_relationship_stress_score` | 5 |
| A56 | Self-talk themes | journal + forms NLP | `form_self_talk_score` | 5 |
| A57 | Crisis marker | `intake_form_submitted` | `form_crisis_marker_flag` | 5 |
| A58 | Coping improvement | `intake_form_submitted` | `form_coping_improvement_score` | 5 |
| A59 | Coping behaviour | `intake_form_submitted` | `form_coping_score` | 5 |
| A60 | Trigger reduction | `intake_form_submitted` | `form_trigger_reduction_score` | 5 |
| A61 | Burnout | `intake_form_submitted` | `form_burnout_score` | 5 |
| A62 | Work functioning | `intake_form_submitted` | `form_work_functioning_score` | 5 |
| A63 | Routine difficulty | `intake_form_submitted` | `form_routine_difficulty_score` | 5 |
| A64 | Overwhelm | `intake_form_submitted` | `form_overwhelm_score` | 5 |
| A65 | Missed check-ins | staging rollup | `missed_checkin_days_7d` | 5 |
| A66 | Session missed | `session_missed` | `therapy_missed_rate_30d` | 5 |
| A67 | Days since session | therapy events | `days_since_last_session` | 5 |
| A68 | Therapist availability | `therapist_profile_sync` | `therapist_availability_score` | 5 |
| A69 | Affordability | `therapist_profile_sync` | `therapy_affordability_score` | 5 |
| A70 | Mode/language match | `therapist_profile_sync` | `therapist_match_score` | 5 |

---

<!-- pagebreak -->

## 12. Security, operations, and governance

### 12.1 Security

- TLS on all API paths; mTLS / API keys for connectors
- PHI encrypted at rest; journal blobs in separate store
- RBAC: API scoped by `user_id`; batch jobs use service accounts
- Biomarker ingestion requires `biomarker_consent = true` on user profile

### 12.2 Observability

| Signal | Alert threshold |
|--------|-----------------|
| Ingestion lag | > 15 min |
| Quarantine rate | > 2% daily |
| Batch job duration | SLA miss per stage |
| Null feature rate | > 15% any required column |
| CRS distribution drift | KL divergence > 0.1 |
| Model AUC | > 5% weekly drop |

### 12.3 Failure modes

| Failure | Recovery |
|---------|----------|
| Connector down | Retry + stale data flag on snapshot |
| Batch job fail | Idempotent rerun from failed stage |
| Model corrupt | Rollback `model_bundle_version` |
| Risk cap misconfig | Hotfix `score_version` |

### 12.4 Versioning governance

| Field | Bumped when |
|-------|-------------|
| `feature_version` | L2 formula or column change |
| `label_version` | Label rule change |
| `model_bundle_version` | Model retrain / deploy |
| `score_version` | L3 formula change |
| `trend_version` | Trend formula change |

All version fields mandatory on every `user_engine_snapshot`.

### 12.5 Migration — score coexistence

| Period | `crs_primary` | User experience |
|--------|---------------|-----------------|
| Phase 1 | `readiness` | Single rule-based CRS |
| Phase 3 | `readiness` (shadow v2) | Both scores visible to internal QA |
| Phase 4+ | `v2` | ML CRS headline; readiness in breakdown |

---

<!-- pagebreak -->

## Appendix A — Canonical data tables

| Table | Grain | Owner | Purpose |
|-------|-------|-------|---------|
| `raw.events` | event | L0 | Append-only event store |
| `staging.user_daily_activity` | user-day | L0 | Daily rollups for L2 |
| `features.user_features_daily` | user-day | L2 | Feature row |
| `ml.training_labels` | user-snapshot | L4 | Offline labels |
| `ml.model_registry` | model version | L4 | Model artifacts |
| `scoring.user_scores_daily` | user-day | L3 | Scores + trends |
| `user_engine_snapshot` | user-day | L1 | API read model |

---

## Appendix B — L0 event type catalog

| event_type | source_system | Version |
|------------|---------------|---------|
| `user_registered` | auth_crm | v1 |
| `user_profile_updated` | auth_crm | v1 |
| `user_churned` | auth_crm | v1 |
| `mood_checkin` | app_mobile, app_web | v1 |
| `motivation_checkin` | app_mobile, app_web | v1 |
| `confidence_checkin` | app_mobile, app_web | v1 |
| `app_session` | app_mobile, app_web | v1 |
| `journal_entry` | app_mobile | v1 |
| `journal_features_computed` | nlp_worker | v1 |
| `sleep_session` | wearable_* | v1 |
| `heart_rate_daily` | wearable_* | v1 |
| `activity_daily` | wearable_* | v1 |
| `session_scheduled` | therapy_platform | v1 |
| `session_attended` | therapy_platform | v1 |
| `session_missed` | therapy_platform | v1 |
| `assessment_completed` | assessments | v1 |
| `assessment_corrected` | assessments | v1 |
| `content_viewed` | content_engagement | v1 (optional) |
| `lifestyle_checkin` | app_mobile, lifestyle_tracker | **v1.1** |
| `game_session_completed` | games | **v1.1** |
| `intake_form_submitted` | forms, onboarding | **v1.1** |
| `biomarker_result` | lab_partner, health_sync | **v1.1** |
| `therapist_profile_sync` | therapy_platform, sheet_sync | **v1.1** |

---

## Appendix C — L2 feature registry summary

**v1.0.0 (34 columns):** Phase 1 — see §6.3  
**v2.0.0 (86 columns):** Phase 5 — v1 unchanged + 52 additive

Full registry with computation formulas: L2 spec §7.3–§7.5.  
Full lineage: L2 spec §11.

---

## Appendix D — Clinical label rules summary

| Label | Positive when | Censored when |
|-------|---------------|---------------|
| `recovery_label` | R1–R4 criteria met; risk guard passes | No follow-up assessment in window |
| `relapse_label` | L1–L5 criteria met | No follow-up assessment in window |
| `dropout_label` | Churned or 30d inactive | — |
| `engagement_loss_label` | 50%+ engagement drop | Insufficient baseline |

Full rules, pseudocode, worked examples: CRS Unified v3 §4.3.

---

## Appendix E — Version and audit fields

Every scoring output must include:

```
score_version
feature_version
model_bundle_version
trend_version
computed_at
```

Training rows additionally require: `label_version`, `label_censored_reason` (when applicable).

---

## Appendix F — Glossary

| Term | Definition |
|------|------------|
| **CRS** | Cognitive Readiness Score (0–100) |
| **CRS v2** | ML composite of four outcome probabilities |
| **CRS readiness** | Part1 rule-based same-day score |
| **Pillar** | One of four state dimensions (Clarity, Emotional Balance, Resilience, Capacity) |
| **Trend** | Trajectory metric with direction arrow |
| **MCID** | Minimum clinically important difference |
| **PIT** | Point-in-time — no future data leakage |
| **Censoring** | Label = null when follow-up data unavailable |
| **Risk cap** | All scores capped at 40 when `core_om_risk ≥ 0.70` |
| **Shadow period** | CRS v2 computed but readiness remains headline |
| **system_type** | 1 = wearable capable; 0 = web-only |
| **local_date** | Calendar date in user timezone for daily aggregation |

---

## Appendix G — Acceptance checklist

**Program-level sign-off:**

- [ ] End-to-end demo: event → snapshot → API for test user
- [ ] Clinical sign-off on label thresholds and risk cap
- [ ] Product sign-off on five narrative questions
- [ ] Load test: 10K RPM API read path
- [ ] Batch SLA: 03:30 UTC completion × 30 consecutive days
- [ ] Model monitoring dashboards live
- [ ] Runbooks: ingestion failure, batch retry, model rollback

**Spec completeness:**

- [x] 70/70 Part1 attributes bound (state + trajectory)
- [x] 86 L2 columns defined at `feature_v2.0.0`
- [x] L0 v1.1 event catalog (Appendix F in Data Ingestion spec)
- [x] L0 → L2 full lineage (L2 §11)
- [x] Phase TRD + HLD for Phases 01–05
- [x] CRS Unified v3 (dual CRS, labels, trends, API)

---

## Appendix H — Source document index

Use this master document for **orientation and review**. For implementation, the layer-specific specs remain authoritative.

| Document | Path | Role |
|----------|------|------|
| **This document** | `final/MindPeers-Engine-Master-Production-Spec.md` | Single combined program spec |
| **Development Roadmap (stakeholder)** | `final/Development-Roadmap-Stakeholder.md` | Plain-language timeline for Product, Clinical, Leadership |
| **Development Roadmap (technical)** | `final/Development-Roadmap.md` | Program schedule, milestones, gates |
| Master TRD | `final/00-Master-Program-TRD.md` | Program requirements |
| Master HLD | `final/00-Master-Program-HLD.md` | Architecture diagrams |
| CRS Unified v3 | `CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md` | L3/L4 scoring, labels, API (full detail) |
| Data Ingestion | `Data-Ingestion-Layer-Production-Spec.md` | L0 events, staging, validation |
| L2 Feature Store | `L2-Feature-Store-Production-Spec.md` | Feature registry, formulas, lineage |
| Part1 Binding | `final/Engine-Part1-Full-Attribute-Binding-Spec.md` | 70-attribute mandatory binding |
| Phase TRDs/HLDs | `final/Phase-*/` | Per-phase implementation specs |
| Architecture Index | `Engine-Architecture-Index.md` | Quick navigation |
| Engine Part1.docx | repo root | Source pillar weights and screens |
| ENGINE-POC | `ENGINE-POC-COMPLETE-DOCUMENTATION.md` | Historical POC reference |

---

## Revision history

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-05 | Initial master document — consolidates program TRD/HLD, layer specs, phases, 70-attribute binding |

---

*MindPeers Cognitive Readiness Engine — Master Production Specification v1.0.0*  
*For questions: Engineering (L0–L3), Data Platform (L2 batch), ML (L4), Clinical (labels + risk cap), Product (narrative + UX)*
