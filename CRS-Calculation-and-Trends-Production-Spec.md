# Cognitive Readiness Score (CRS) & Trend Metrics — Production Specification

**Version:** 1.0.0  
**Status:** Production-ready specification  
**Source artifacts:** `CRS Calculation with trends.docx`, `CRS Calculation.docx`, `ENGINE-POC-COMPLETE-DOCUMENTATION.md`  
**Audience:** Engineering, ML, Product, Clinical  
**Last updated:** 2026-06-05

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Design philosophy](#2-design-philosophy)
3. [The two-layer model: state vs trajectory](#3-the-two-layer-model-state-vs-trajectory)
4. [Data foundation: snapshots, features, and labels](#4-data-foundation-snapshots-features-and-labels)
5. [Outcome prediction models (L4 ML layer)](#5-outcome-prediction-models-l4-ml-layer)
6. [CRS calculation — composite of future probabilities](#6-crs-calculation--composite-of-future-probabilities)
7. [Secondary pillar scores (state layer)](#7-secondary-pillar-scores-state-layer)
8. [Trend metrics (trajectory layer)](#8-trend-metrics-trajectory-layer)
9. [End-to-end architecture](#9-end-to-end-architecture)
10. [API contracts and response examples](#10-api-contracts-and-response-examples)
11. [Normalization, bands, and direction](#11-normalization-bands-and-direction)
12. [Explainability (SHAP) and driver attribution](#12-explainability-shap-and-driver-attribution)
13. [Data maturity, cold start, and confidence](#13-data-maturity-cold-start-and-confidence)
14. [Versioning, monitoring, and governance](#14-versioning-monitoring-and-governance)
15. [Migration path from rule-based v1](#15-migration-path-from-rule-based-v1)
16. [Appendices](#16-appendices)

---

## 1. Executive summary

### 1.1 What CRS answers

**Cognitive Readiness Score (CRS)** is a single 0–100 score that answers:

> *What is the user's expected future trajectory in therapy and daily functioning?*

CRS is **not** a direct ML target. There is no ground-truth `crs_label` in historical data. Instead, CRS is a **deterministic composite** of four supervised outcome models trained on real business events:

| Outcome | Label question | Label type |
|---------|----------------|------------|
| **Recovery** | Did CORE-OM improve by more than threshold X? | Binary (0/1) |
| **Relapse** | Did CORE-OM worsen by more than threshold X? | Binary (0/1) |
| **Dropout** | Did the user leave therapy? | Binary (0/1) |
| **Engagement loss** | Did engagement drop more than 50%? | Binary (0/1) |

These labels are **natural, auditable business events** — not synthetic constructs — and make stronger ML targets than an arbitrarily defined readiness score.

### 1.2 What trend metrics answer

Trend metrics answer a different question:

> *Where is the user heading, regardless of how good they look right now?*

| Layer | Question | Examples |
|-------|----------|----------|
| **State (pillars)** | How is the user **right now**? | Clarity = 80, Emotional Balance = 72 |
| **Trajectory (trends)** | Where is the user **heading**? | Motivation Momentum = −25 (declining) |

A user can have high Clarity (80) but negative Motivation Momentum (−25). That combination means: *currently healthy, but deteriorating* — a clinically critical signal that state-only dashboards miss.

### 1.3 Recommended dashboard layout

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

### 1.4 Worked example — full user snapshot

**User 1001 on 2025-01-15** (45 days in program, wearable + app):

```json
{
  "user_id": "1001",
  "as_of_date": "2025-01-15",
  "cognitive_readiness_score": 81.2,
  "confidence_tier": "High",
  "pillars": {
    "clarity_score": 78,
    "emotional_balance_score": 72,
    "resilience_score": 80,
    "capacity_score": 74
  },
  "outcome_probabilities": {
    "recovery_probability": 0.82,
    "relapse_probability": 0.15,
    "dropout_probability": 0.25,
    "engagement_loss_probability": 0.18
  },
  "trends": {
    "recovery_readiness": { "score": 85, "band": "High", "direction_7d": "improving" },
    "stress_load": { "score": 28, "band": "Low", "direction_7d": "declining" },
    "sleep_consistency": { "score": 90, "band": "High", "direction_7d": "improving" },
    "energy_rhythm": { "score": 55, "band": "Moderate", "direction_7d": "stable" },
    "emotional_stability": { "score": 72, "band": "High", "direction_7d": "improving" },
    "motivation_momentum": { "score": 38, "band": "Moderate", "direction_7d": "declining" },
    "cognitive_momentum": { "score": 65, "band": "Moderate", "direction_7d": "improving" }
  }
}
```

**Clinical interpretation:** Strong current state and high CRS, but Motivation Momentum is declining — recommend proactive engagement intervention before dropout risk materializes.

---

## 2. Design philosophy

### 2.1 Why not train CRS directly?

**Anti-pattern (do not build):**

```
Features  →  ML Model  →  CRS
              ↑
         No CRS label exists
```

Training a model to predict CRS requires either:
- Synthetic labels (not grounded in outcomes), or
- Using CRS itself as a label (circular logic)

**Correct pattern:**

```
Features  →  Recovery Model    →  P(recovery)
         →  Relapse Model     →  P(relapse)
         →  Dropout Model     →  P(dropout)
         →  Engagement Model  →  P(engagement_loss)
                    ↓
         Deterministic CRS formula (weighted composite)
                    ↓
                  CRS (0–100)
```

CRS becomes **interpretable**: every point on the score maps to a weighted contribution from a real future outcome probability.

### 2.2 Why real labels beat synthetic scores

| Approach | Label source | Pros | Cons |
|----------|-------------|------|------|
| Synthetic CRS label | Rule-based formula applied retroactively | Easy to generate | Circular; model learns the formula, not outcomes |
| **Real outcome labels** | Dropout events, CORE-OM deltas, engagement drops | Grounded in business/clinical reality; auditable | Requires label engineering and threshold tuning |

**Example — label definition for Recovery:**

```
recovery_label = 1  IF  (core_om_score_at_T+30d - core_om_score_at_T) < -X
recovery_label = 0  OTHERWISE

Where X = clinically agreed minimum meaningful change (e.g., 5 points on CORE-OM)
```

**Example — label rows in training data:**

| user_id | snapshot_date | core_om_score | recovery_label | Notes |
|---------|---------------|---------------|----------------|-------|
| 1001 | 2024-10-01 | 22 | 1 | CORE-OM dropped to 16 by Nov 1 (−6) |
| 1002 | 2024-10-01 | 18 | 0 | CORE-OM stable at 17 by Nov 1 |
| 1003 | 2024-10-01 | 25 | 0 | User dropped out before 30d window → exclude or censor |

### 2.3 Determinism rule

Same inputs + same `score_version` + same model versions → **identical outputs**.

- Batch pipeline and API must use the same scoring code path.
- LLM/chat layer **must read** precomputed scores — never invent numbers.

---

## 3. The two-layer model: state vs trajectory

### 3.1 State layer — "Where am I now?"

Four pillar scores (0–100 each):

| Pillar | Domain focus | Primary question |
|--------|-------------|------------------|
| **Clarity** | Cognitive functioning | Can the user think clearly and organize daily life? |
| **Emotional Balance** | Emotional regulation | Are emotions stable and within a healthy range? |
| **Resilience** | Recovery & persistence | Can the user bounce back from setbacks? |
| **Capacity** | Behavioral bandwidth | Does the user have energy and engagement to act? |

### 3.2 Trajectory layer — "Where am I heading?"

Seven trend metrics (0–100 each + direction arrow):

| Trend metric | Pillar domain | Primary question |
|-------------|---------------|------------------|
| Recovery Readiness | Biological | How physiologically restored is the user? |
| Stress Load | Biological | Is physiological strain increasing or decreasing? |
| Sleep Consistency | Biological + Behavioral | Is sleep regular or chaotic? |
| Energy Rhythm | Behavioral | Is daily energy stable or boom-bust? |
| Emotional Stability | Psychological | Are emotions becoming more or less chaotic? |
| Motivation Momentum | Psychological + Behavioral | Is the user moving toward growth or withdrawal? |
| Cognitive Momentum | Cognitive | Is thinking becoming clearer or more fragmented? |

### 3.3 Why the distinction matters — three user archetypes

**Archetype A — "Stable and improving"**

```
Clarity = 78 ↑     Recovery Readiness = 85 ↑
Emotional Balance = 72 ↑    Stress Load = 28 ↓
CRS = 81
```

*Action:* Reinforce positive patterns; no urgent intervention.

**Archetype B — "Healthy now, declining trajectory" (critical)**

```
Clarity = 80        Motivation Momentum = 25 ↓
Emotional Balance = 75    Engagement slope = −5/day
CRS = 74 (still moderate-high)
```

*Action:* Proactive outreach — user looks fine on state scores but trajectory predicts dropout/engagement loss within 14–30 days.

**Archetype C — "Low state, recovering trajectory"**

```
Clarity = 45        Recovery Readiness = 72 ↑
Emotional Balance = 40    Emotional Stability = 68 ↑
CRS = 52
```

*Action:* Support recovery momentum; avoid alarmist messaging — trajectory is positive even though current state is low.

---

## 4. Data foundation: snapshots, features, and labels

### 4.1 Daily snapshot schema

Every user-day produces one row in the feature store with **features + labels** (labels used only for training, not inference):

```json
{
  "user_id": "1001",
  "snapshot_date": "2025-01-01",

  "sleep_avg_7d": 6.5,
  "sleep_slope_7d": -0.2,
  "sleep_consistency_7d": 0.82,
  "hrv_avg": 58,
  "hrv_trend_7d": 2.1,
  "resting_hr_trend": -0.5,

  "mood_avg_14d": 5.8,
  "mood_volatility_14d": 1.1,
  "mood_slope_7d": 0.15,

  "engagement_rate_7d": 0.72,
  "engagement_slope_7d": -5.0,
  "therapy_attendance_rate": 0.80,

  "core_om_score": 18,
  "core_om_trend_30d": -2.0,
  "gad7_score": 9,

  "dropout_label": 0,
  "recovery_label": 1,
  "relapse_label": 0,
  "engagement_loss_label": 0,

  "days_active": 45,
  "system_type": 1,
  "data_completeness_score": 0.82
}
```

### 4.2 Feature groups by domain

| Domain | Example features | Used by |
|--------|-----------------|---------|
| **Biological** | `sleep_avg_7d`, `sleep_slope_7d`, `hrv_avg`, `hrv_trend`, `resting_hr_trend` | Resilience pillar, Recovery Readiness, Stress Load |
| **Behavioral** | `engagement_rate_7d`, `engagement_slope_7d`, `therapy_attendance_rate`, `activity_trend` | Capacity pillar, Energy Rhythm, Motivation Momentum |
| **Psychological** | `mood_avg_14d`, `mood_volatility_14d`, `gad7_score`, `core_om_score` | Emotional Balance pillar, Emotional Stability |
| **Cognitive** | `core_om_functioning`, journal coherence, CogniArt features (future) | Clarity pillar, Cognitive Momentum |

### 4.3 Label definitions (production)

| Label | Field | Definition | Prediction horizon | Example threshold |
|-------|-------|------------|-------------------|-------------------|
| `recovery_label` | Binary | CORE-OM improved by > X points | 30 days | X = 5 (clinical sign-off required) |
| `relapse_label` | Binary | CORE-OM worsened by > X points | 30 days | X = 5 |
| `dropout_label` | Binary | User terminated therapy / no activity for Y days | 60 days | Y = 30 |
| `engagement_loss_label` | Binary | `engagement_rate` dropped > 50% vs 30d baseline | 14 days | 50% relative drop |

**Example — computing recovery_label:**

```python
# Pseudocode — label generation (offline, training pipeline only)
def compute_recovery_label(user_id, snapshot_date, horizon_days=30, threshold=5):
    score_now = get_core_om(user_id, snapshot_date)
    score_future = get_core_om(user_id, snapshot_date + horizon_days)

    if score_future is None:
        return None  # censored — exclude from training

    delta = score_future - score_now
    # Lower CORE-OM = better (distress reduction)
    return 1 if delta <= -threshold else 0
```

**Example — label distribution in a training cohort:**

| Label | Positive rate | Typical class balance |
|-------|--------------|----------------------|
| recovery_label | ~35% | Moderate imbalance — use class weights |
| relapse_label | ~12% | Imbalanced — stratified sampling |
| dropout_label | ~18% | Moderate |
| engagement_loss_label | ~22% | Moderate |

### 4.4 What makes a good trend feature?

Trend features must capture **movement**, not **state**:

| Bad (state) | Good (trend) | Why |
|-------------|-------------|-----|
| `stress = 65` | `stress_load_trend = +18%` | State tells you where they are; trend tells you direction |
| `mood_avg = 4.2` | `mood_slope_7d = −0.3/day` | Average mood hides deterioration |
| `sleep_hours = 7.0` | `sleep_duration_variance_14d = 1.8h` | Consistency matters more than one night's value |

Historical snapshots naturally encode direction, velocity, and acceleration:

```
sleep_avg_7d  = 6.5h   (recent)
sleep_avg_14d = 6.8h   (medium)
sleep_avg_30d = 7.2h   (baseline)

→ sleep_slope_7d = −0.2h/day  (declining)
→ sleep_delta_30d = −0.7h     (below personal baseline)
```

---

## 5. Outcome prediction models (L4 ML layer)

### 5.1 Model inventory

| Model ID | Target | Output | Algorithm (recommended) |
|----------|--------|--------|------------------------|
| `recovery_model_v1` | `recovery_label` | P(recovery) ∈ [0, 1] | Gradient boosted trees (XGBoost/LightGBM) |
| `relapse_model_v1` | `relapse_label` | P(relapse) ∈ [0, 1] | Gradient boosted trees |
| `dropout_model_v1` | `dropout_label` | P(dropout) ∈ [0, 1] | Gradient boosted trees |
| `engagement_loss_model_v1` | `engagement_loss_label` | P(engagement_loss) ∈ [0, 1] | Gradient boosted trees |

### 5.2 Training dataset structure

Each row = one snapshot. Features = all snapshot features. Label = outcome for that model.

**Recovery model training example:**

| Row | Features (abbreviated) | recovery_label |
|-----|------------------------|----------------|
| 1 | sleep=6.5, mood=5.8, engagement=0.72, core_om=18 | 1 |
| 2 | sleep=5.1, mood=3.2, engagement=0.41, core_om=24 | 0 |
| 3 | sleep=7.0, mood=6.1, engagement=0.85, core_om=15 | 1 |

### 5.3 Model 1 — Recovery probability

**Training:**

```
Input:  snapshot_features (all L2 features for user-day T)
Target: recovery_label (CORE-OM improved > X within 30d)
Output: recovery_probability ∈ [0, 1]
```

**Inference example:**

```json
{
  "user_id": "1001",
  "snapshot_date": "2025-01-15",
  "recovery_probability": 0.82,
  "model_version": "recovery_model_v1.2.0",
  "top_features": [
    { "feature": "mood_slope_7d", "shap_value": 0.12 },
    { "feature": "core_om_trend_30d", "shap_value": 0.09 },
    { "feature": "therapy_attendance_rate", "shap_value": 0.07 }
  ]
}
```

**Interpretation:** 82% predicted probability of clinically meaningful CORE-OM improvement in the next 30 days.

### 5.4 Model 2 — Relapse probability

**Training:**

```
Target: relapse_label (CORE-OM worsened > X within 30d)
```

**Inference example — high-risk user:**

```json
{
  "user_id": "2045",
  "snapshot_date": "2025-01-15",
  "relapse_probability": 0.67,
  "model_version": "relapse_model_v1.1.0",
  "top_features": [
    { "feature": "mood_volatility_14d", "shap_value": 0.15 },
    { "feature": "engagement_slope_7d", "shap_value": 0.11 },
    { "feature": "sleep_slope_7d", "shap_value": 0.08 }
  ]
}
```

**Interpretation:** 67% probability of clinical worsening — trigger Risk Watch pattern and therapist review.

### 5.5 Model 3 — Dropout probability

**Inference example:**

```json
{
  "user_id": "1001",
  "dropout_probability": 0.25
}
```

**Interpretation:** 25% chance of leaving therapy within the prediction window. Contributes to CRS via retention term `(1 − dropout_probability)`.

### 5.6 Model 4 — Engagement loss probability

**Inference example:**

```json
{
  "user_id": "1001",
  "engagement_loss_probability": 0.18
}
```

**Interpretation:** 18% chance of engagement dropping > 50%. Contributes to CRS via `(1 − engagement_loss_probability)`.

### 5.7 Combined model output (input to CRS)

```json
{
  "user_id": "1001",
  "snapshot_date": "2025-01-15",
  "outcome_probabilities": {
    "recovery_probability": 0.82,
    "relapse_probability": 0.15,
    "dropout_probability": 0.25,
    "engagement_loss_probability": 0.18
  },
  "model_bundle_version": "outcome_models_v1.2.0"
}
```

---

## 6. CRS calculation — composite of future probabilities

### 6.1 Formula

CRS is a **weighted linear composite** of four outcome-derived terms:

```
CRS = 0.40 × RecoveryProbability
    + 0.20 × (1 − DropoutProbability)
    + 0.20 × (1 − EngagementLossProbability)
    + 0.20 × (1 − RelapseProbability)
```

All probabilities are in [0, 1]. CRS output is scaled to **0–100**.

| Component | Weight | Meaning | Orientation |
|-----------|--------|---------|-------------|
| Recovery Potential | 40% | Likelihood of clinical improvement | Higher P(recovery) → higher CRS |
| Retention Probability | 20% | Likelihood of staying in therapy | Higher (1 − P(dropout)) → higher CRS |
| Engagement Stability | 20% | Likelihood of sustained engagement | Higher (1 − P(engagement_loss)) → higher CRS |
| Relapse Avoidance | 20% | Likelihood of avoiding worsening | Higher (1 − P(relapse)) → higher CRS |

**Rationale for 40/20/20/20 weighting:** Recovery is the primary clinical outcome and receives the largest weight. Retention, engagement, and relapse avoidance are equally important secondary factors that predict program success.

### 6.2 Step-by-step calculation example

**Given predictions:**

```json
{
  "recovery_probability": 0.82,
  "dropout_probability": 0.25,
  "engagement_loss_probability": 0.18,
  "relapse_probability": 0.15
}
```

**Step 1 — Convert to percentage-scale terms:**

| Term | Calculation | Value |
|------|-------------|-------|
| Recovery Potential | 0.40 × (0.82 × 100) | 32.8 |
| Retention Probability | 0.20 × ((1 − 0.25) × 100) = 0.20 × 75 | 15.0 |
| Engagement Stability | 0.20 × ((1 − 0.18) × 100) = 0.20 × 82 | 16.4 |
| Relapse Avoidance | 0.20 × ((1 − 0.15) × 100) = 0.20 × 85 | 17.0 |

**Step 2 — Sum:**

```
CRS = 32.8 + 15.0 + 16.4 + 17.0 = 81.2
```

**Step 3 — Round and persist:**

```json
{
  "cognitive_readiness_score": 81.2,
  "score_version": "crs_v2.0.0"
}
```

### 6.3 Worked examples — three user profiles

**User A — High readiness (CRS = 81.2)**

| Probability | Value | Contribution |
|-------------|-------|-------------|
| P(recovery) | 0.82 | 32.8 |
| P(dropout) | 0.25 | 15.0 |
| P(engagement_loss) | 0.18 | 16.4 |
| P(relapse) | 0.15 | 17.0 |
| **CRS** | | **81.2** |

**User B — At-risk (CRS = 48.6)**

| Probability | Value | Contribution |
|-------------|-------|-------------|
| P(recovery) | 0.35 | 14.0 |
| P(dropout) | 0.62 | 7.6 |
| P(engagement_loss) | 0.55 | 9.0 |
| P(relapse) | 0.48 | 10.4 |
| **CRS** | | **41.0** |

**User C — Recovering but fragile retention (CRS = 65.4)**

| Probability | Value | Contribution |
|-------------|-------|-------------|
| P(recovery) | 0.78 | 31.2 |
| P(dropout) | 0.45 | 11.0 |
| P(engagement_loss) | 0.30 | 14.0 |
| P(relapse) | 0.20 | 16.0 |
| **CRS** | | **72.2** |

*Note:* User C has strong recovery potential but elevated dropout risk — retention interventions would have the highest impact on CRS.

### 6.4 CRS band mapping

| Band | CRS range | User-facing label | Recommended action intensity |
|------|-----------|-------------------|------------------------------|
| High | 67–100 | "Strong readiness" | Reinforcement, advanced goals |
| Moderate | 34–66 | "Building readiness" | Guided support, monitor trends |
| Low | 0–33 | "Needs support" | Active intervention, therapist review |

### 6.5 Implementation pseudocode

```python
def compute_crs(
    recovery_prob: float,
    dropout_prob: float,
    engagement_loss_prob: float,
    relapse_prob: float,
    weights: dict = None
) -> float:
    w = weights or {
        "recovery": 0.40,
        "retention": 0.20,
        "engagement": 0.20,
        "relapse_avoidance": 0.20,
    }

    crs = (
        w["recovery"] * recovery_prob * 100
        + w["retention"] * (1 - dropout_prob) * 100
        + w["engagement"] * (1 - engagement_loss_prob) * 100
        + w["relapse_avoidance"] * (1 - relapse_prob) * 100
    )
    return round(crs, 1)
```

---

## 7. Secondary pillar scores (state layer)

Pillar scores represent **current state** and are derived from domain-specific models or deterministic formulas. They feed the dashboard "Where am I now?" section and complement (but do not replace) the ML-based CRS.

### 7.1 Pillar overview

| Pillar | ML target(s) | Primary features | v1 approach |
|--------|-------------|------------------|-------------|
| **Emotional Balance** | `recovery_label`, `relapse_label` | mood, GAD-7, CORE-OM, volatility | ML model or weighted formula |
| **Resilience** | `recovery_label` | sleep, HRV, engagement persistence, therapy consistency | ML model or weighted formula |
| **Capacity** | `engagement_loss_label`, `dropout_label` | engagement, attendance, activity | ML model or weighted formula |
| **Clarity** | No direct label (v1) | sleep, HRV, functioning, GAD-7 | Deterministic formula (v1); ML when labels available |

### 7.2 Emotional Balance

**Purpose:** How stable and healthy are the user's emotions right now?

**Features:**

| Feature | Example value | Role |
|---------|--------------|------|
| `mood_avg_14d` | 5.8 / 10 | Current emotional level |
| `mood_volatility_14d` | 1.1 | Emotional chaos (lower = better) |
| `gad7_score` | 9 | Anxiety load (lower = better) |
| `core_om_score` | 18 | Clinical distress (lower = better) |

**ML approach:** Train a model against `recovery_label` + `relapse_label` (multi-task or ensemble). Model output mapped to 0–100.

**Deterministic v1 fallback (weighted formula):**

```
Emotional_Balance = 0.25 × norm(mood_avg_14d)
                  + 0.25 × inv_norm(mood_volatility_14d)
                  + 0.25 × inv_norm(gad7_score)
                  + 0.25 × inv_norm(core_om_score)
```

**Example calculation:**

| Feature | Raw | Normalized (0–100) | Weight | Contribution |
|---------|-----|-------------------|--------|-------------|
| mood_avg_14d | 5.8 | 72 | 0.25 | 18.0 |
| mood_volatility_14d | 1.1 | 65 | 0.25 | 16.3 |
| gad7_score | 9 | 68 | 0.25 | 17.0 |
| core_om_score | 18 | 70 | 0.25 | 17.5 |
| **Emotional Balance** | | | | **68.8 → 69** |

### 7.3 Resilience

**Purpose:** Can the user recover from stress and maintain healthy routines?

**Features:**

| Feature | Example value | Role |
|---------|--------------|------|
| `sleep_avg_7d` | 6.5h | Recovery foundation |
| `sleep_slope_7d` | −0.2 | Sleep trend (positive slope = improving) |
| `therapy_attendance_rate` | 0.80 | Treatment consistency |
| `engagement_rate_7d` | 0.72 | Behavioral persistence |
| `hrv_avg` | 58ms | Physiological recovery capacity |

**Example calculation:**

| Feature | Raw | Normalized | Weight | Contribution |
|---------|-----|-----------|--------|-------------|
| sleep_avg_7d | 6.5h | 62 | 0.25 | 15.5 |
| sleep_slope_7d | −0.2 | 45 | 0.15 | 6.8 |
| therapy_attendance_rate | 0.80 | 80 | 0.20 | 16.0 |
| engagement_rate_7d | 0.72 | 72 | 0.20 | 14.4 |
| hrv_avg | 58 | 75 | 0.20 | 15.0 |
| **Resilience** | | | | **67.7 → 68** |

### 7.4 Capacity

**Purpose:** Does the user have behavioral bandwidth to engage and act?

**Features:**

| Feature | Example value | Role |
|---------|--------------|------|
| `engagement_rate_7d` | 0.72 | Current engagement level |
| `engagement_slope_7d` | −5.0 | Engagement direction |
| `therapy_attendance_rate` | 0.80 | Commitment to treatment |

**ML approach:** Train against `engagement_loss_label` + `dropout_label`.

**Example — declining capacity:**

```
engagement_rate_7d = 0.72  → 72
engagement_slope_7d = -5.0 → 30 (steep decline)
therapy_attendance_rate = 0.80 → 80

Capacity = 0.40 × 72 + 0.35 × 30 + 0.25 × 80 = 28.8 + 10.5 + 20.0 = 59.3
```

Despite reasonable current engagement (72), the steep negative slope pulls Capacity down to 59 — an early warning.

### 7.5 Clarity

**Purpose:** Can the user think clearly, focus, and organize daily functioning?

**Challenge:** No direct clarity label exists in the current MindPeers dataset.

**v1 recommendation:** Deterministic composite until CogniArt, journal NLP, or therapist ratings provide supervised labels.

**Feature tree (current + future):**

```
Clarity
├── Sleep (sleep_avg_7d, sleep_consistency)
├── HRV (hrv_avg — physiological readiness for cognition)
├── GAD-7 (gad7_score — anxiety impairs clarity)
├── CORE-OM functioning subscale
├── Journal Features (future — coherence, sentiment)
├── CogniArt Features (future — focus, decision-making tasks)
└── Therapist Ratings (future — clinical observation)
```

**v1 deterministic formula:**

```
Clarity = 0.30 × norm(sleep_avg_7d)
        + 0.20 × norm(hrv_avg)
        + 0.20 × inv_norm(gad7_score)
        + 0.30 × norm(core_om_functioning)
```

**Example:**

| Feature | Raw | Normalized | Weight | Contribution |
|---------|-----|-----------|--------|-------------|
| sleep_avg_7d | 7.2h | 78 | 0.30 | 23.4 |
| hrv_avg | 58 | 75 | 0.20 | 15.0 |
| gad7_score | 9 | 68 | 0.20 | 13.6 |
| core_om_functioning | 0.7 | 70 | 0.30 | 21.0 |
| **Clarity** | | | | **73.0 → 73** |

**Future:** When CogniArt and journal features are available, promote to ML model trained on therapist-rated clarity or functioning subscale changes.

---

## 8. Trend metrics (trajectory layer)

Trend metrics are **time-series constructs** — they measure direction, velocity, and stability over time. They are naturally computed from historical snapshots and are strong candidates for ML-generated or formula-based composites.

### 8.1 Trend framework summary

| # | Trend metric | Pillar | Score range | Key question |
|---|-------------|--------|-------------|-------------|
| 1 | Recovery Readiness | Biological | 0–100 | How restored is the body? |
| 2 | Stress Load | Biological | 0–100 | How much physiological strain? |
| 3 | Sleep Consistency | Biological + Behavioral | 0–100 | How regular is sleep? |
| 4 | Energy Rhythm | Behavioral | 0–100 | Is daily energy stable? |
| 5 | Emotional Stability | Psychological | 0–100 | Are emotions stabilizing? |
| 6 | Motivation Momentum | Psychological + Behavioral | 0–100 | Growth or withdrawal? |
| 7 | Cognitive Momentum | Cognitive | 0–100 | Is thinking clarifying? |

### 8.2 Trend metric 1 — Recovery Readiness

**Definition:** How restored and physiologically ready the person is for cognitive and emotional demands.

**Features:**

| Feature | Weight | Example |
|---------|--------|---------|
| `sleep_avg_7d` | 0.30 | 6.5h |
| `sleep_consistency_7d` | 0.25 | 0.82 (high = regular) |
| `hrv_avg` | 0.25 | 58ms |
| `recovery_score` | 0.10 | 72 (wearable-derived) |
| `resting_hr_trend` | 0.10 | −0.5 bpm/day (declining = good) |

**Output:** 0–100

**Interpretation examples:**

| Score | Band | Meaning |
|-------|------|---------|
| 85 | High | Highly recovered; body is ready for demanding days |
| 55 | Moderate | Partially recovered; monitor sleep and HRV |
| 35 | Low | Physiologically depleted; prioritize rest |

**Sample output:**

```json
{
  "trend_id": "recovery_readiness",
  "score": 85,
  "band": "High",
  "direction_7d": "improving",
  "available": true,
  "top_inputs": [
    { "feature": "sleep_avg_7d", "contribution": 0.30 },
    { "feature": "hrv_avg", "contribution": 0.25 }
  ]
}
```

### 8.3 Trend metric 2 — Stress Load

**Definition:** Ongoing physiological strain from anxiety, poor recovery, or environmental stressors.

**Features:**

| Feature | Weight | Orientation |
|---------|--------|-------------|
| `gad7_score` | 0.30 | Higher = more stress |
| `hrv_avg` | 0.25 | Lower HRV = more stress (inverted) |
| `hrv_trend` | 0.20 | Declining HRV = worsening (inverted) |
| `stress_assessment` | 0.15 | Self-reported stress |
| `sleep_deficit` | 0.10 | Cumulative sleep debt |

**Output:** 0–100 where **higher = more stress load**

**Interpretation examples:**

| Score | Band | Meaning |
|-------|------|---------|
| 75 | High | Overloaded — intervention recommended |
| 45 | Moderate | Manageable but monitor |
| 20 | Low | Low physiological strain |

**Example — user with rising stress:**

```
Week 1: Stress Load = 35 (Low)
Week 2: Stress Load = 48 (Moderate)    ← hrv_trend declining
Week 3: Stress Load = 62 (Moderate)    ← gad7_score rising
Week 4: Stress Load = 78 (High)        ← sleep_deficit accumulating

direction_7d = "declining" (score increasing = getting worse)
```

### 8.4 Trend metric 3 — Sleep Consistency

**Definition:** How regular and predictable the user's sleep schedule is.

**Features:**

| Feature | Weight | Example (good) | Example (poor) |
|---------|--------|---------------|----------------|
| `sleep_duration_variance` | 0.35 | 0.3h std dev | 2.1h std dev |
| `bedtime_variance` | 0.25 | 15 min | 90 min |
| `wake_time_variance` | 0.25 | 20 min | 120 min |
| `sleep_efficiency_variance` | 0.15 | 0.05 | 0.25 |

**Output:** 0–100 where **higher = more consistent**

**Interpretation examples:**

| Score | Meaning |
|-------|---------|
| 90 | Highly regular — bedtime within 15 min, wake within 20 min |
| 50 | Moderate variation — weekend drift |
| 20 | Chaotic — sleep schedule unpredictable |

**Example — two users with same average sleep:**

| User | sleep_avg_7d | Sleep Consistency | Why |
|------|-------------|-------------------|-----|
| A | 7.0h | 90 | Bedtime 10:30 ± 15 min every night |
| B | 7.0h | 25 | Mon 11pm, Tue 2am, Wed 9pm, Thu 1am |

Same average sleep, radically different consistency — only the trend metric captures this.

### 8.5 Trend metric 4 — Energy Rhythm

**Definition:** Is the user maintaining a healthy, sustainable daily energy pattern?

**Features:**

| Feature | Weight |
|---------|--------|
| `activity_trend` | 0.35 |
| `engagement_trend` | 0.30 |
| `fatigue_markers` | 0.20 |
| `completion_rate` | 0.15 |

**Question answered:** Is daily functioning stable or boom-bust?

**Pattern examples:**

**Good rhythm (score ≈ 82):**

```
Mon: ████████ High activity, high engagement
Tue: ███████░ High activity, high engagement
Wed: ████████ High activity, high engagement
Thu: ██████░░ Moderate (natural variation)
Fri: ███████░ High activity, high engagement
→ Stable, sustainable pattern
```

**Poor rhythm (score ≈ 35):**

```
Mon: ████████ High
Tue: ███░░░░░ Crash
Wed: ████████ High (compensating)
Thu: ██░░░░░░ Crash
Fri: ██████░░ Moderate recovery
→ Boom-bust cycle — unsustainable, predicts burnout
```

**Sample output:**

```json
{
  "trend_id": "energy_rhythm",
  "score": 35,
  "band": "Moderate",
  "direction_7d": "declining",
  "pattern_type": "boom_bust",
  "available": true
}
```

### 8.6 Trend metric 5 — Emotional Stability

**Definition:** Are emotions becoming more stable or more chaotic over time?

**Features:**

| Feature | Weight | Trend signal |
|---------|--------|-------------|
| `mood_volatility_14d` | 0.35 | Lower volatility = more stable |
| `mood_slope_7d` | 0.25 | Positive slope = improving mood |
| `core_om_trend` | 0.20 | Declining CORE-OM = improving |
| `gad7_trend` | 0.10 | Declining GAD-7 = improving |
| `journal_sentiment_trend` | 0.10 | Positive sentiment trend (future) |

**Question answered:** Is emotional regulation improving or deteriorating?

**Example — improving stability:**

```
Week 1: mood_volatility = 2.1, mood_slope = -0.3  →  Score = 42
Week 2: mood_volatility = 1.8, mood_slope = -0.1  →  Score = 51
Week 3: mood_volatility = 1.3, mood_slope = +0.1  →  Score = 63
Week 4: mood_volatility = 0.9, mood_slope = +0.2  →  Score = 74

direction_7d = "improving"
```

**Example — deteriorating stability (early relapse signal):**

```
Week 1: mood_volatility = 0.8  →  Score = 78
Week 2: mood_volatility = 1.2  →  Score = 65
Week 3: mood_volatility = 1.8  →  Score = 48
Week 4: mood_volatility = 2.4  →  Score = 32

direction_7d = "declining"  ← correlate with rising relapse_probability
```

### 8.7 Trend metric 6 — Motivation Momentum

**Definition:** Is the user moving toward growth and engagement, or toward withdrawal?

**Recommended rename:** Consider **"Motivation Momentum"** (drop "& Confidence") for clarity, unless confidence is a distinct measured signal.

**Features:**

| Feature | Weight | Source |
|---------|--------|--------|
| `engagement_rate` | 0.20 | App activity |
| `engagement_slope` | 0.25 | Engagement direction |
| `homework_completion` | 0.15 | Therapy tasks |
| `journal_language` | 0.10 | NLP sentiment/activation (future) |
| `goal_completion` | 0.15 | User-set goals |
| `session_attendance` | 0.15 | Therapy sessions |

**Question answered:** Growth vs withdrawal trajectory.

**Example — withdrawal pattern:**

```json
{
  "trend_id": "motivation_momentum",
  "score": 28,
  "band": "Low",
  "direction_7d": "declining",
  "signals": {
    "engagement_slope_7d": -5.0,
    "homework_completion_7d": 0.20,
    "session_attendance_30d": 0.60
  }
}
```

**Critical insight:** This metric often declines **before** state scores drop. In the source document example:

```
Clarity = 80 (looks good)
Motivation Momentum = -25 (declining)
→ User is deteriorating despite currently appearing healthy
```

### 8.8 Trend metric 7 — Cognitive Momentum (recommended addition)

**Definition:** Is the user's thinking becoming clearer or more fragmented?

**Rationale:** Clarity is a state pillar, but no trend metric currently tracks cognitive **trajectory**. This gap means users can show stable Clarity while cognitive function silently declines.

**Features (current + future):**

| Feature | Availability | Role |
|---------|-------------|------|
| `core_om_functioning_trend` | Now | Clinical functioning trajectory |
| `gad7_trend` | Now | Anxiety impact on cognition |
| `sleep_avg_trend` | Now | Sleep quality affects cognition |
| CogniArt task performance trend | Future | Direct cognitive measurement |
| Journal coherence trend | Future | NLP-derived thought organization |
| Therapist cognitive ratings | Future | Clinical observation |

**v1 formula (deterministic):**

```
Cognitive_Momentum = 0.40 × norm(core_om_functioning_trend)
                   + 0.30 × inv_norm(gad7_trend)
                   + 0.30 × norm(sleep_avg_trend)
```

**Question answered:** Is thinking becoming clearer or more fragmented?

**Example:**

| User | Clarity (state) | Cognitive Momentum (trend) | Interpretation |
|------|----------------|---------------------------|----------------|
| A | 78 | 72 ↑ | Stable clarity, improving trajectory |
| B | 80 | 35 ↓ | Looks clear now, but cognition declining |
| C | 45 | 68 ↑ | Low clarity, but recovering — encourage |

---

## 9. End-to-end architecture

### 9.1 System diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION                                │
│  Sleep │ Mood │ CORE-OM │ GAD-7 │ Engagement │ HRV │ Therapy │ App  │
└──────────────────────────────┬───────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────────┐
│                     L2 — FEATURE STORE                               │
│  Daily snapshots: averages, slopes, deltas, volatilities, flags      │
│  Millions of rows: (user_id, snapshot_date, features, labels)        │
└──────────────────────────────┬───────────────────────────────────────┘
                               ↓
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Recovery Model  │  │  Relapse Model  │  │ Dropout Model   │
│  → P(recovery)  │  │  → P(relapse)   │  │  → P(dropout)   │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ↓
                   ┌─────────────────────┐
                   │ Engagement Loss Model│
                   │ → P(engagement_loss) │
                   └──────────┬──────────┘
                              ↓
                   ┌─────────────────────┐
                   │   SHAP Explanations  │
                   │  (per-model drivers) │
                   └──────────┬──────────┘
                              ↓
          ┌───────────────────┼───────────────────┐
          ↓                   ↓                   ↓
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Secondary Scores│  │  Trend Metrics  │  │  CRS Calculation │
│ Clarity         │  │  Recovery Ready │  │  0.4×P(rec)     │
│ Emot. Balance   │  │  Stress Load    │  │  0.2×(1-P drop) │
│ Resilience      │  │  Sleep Consist. │  │  0.2×(1-P eng)  │
│ Capacity        │  │  Energy Rhythm  │  │  0.2×(1-P rel)  │
│                 │  │  Emot. Stability│  │                 │
│                 │  │  Motiv. Momentum│  │                 │
│                 │  │  Cognitive Mom. │  │                 │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ↓
                   ┌─────────────────────┐
                   │  user_engine_snapshot│
                   │  (daily batch persist)│
                   └──────────┬──────────┘
                              ↓
          ┌───────────────────┼───────────────────┐
          ↓                   ↓                   ↓
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  L1 Dashboard   │  │  Intent Engine  │  │  Action Engine  │
│  (PRD UI)       │  │  (LLM context)  │  │  (interventions)│
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 9.2 Batch pipeline schedule

| Step | Frequency | Latency target | Output |
|------|-----------|---------------|--------|
| L2 feature computation | Daily (02:00 UTC) | < 30 min for full cohort | Feature rows |
| ML model inference | Daily (02:30 UTC) | < 15 min | Outcome probabilities |
| L3 scoring (CRS + pillars + trends) | Daily (02:45 UTC) | < 10 min | Score snapshot |
| Pattern evaluation | Daily (03:00 UTC) | < 5 min | Pattern cards |
| Snapshot persist | Daily (03:05 UTC) | < 2 min | `user_engine_snapshot` row |

**Read API latency:** < 200ms p95 (read from precomputed snapshot).

### 9.3 Processing flow example

**Day T, 02:00 — Feature computation for user 1001:**

```
Input events (Jan 8–14):
  - Sleep: [6.8, 7.1, 6.5, 6.9, 7.0, 6.4, 6.5] hours
  - Mood check-ins: [5.5, 6.0, 5.8, 5.2, 6.1, 5.9, 5.7]
  - App opens: 5 of 7 days

Computed features:
  sleep_avg_7d = 6.6
  sleep_slope_7d = -0.05
  mood_avg_14d = 5.8
  mood_volatility_14d = 1.1
  engagement_rate_7d = 0.71
```

**Day T, 02:30 — Model inference:**

```
recovery_probability = 0.82
relapse_probability = 0.15
dropout_probability = 0.25
engagement_loss_probability = 0.18
```

**Day T, 02:45 — Scoring:**

```
CRS = 0.4×82 + 0.2×75 + 0.2×82 + 0.2×85 = 81.2
Clarity = 73, Emotional Balance = 69, Resilience = 68, Capacity = 59
Recovery Readiness = 85, Stress Load = 28, ...
```

**Day T, 03:05 — Persist snapshot → available via API at 03:10**

---

## 10. API contracts and response examples

### 10.1 GET `/users/{user_id}/engine/report`

**Query params:** `date` (optional, default today)

**Response:**

```json
{
  "user_id": "1001",
  "as_of_date": "2025-01-15",
  "computed_at": "2025-01-15T03:05:00Z",
  "score_version": "crs_v2.0.0",
  "model_bundle_version": "outcome_models_v1.2.0",
  "confidence_tier": "High",
  "data_maturity_stage": "full",

  "cognitive_readiness_score": 81.2,
  "crs_band": "High",

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

  "crs_breakdown": {
    "recovery_potential": 32.8,
    "retention_probability": 15.0,
    "engagement_stability": 16.4,
    "relapse_avoidance": 17.0
  },

  "trends": [
    {
      "trend_id": "recovery_readiness",
      "score": 85,
      "band": "High",
      "direction_7d": "improving",
      "available": true
    },
    {
      "trend_id": "stress_load",
      "score": 28,
      "band": "Low",
      "direction_7d": "declining",
      "available": true
    },
    {
      "trend_id": "sleep_consistency",
      "score": 90,
      "band": "High",
      "direction_7d": "improving",
      "available": true
    },
    {
      "trend_id": "energy_rhythm",
      "score": 55,
      "band": "Moderate",
      "direction_7d": "stable",
      "available": true
    },
    {
      "trend_id": "emotional_stability",
      "score": 72,
      "band": "High",
      "direction_7d": "improving",
      "available": true
    },
    {
      "trend_id": "motivation_momentum",
      "score": 38,
      "band": "Moderate",
      "direction_7d": "declining",
      "available": true
    },
    {
      "trend_id": "cognitive_momentum",
      "score": 65,
      "band": "Moderate",
      "direction_7d": "improving",
      "available": true
    }
  ],

  "drivers": {
    "biological_pct": 38,
    "behavioral_pct": 34,
    "psychological_pct": 28,
    "visible": true
  },

  "pattern_cards": [
    {
      "pattern_id": "motivation_decline_warning",
      "type": "warning",
      "title": "Engagement momentum declining",
      "summary": "Motivation Momentum dropped 15 points in 7 days despite stable Clarity."
    }
  ]
}
```

### 10.2 GET `/users/{user_id}/engine/trends/{trend_id}/series`

**Query params:** `days=30`

**Response:**

```json
{
  "trend_id": "emotional_stability",
  "user_id": "1001",
  "series": [
    { "date": "2024-12-16", "score": 42, "band": "Moderate" },
    { "date": "2024-12-23", "score": 51, "band": "Moderate" },
    { "date": "2024-12-30", "score": 63, "band": "Moderate" },
    { "date": "2025-01-06", "score": 68, "band": "High" },
    { "date": "2025-01-13", "score": 72, "band": "High" }
  ],
  "direction_7d": "improving",
  "baseline": 55
}
```

### 10.3 Cold-start response example

**User with 4 days active, web-only:**

```json
{
  "user_id": "3050",
  "as_of_date": "2025-01-15",
  "confidence_tier": "Limited",
  "data_maturity_stage": "cold_start",
  "cognitive_readiness_score": null,
  "pillars": {
    "clarity_score": 50,
    "emotional_balance_score": 50,
    "resilience_score": null,
    "capacity_score": 52
  },
  "outcome_probabilities": null,
  "trends": [
    {
      "trend_id": "emotional_stability",
      "score": 48,
      "band": "Moderate",
      "available": true
    },
    {
      "trend_id": "motivation_momentum",
      "available": false,
      "message": "Complete a few check-ins to unlock this trend."
    }
  ],
  "drivers": { "visible": false }
}
```

---

## 11. Normalization, bands, and direction

### 11.1 Feature normalization patterns

| Pattern | Applies to | Formula | Example |
|---------|-----------|---------|---------|
| **Linear scale** | Bounded metrics (mood 0–10, engagement 0–1) | `100 × clamp((value − min)/(max − min), 0, 1)` | mood=5.8 → 72 |
| **Inverted linear** | Lower-is-better (GAD-7, CORE-OM, volatility) | `100 − linear_scale(value)` | gad7=9 → 68 |
| **Slope centered** | Slopes and deltas | `50 + 50 × clamp(value/span, −1, 1)` | slope=−0.2 → 45 |
| **Flag penalty** | Binary flags | `100 − penalty` if active | withdrawal_flag=1 → 75 |

### 11.2 Band labels (universal)

| Band | Score range | UI color (suggested) |
|------|-------------|---------------------|
| Low | 0–33 | Amber |
| Moderate | 34–66 | Blue |
| High | 67–100 | Green |

**Exception:** Stress Load uses inverted semantics — High band = high stress = amber/warning color.

### 11.3 Direction calculation

Direction is computed from the 7-day delta of the trend score:

```python
def compute_direction(score_now, score_7d_ago, threshold=3):
    delta = score_now - score_7d_ago
    if delta > threshold:
        return "improving"
    elif delta < -threshold:
        return "declining"
    else:
        return "stable"
```

**Examples:**

| Trend | Score now | Score 7d ago | Delta | Direction |
|-------|-----------|-------------|-------|-----------|
| Recovery Readiness | 85 | 78 | +7 | improving ↑ |
| Stress Load | 28 | 35 | −7 | declining ↓ (good — stress decreasing) |
| Energy Rhythm | 55 | 53 | +2 | stable → |
| Motivation Momentum | 38 | 53 | −15 | declining ↓ |

---

## 12. Explainability (SHAP) and driver attribution

### 12.1 Per-model SHAP explanations

Each outcome model produces top feature contributions:

```json
{
  "model": "recovery_model_v1",
  "prediction": 0.82,
  "shap_explanations": [
    { "feature": "mood_slope_7d", "value": 0.15, "shap": +0.12, "direction": "positive" },
    { "feature": "therapy_attendance_rate", "value": 0.80, "shap": +0.07, "direction": "positive" },
    { "feature": "sleep_slope_7d", "value": -0.2, "shap": -0.05, "direction": "negative" }
  ]
}
```

**User-facing translation:**

> "Your recovery outlook is strong (82%). Improving mood over the past week and consistent therapy attendance are the biggest positive factors. Declining sleep is slightly reducing your score."

### 12.2 CRS driver breakdown (domain attribution)

Map features to three domains for the PRD "Biological / Behavioral / Psychological" breakdown:

| Domain | Example features | Typical share |
|--------|-----------------|---------------|
| Biological | sleep, HRV, resting HR, cortisol | 35–42% |
| Behavioral | engagement, attendance, activity | 28–35% |
| Psychological | mood, GAD-7, CORE-OM, motivation | 25–35% |

**Example output:**

```json
{
  "drivers": {
    "biological_pct": 38,
    "behavioral_pct": 34,
    "psychological_pct": 28,
    "visible": true,
    "copy": "Your readiness may be influenced by biological (38%), behavioral (34%), and psychological (28%) factors."
  }
}
```

**Visibility rules:**
- Hidden when `confidence_tier = Limited` or `days_active < 7`
- Copy uses "may be influenced by" — not causal medical claims

---

## 13. Data maturity, cold start, and confidence

### 13.1 Maturity stages

| Stage | days_active | Behavior |
|-------|------------|----------|
| **Cold start** | 0–7 | Cohort prior (50) for missing features; CRS unavailable; confidence = Limited |
| **Early** | 7–30 | Mix of personal + cohort prior; CRS available with Moderate confidence cap |
| **Full** | 30+ | Personal features only; High confidence possible |

### 13.2 Confidence tier rules

| Tier | Conditions |
|------|-----------|
| **Limited** | `days_active ≤ 7` OR `data_completeness_score < 0.4` |
| **Moderate** | `days_active ≤ 30` OR `data_completeness_score < 0.7` (and not Limited) |
| **High** | `days_active > 30` AND `data_completeness_score ≥ 0.7` |

### 13.3 Web-only users (`system_type = 0`)

- Exclude wearable-dependent features (HRV, resting HR, recovery score)
- Renormalize pillar and trend weights
- Never surface HRV-specific copy
- Biological trends use sleep-only proxy mode

**Example — web-only Recovery Readiness:**

```
Standard weights: sleep_delta(0.35) + sleep_avg(0.30) + HR(0.20) + persistence(0.15)
Web-only weights: sleep_delta(0.45) + sleep_avg(0.35) + persistence(0.20)
Footnote: "Based on sleep and mood signals."
```

---

## 14. Versioning, monitoring, and governance

### 14.1 Version identifiers

| Component | Version field | Bump trigger |
|-----------|--------------|-------------|
| CRS formula | `score_version` (e.g., `crs_v2.0.0`) | Weight changes, new components |
| Outcome models | `model_bundle_version` | Retraining, feature changes |
| Feature computation | `feature_version` | Formula or window changes |
| Trend composites | `trend_version` | Input weight changes |

### 14.2 Model monitoring (production)

| Metric | Alert threshold | Action |
|--------|----------------|--------|
| Prediction distribution drift | KL divergence > 0.1 vs training | Investigate feature drift |
| Label rate change | ±5% vs baseline | Retrain or recalibrate |
| Model AUC degradation | > 5% drop on holdout | Schedule retrain |
| CRS mean shift | ±3 points cohort-wide | Check upstream data pipeline |
| Missing feature rate | > 15% for any required feature | Alert data engineering |

### 14.3 Clinical governance

| Decision | Owner | Review cadence |
|----------|-------|---------------|
| Label thresholds (X for recovery/relapse) | Clinical lead | Quarterly |
| CRS weight allocation (40/20/20/20) | Product + Clinical | Semi-annual |
| Band cutoffs (33/66) | Product | Annual |
| New trend metric addition | Product + Clinical + Engineering | Ad hoc |

---

## 15. Migration path from rule-based v1

The existing POC specification (`ENGINE-POC-COMPLETE-DOCUMENTATION.md`) defines a **rule-based CRS**:

```
CRS_v1 = 0.25 × Clarity + 0.25 × Emotional_Balance + 0.25 × Resilience + 0.25 × Capacity
```

This document defines **CRS v2** as an ML-composite. Both can coexist during migration.

### 15.1 Comparison

| Aspect | CRS v1 (rule-based) | CRS v2 (ML-composite) |
|--------|--------------------|-----------------------|
| Formula | Weighted pillar average | Weighted outcome probabilities |
| Training required | No | Yes (4 outcome models) |
| Interpretability | Pillar-level | Outcome-level (recovery, retention, etc.) |
| Predictive power | Descriptive (current state) | Predictive (future trajectory) |
| Labels needed | None | 4 binary outcome labels |
| Cold start | Works immediately | Requires model maturity |

### 15.2 Recommended migration phases

| Phase | Timeline | Action |
|-------|----------|--------|
| **Phase 1** | Weeks 1–4 | Ship v1 rule-based CRS + trend metrics (deterministic) |
| **Phase 2** | Weeks 5–8 | Train outcome models on historical snapshots; validate AUC |
| **Phase 3** | Weeks 9–10 | Shadow-mode v2 CRS alongside v1; compare distributions |
| **Phase 4** | Week 11+ | Switch primary CRS to v2; keep v1 pillars as state layer |
| **Phase 5** | Ongoing | Promote pillar scores to ML as labels become available |

### 15.3 Dual-score period example

During Phase 3, snapshot includes both:

```json
{
  "cognitive_readiness_score_v1": 71,
  "cognitive_readiness_score_v2": 81.2,
  "crs_primary": "v2",
  "score_version": "crs_v2.0.0"
}
```

---

## 16. Appendices

### Appendix A — Complete feature registry (MindPeers v1)

| Canonical name | Type | Window | Used by |
|----------------|------|--------|---------|
| `sleep_avg_7d` | continuous | 7d | Resilience, Recovery Readiness, Clarity |
| `sleep_slope_7d` | slope | 7d | Resilience, Sleep Consistency |
| `sleep_consistency_7d` | continuous | 7d | Recovery Readiness, Sleep Consistency |
| `sleep_duration_variance` | continuous | 14d | Sleep Consistency |
| `hrv_avg` | continuous | 7d | Resilience, Recovery Readiness, Stress Load |
| `hrv_trend` | slope | 7d | Stress Load |
| `resting_hr_trend` | slope | 7d | Recovery Readiness |
| `mood_avg_14d` | continuous | 14d | Emotional Balance, Emotional Stability |
| `mood_volatility_14d` | continuous | 14d | Emotional Balance, Emotional Stability, Stress Load |
| `mood_slope_7d` | slope | 7d | Emotional Stability |
| `engagement_rate_7d` | rate | 7d | Capacity, Energy Rhythm, Motivation Momentum |
| `engagement_slope_7d` | slope | 7d | Capacity, Motivation Momentum |
| `therapy_attendance_rate` | rate | 30d | Resilience, Capacity, Motivation Momentum |
| `core_om_score` | clinical | latest | Emotional Balance |
| `core_om_functioning` | clinical | latest | Clarity, Cognitive Momentum |
| `core_om_trend` | delta | 30d | Emotional Stability, Cognitive Momentum |
| `gad7_score` | clinical | latest | Emotional Balance, Stress Load, Cognitive Momentum |
| `gad7_trend` | slope | 30d | Emotional Stability, Cognitive Momentum |

### Appendix B — Label generation SQL (reference)

```sql
-- Recovery label: CORE-OM improved by > 5 points within 30 days
SELECT
    s.user_id,
    s.snapshot_date,
    CASE
        WHEN f.core_om_score IS NOT NULL
         AND (s.core_om_score - f.core_om_score) >= 5
        THEN 1 ELSE 0
    END AS recovery_label
FROM snapshots s
LEFT JOIN snapshots f
    ON s.user_id = f.user_id
   AND f.snapshot_date = s.snapshot_date + INTERVAL '30 days'
WHERE s.snapshot_date <= CURRENT_DATE - INTERVAL '30 days';
```

### Appendix C — CRS quick-reference card

```
┌─────────────────────────────────────────────────┐
│           CRS CALCULATION (v2)                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  CRS = 0.40 × P(recovery)                       │
│      + 0.20 × (1 − P(dropout))                  │
│      + 0.20 × (1 − P(engagement_loss))          │
│      + 0.20 × (1 − P(relapse))                  │
│                                                 │
│  Scale: 0–100                                   │
│  Bands: Low (0-33) | Mod (34-66) | High (67+)  │
│                                                 │
│  State layer: Clarity, Balance, Resilience,     │
│               Capacity (0–100 each)             │
│                                                 │
│  Trend layer: 7 trajectory metrics with         │
│               direction arrows (↑ ↓ →)          │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Appendix D — Glossary

| Term | Definition |
|------|-----------|
| **CRS** | Cognitive Readiness Score — composite 0–100 predicting future trajectory |
| **Pillar** | One of four state scores: Clarity, Emotional Balance, Resilience, Capacity |
| **Trend metric** | Time-series composite measuring direction of change |
| **Snapshot** | One row of features + labels for a user on a specific date |
| **Outcome model** | ML classifier predicting a binary business/clinical label |
| **SHAP** | SHapley Additive exPlanations — feature attribution for model predictions |
| **Direction** | 7-day trend of a metric: improving, stable, or declining |
| **Band** | Categorical label (Low/Moderate/High) derived from score range |
| **Cohort prior** | Default score (50) used during cold start for missing features |

### Appendix E — Revision history

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-06-05 | Engineering | Initial production spec from `CRS Calculation with trends.docx` |

---

*This document is the authoritative production specification for CRS calculation and trend metrics. For implementation details of the L2 feature store, L3 scoring service batch pipeline, and L1 API contracts, see `ENGINE-POC-COMPLETE-DOCUMENTATION.md`.*
