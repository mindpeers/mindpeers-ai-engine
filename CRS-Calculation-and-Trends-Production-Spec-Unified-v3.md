# Cognitive Readiness Score (CRS) & Trend Metrics — Unified Production Specification

**Version:** 3.0.0 (Unified)  
**Status:** Production-ready — integrates CRS v2 ML pipeline + Engine Part1 product model + clinical labels v2  
**Supersedes:** [CRS-Calculation-and-Trends-Production-Spec.md](./CRS-Calculation-and-Trends-Production-Spec.md) v2.0.0 (retained as reference)  
**Source artifacts:**

| Artifact | Role in this spec |
|----------|-------------------|
| `CRS Calculation with trends.docx` | CRS v2 formula, 7 trend metrics |
| `CRS Calculation.docx` | Original CRS framework |
| `Engine Part1.docx` | Pillar definitions, input catalogs, 5-category weights, product screens |
| `ENGINE-POC-COMPLETE-DOCUMENTATION.md` | L1–L3 POC, feature registry |
| [L2-Feature-Store-Production-Spec.md](./L2-Feature-Store-Production-Spec.md) | 34-column feature row |
| [Data-Ingestion-Layer-Production-Spec.md](./Data-Ingestion-Layer-Production-Spec.md) | L0 events, label sources |

**Related layers:** L0 Ingestion → L2 Feature Store → L4 ML (labels + models) → L3 Scoring → L1 Engine  
**Audience:** Engineering, ML, Product, Clinical, Design  
**Last updated:** 2026-06-05

---

## Document map — what this unified spec covers

| Layer | Question answered | Primary sections |
|-------|-------------------|------------------|
| **Product narrative** | Why am I here? What should I do? | §1.5, §10.4 |
| **State (pillars)** | Where am I right now? | §7, Appendix F |
| **Trajectory (CRS v2)** | Where am I heading? | §5, §6 |
| **Trends** | Which direction per domain? | §8 |
| **Risk & safety** | What is the risk? | §4.3, §7.7, §11.4 |
| **Data & labels** | How are scores grounded? | §4, Appendix B |
| **API & UX** | What does the client receive? | §10 |

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Design philosophy](#2-design-philosophy)
3. [The three-layer model: state, trajectory, narrative](#3-the-three-layer-model-state-trajectory-narrative)
4. [Data foundation: snapshots, features, and labels](#4-data-foundation-snapshots-features-and-labels)
5. [Outcome prediction models (L4 ML layer)](#5-outcome-prediction-models-l4-ml-layer)
6. [CRS calculation — dual model (ML v2 + rule-based readiness)](#6-crs-calculation--dual-model-ml-v2--rule-based-readiness)
7. [Pillar scores (state layer) — Engine Part1 model](#7-pillar-scores-state-layer--engine-part1-model)
8. [Trend metrics (trajectory layer)](#8-trend-metrics-trajectory-layer)
9. [End-to-end architecture](#9-end-to-end-architecture)
10. [API contracts and response examples](#10-api-contracts-and-response-examples)
11. [Normalization, bands, direction, and risk caps](#11-normalization-bands-direction-and-risk-caps)
12. [Explainability (SHAP) and driver attribution](#12-explainability-shap-and-driver-attribution)
13. [Data maturity, cold start, and confidence](#13-data-maturity-cold-start-and-confidence)
14. [Versioning, monitoring, and governance](#14-versioning-monitoring-and-governance)
15. [Migration and score coexistence](#15-migration-and-score-coexistence)
16. [Appendices](#16-appendices) — includes [F: Part1 input registry](#appendix-f--engine-part1-input-registry), [G: Screen lineage](#appendix-g--screen--l0--l2-lineage)

---

## 1. Executive summary

### 1.1 What CRS answers

**Cognitive Readiness Score (CRS)** is a single 0–100 score that answers:

> *What is the user's expected future trajectory in therapy and daily functioning?*

CRS is **not** a direct ML target. There is no ground-truth `crs_label` in historical data. Instead, CRS is a **deterministic composite** of four supervised outcome models trained on real business events:

| Outcome | Label question | Label type |
|---------|----------------|------------|
| **Recovery** | Clinically meaningful improvement on CORE-OM (subscales + total) with GAD-7 confirmers — see [§4.3](#43-clinical-outcome-labels-production-specification) | Binary (0/1) / censored |
| **Relapse** | Meaningful CORE-OM worsening, risk elevation, or GAD-7 worsening — see [§4.3](#43-clinical-outcome-labels-production-specification) | Binary (0/1) / censored |
| **Dropout** | Did the user leave therapy or become inactive? | Binary (0/1) |
| **Engagement loss** | Did engagement drop more than 50% vs baseline? | Binary (0/1) |

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

### 1.5 Five questions the report must answer (Engine Part1)

Every engine report — API, dashboard, or therapist view — must support these user-facing questions:

| # | Question | Primary data source | CRS unified section |
|---|----------|---------------------|---------------------|
| 1 | **Where am I right now?** | 4 pillar scores + bands | §7 pillars, API `pillars` |
| 2 | **Why am I here?** | Top drivers by input category | §12 SHAP + §10.4 `narrative.why` |
| 3 | **What should I be aware of?** | Declining trends, volatility flags | §8 trends, API `trends`, `awareness_flags` |
| 4 | **What is the risk?** | P(relapse), CORE-OM risk, escalation | §4.3, §7.7, API `risk` |
| 5 | **What should I do next?** | L1 patterns + pillar-specific actions | §10.4 `narrative.next_actions` |

**Copy rule:** Scores describe *readiness and trajectory* — never diagnosis. Use "may be influenced by" not "caused by."

### 1.6 Product surfaces → data pipeline (Engine Part1)

| Product screen | User actions | L0 events | L2 / scoring use |
|----------------|-------------|-----------|-------------------|
| **Daily Check-in** | Mood, motivation, confidence | `mood_checkin`, `motivation_checkin`, `confidence_checkin` | Emotional Balance, Capacity, trends |
| **Assessment** | CORE-OM, GAD-7, PHQ-9, trauma | `assessment_completed` | All pillars, labels §4.3, risk cap §7.7 |
| **Lifestyle Tracker** | Sleep, fatigue, HRV, pulse, exercise, nutrition, hydration | `sleep_session`, `heart_rate_daily`, lifestyle events | CRS readiness, Clarity, Resilience, Capacity |
| **Games** | Memory Game, Connect Four, Whack A Mole | `game_session_completed` (v1.1) | Clarity, Emotional Balance |
| **Journaling** | Blank Slate, Letter to Self, Gratitude | `journal_entry`, `journal_features_computed` | Emotional Balance, Resilience |
| **Forms / Intake** | Therapy intent, concerns, burnout patterns | `intake_form_submitted` (v1.1) | All pillars — Forms category 15–20% |
| **Therapy / Sessions** | Book, attend, cancel sessions | `session_attended`, `session_missed` | Capacity, dropout label, Therapist category |
| **Biomarkers** | Cortisol, TSH, blood sugar, Vit D, HbA1c | `biomarker_result` (v1.1) | Lifestyle+Biomarker category 20–30% |

Full lineage: [Appendix G — Screen → L0 → L2 lineage](#appendix-g--screen--l0--l2-lineage).

### 1.7 Unified score stack (v3)

```
┌─────────────────────────────────────────────────────────────────┐
│  NARRATIVE LAYER     Why / Aware / Risk / Next (§1.5, §10.4)   │
├─────────────────────────────────────────────────────────────────┤
│  TRAJECTORY          CRS v2 (ML) + 7 trend metrics (§6, §8)    │
├─────────────────────────────────────────────────────────────────┤
│  STATE               4 pillars — Part1 category weights (§7)  │
├─────────────────────────────────────────────────────────────────┤
│  DATA                L0 → L2 features + offline labels (§4)   │
└─────────────────────────────────────────────────────────────────┘
```

**CRS headline (production):** `cognitive_readiness_score` = CRS v2 ML composite (§6.1) after model maturity.  
**CRS readiness (same-day):** `crs_readiness_score` = Part1 rule-based blend (§6.6) — cold start + explainability.  
**Display rule:** Apply risk cap (§7.7) to **both** before user-facing output.

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

**Example — label definition for Recovery (see §4.3 for full rules):**

Recovery and relapse labels compare a **baseline assessment at snapshot date T** with a **follow-up assessment** roughly 30 days later (any date in **T+21 to T+45**). CORE-OM total alone is not sufficient — subscales matter too.

#### 2.2.1 Glossary — terms used in label rules

| Term | Definition | Example in this spec |
|------|------------|----------------------|
| **CORE-OM** | Clinical Outcome in Routine Evaluation — a standardized questionnaire measuring psychological distress and functioning. Users complete it in the app; scores are stored as `assessment_completed` events. | Total score 22 at baseline, 17 at follow-up |
| **Subscale** | A **section** of CORE-OM measuring one domain. We use four subscales, each stored as a **normalized** score between 0 and 1. | `wellbeing_norm = 0.45`, `problems_norm = 0.55` |
| **Total score** | The overall CORE-OM score in **raw points** (not 0–1). On CORE-OM, **lower total = less distress = better**. | 22 → 17 is improvement (dropped by 5) |
| **Normalized score** | Subscale value rescaled to **0.0–1.0** so different subscales are comparable. Stored in L2 as `core_om_wellbeing`, `core_om_problems`, etc. | `problems_norm = 0.55` means moderate problem level |
| **MCID** | **Minimum Clinically Important Difference** — the smallest change we treat as *meaningful*, not noise. Below MCID = "stable"; at or above MCID = "meaningful change." | Total MCID = 5 points; subscale MCID = 0.10 |
| **Snapshot date (T)** | The date of the training row — "what did we know about the user on this day?" Labels look **forward** from T. | `snapshot_date = 2024-10-01` |
| **Follow-up** | The next CORE-OM assessment in window **[T+21d, T+45d]**, picked as closest to T+30d. | Assessment on 2024-10-31 for T = 2024-10-01 |
| **Assessment window** | Valid follow-up must fall between 21 and 45 days after T. Avoids labeling from assessments too early or too late. | T = Oct 1 → valid follow-up Oct 22 – Nov 15 |
| **Censoring (`null`)** | When we **cannot** assign a clinical label because follow-up data is missing. `null` ≠ 0. Censored rows are **excluded** from recovery/relapse model training. | User never retook CORE-OM → `recovery_label = null` |
| **Risk guard** | Safety check: even if scores improved, we **block** recovery if the **risk subscale** at follow-up is ≥ 0.70 (elevated risk). | Problems improved but `risk_norm = 0.72` → not recovery |
| **GAD-7** | Generalized Anxiety Disorder 7-item scale. Used as a **secondary confirmer** for recovery when CORE-OM follow-up is missing. Lower GAD-7 = less anxiety = better. | GAD-7: 12 → 7 (drop of 5 ≥ MCID 4) |
| **R1–R4** | **Recovery** rules — any one can trigger `recovery_label = 1` (with guards). | R1 = total improved by ≥ 5 points |
| **L1–L5** | **Relapse** rules — any one can trigger `relapse_label = 1`. Checked **before** recovery. | L3 = risk subscale ≥ 0.70 at follow-up |
| **Precedence** | Relapse is evaluated first. If relapse fires, recovery cannot be 1. | L3 true → `relapse=1`, `recovery=0` even if R2 also true |

#### 2.2.2 CORE-OM structure — four subscales and direction of improvement

When a user completes CORE-OM, we store **one total score** and **four subscales**:

| Subscale | L2 column | What it measures | Higher score means | Improvement direction |
|----------|-----------|------------------|--------------------|-----------------------|
| **Wellbeing** | `core_om_wellbeing` | General positive mental state | Better wellbeing | **Increase** by ≥ 0.10 (R3) |
| **Problems** | `core_om_problems` | Distress, symptoms, difficulties | More problems / worse | **Decrease** by ≥ 0.10 (R2) |
| **Functioning** | `core_om_functioning` | Daily functioning, getting things done | Better functioning | **Increase** by ≥ 0.10 (R4) |
| **Risk** | `core_om_risk` | Risk-related items (self-harm, etc.) | Higher risk | **Decrease** is good; ≥ 0.70 at follow-up blocks recovery and may trigger relapse (L3) |

**Why subscales matter:** Total score can stay flat while subscales move in opposite directions.

```
Example — mixed subscales, total unchanged:
  T:       problems=0.60, functioning=0.55, total=20
  T+30:    problems=0.42, functioning=0.40, total=20

  Problems improved (−0.18) but functioning worsened (−0.15)
  → Neither recovery nor relapse (stable), NOT censored
  → recovery_label = 0, relapse_label = 0
```

#### 2.2.3 Recovery rules R1–R4 — detailed with examples

**Rule:** `recovery_label = 1` requires **at least one** of R1–R4 to be true, **plus** risk guard (risk < 0.70 at follow-up) and **no** relapse (L1–L5).

Default MCID values: total = **5 points**; each subscale = **0.10** normalized.

---

**R1 — Total CORE-OM improvement**

| | |
|---|---|
| **Formula** | `(total_followup − total_T) ≤ −5` |
| **Meaning** | Overall distress dropped by at least 5 raw points |
| **Passes?** | Total fell by 5 or more |

```
Example — R1 PASS → contributes to recovery_label = 1:
  T:        total = 22
  Follow-up: total = 16     → delta = 16 − 22 = −6  (≤ −5) ✓
  risk at follow-up = 0.15  (< 0.70) ✓
  No L1–L5 fired            ✓
  → recovery_label = 1
```

```
Example — R1 FAIL (change too small):
  T:        total = 18
  Follow-up: total = 16     → delta = −2  (needs ≤ −5) ✗
  → R1 does not fire; check R2–R4 instead
```

---

**R2 — Problems subscale improvement**

| | |
|---|---|
| **Formula** | `(problems_followup − problems_T) ≤ −0.10` |
| **Meaning** | Reported problems/distress **decreased** meaningfully |
| **Direction** | Lower problems score = better (problems is inverse) |

```
Example — R2 PASS (total barely moved, problems improved):
  T:        total = 20, problems_norm = 0.55
  Follow-up: total = 19, problems_norm = 0.38  → problems delta = −0.17 ✓
  risk = 0.20, no relapse rules                  ✓
  → recovery_label = 1 via R2 (even though R1 failed — total only −1)
```

---

**R3 — Wellbeing subscale improvement**

| | |
|---|---|
| **Formula** | `(wellbeing_followup − wellbeing_T) ≥ +0.10` |
| **Meaning** | General wellbeing **increased** meaningfully |
| **Direction** | Higher wellbeing = better |

```
Example — R3 PASS:
  T:        wellbeing_norm = 0.40
  Follow-up: wellbeing_norm = 0.52  → delta = +0.12 ✓
  problems, functioning unchanged; risk = 0.25; no relapse ✓
  → recovery_label = 1 via R3
```

---

**R4 — Functioning subscale improvement**

| | |
|---|---|
| **Formula** | `(functioning_followup − functioning_T) ≥ +0.10` |
| **Meaning** | Ability to function in daily life **increased** meaningfully |
| **Direction** | Higher functioning = better |

```
Example — R4 PASS:
  T:        functioning_norm = 0.48
  Follow-up: functioning_norm = 0.61  → delta = +0.13 ✓
  → recovery_label = 1 via R4
```

```
Example — R4 FAIL (improvement below MCID):
  T:        functioning_norm = 0.50
  Follow-up: functioning_norm = 0.57  → delta = +0.07 (< 0.10) ✗
  → R4 does not fire
```

---

**Summary — R1–R4 at a glance**

| Rule | What improved | Condition (default MCID) | Example delta that PASSES |
|------|---------------|--------------------------|---------------------------|
| **R1** | Total score | Drop ≥ 5 points | 22 → 16 (−6) |
| **R2** | Problems | Drop ≥ 0.10 norm | 0.55 → 0.38 (−0.17) |
| **R3** | Wellbeing | Rise ≥ 0.10 norm | 0.40 → 0.52 (+0.12) |
| **R4** | Functioning | Rise ≥ 0.10 norm | 0.48 → 0.61 (+0.13) |

**Only one rule needs to pass** — they are connected by **OR**, not AND.

#### 2.2.4 Relapse rules L1–L5 — detailed with examples

**Rule:** Relapse is checked **before** recovery. If **any** L1–L5 is true → `relapse_label = 1` and `recovery_label = 0`, regardless of R1–R4.

---

**L1 — Total CORE-OM worsening**

| | |
|---|---|
| **Formula** | `(total_followup − total_T) ≥ +5` |
| **Meaning** | Overall distress increased by at least 5 points |

```
Example — L1 PASS:
  T:        total = 15
  Follow-up: total = 21  → delta = +6 ✓
  → relapse_label = 1, recovery_label = 0
```

---

**L2 — Problems subscale worsening**

| | |
|---|---|
| **Formula** | `(problems_followup − problems_T) ≥ +0.10` |
| **Meaning** | Problems/distress **increased** meaningfully |

```
Example — L2 PASS:
  T:        problems_norm = 0.30
  Follow-up: problems_norm = 0.45  → delta = +0.15 ✓
  → relapse_label = 1
```

---

**L3 — Risk elevation at follow-up**

| | |
|---|---|
| **Formula** | `risk_followup ≥ 0.70` |
| **Meaning** | Risk subscale is **high** at follow-up — even if total score barely changed |

```
Example — L3 PASS (critical case — total almost flat):
  T:        total = 18, risk_norm = 0.25
  Follow-up: total = 19, risk_norm = 0.72  → total delta +1 (L1 ✗) but risk ≥ 0.70 ✓
  → relapse_label = 1, recovery_label = 0
```

This is why **risk guard** exists for recovery: a user cannot be labeled "recovered" while risk ≥ 0.70.

---

**L4 — Risk increase (delta)**

| | |
|---|---|
| **Formula** | `(risk_followup − risk_T) ≥ +0.15` |
| **Meaning** | Risk **rose meaningfully** even if absolute level still below 0.70 |

```
Example — L4 PASS:
  T:        risk_norm = 0.20
  Follow-up: risk_norm = 0.38  → delta = +0.18 ✓
  → relapse_label = 1
```

---

**L5 — GAD-7 worsening (secondary — when CORE-OM follow-up absent)**

| | |
|---|---|
| **Formula** | `(gad7_followup − gad7_T) ≥ +4` |
| **When used** | Only when there is **no** CORE-OM in the assessment window but GAD-7 follow-up exists |
| **Meaning** | Anxiety score increased meaningfully |

```
Example — L5 PASS (no CORE-OM follow-up):
  T:        GAD-7 = 8
  Follow-up: GAD-7 = 13  → delta = +5 ✓
  No CORE-OM in [T+21, T+45]
  → relapse_label = 1 (secondary path), recovery_label = 0 or null per GAD-7 rules
```

---

**Summary — L1–L5 at a glance**

| Rule | What worsened | Condition (default) | Example delta that PASSES |
|------|---------------|---------------------|---------------------------|
| **L1** | Total score | Rise ≥ 5 points | 15 → 21 (+6) |
| **L2** | Problems | Rise ≥ 0.10 norm | 0.30 → 0.45 (+0.15) |
| **L3** | Risk (absolute) | risk ≥ 0.70 at follow-up | 0.25 → 0.72 |
| **L4** | Risk (change) | Rise ≥ 0.15 norm | 0.20 → 0.38 (+0.18) |
| **L5** | GAD-7 | Rise ≥ 4 points *(no CORE-OM F/U)* | 8 → 13 (+5) |

**Only one rule needs to pass** — relapse uses **OR** logic across L1–L5.

##### How to get L1–L5 — step by step

L1–L5 are **not** L2 feature columns and **not** ML model inputs. They are **offline label rules** computed by comparing two assessments: **baseline at snapshot T** and **follow-up in [T+21, T+45]**.

```
Step 1: Fix snapshot date T (training row date)
Step 2: Load baseline CORE-OM on or before T
Step 3: Load follow-up CORE-OM nearest to T+30 within [T+21, T+45]
Step 4: For each rule L1–L4, compare baseline vs follow-up fields (see table below)
Step 5: L5 only if Step 3 found NO CORE-OM follow-up — then use GAD-7 baseline + follow-up instead
Step 6: IF any L1–L5 is true → relapse_label = 1, else relapse_label = 0
        IF no follow-up at all (and no L5 path) → relapse_label = null
```

##### L1–L5 → data fields mapping

| Rule | Instrument | Field at **T** (baseline) | Field at **follow-up** | Score type | L0 event path | Related L2 column *(for ML features only)* |
|------|------------|---------------------------|------------------------|------------|---------------|---------------------------------------------|
| **L1** | CORE-OM | `payload.total_score` | `payload.total_score` | **Raw points** | `assessment_completed` | `core_om_score` / total normalized |
| **L2** | CORE-OM | `payload.subscales.problems.normalized` | `payload.subscales.problems.normalized` | **0–1 normalized** | `assessment_completed` | `core_om_problems` |
| **L3** | CORE-OM | *(not used — absolute at follow-up only)* | `payload.subscales.risk.normalized` | **0–1 normalized** | `assessment_completed` | `core_om_risk` |
| **L4** | CORE-OM | `payload.subscales.risk.normalized` | `payload.subscales.risk.normalized` | **0–1 normalized** (delta) | `assessment_completed` | `core_om_risk` |
| **L5** | GAD-7 | `payload.total_score` | `payload.total_score` | **Raw points (0–21)** | `assessment_completed` | `gad7_normalized_latest` *(normalized; label rule uses raw)* |

**Important distinctions:**

| Question | Answer |
|----------|--------|
| Are L1–L5 the same as L2 features? | **No.** L2 columns are **latest value on snapshot day** for model training features. L1–L5 compare **T vs follow-up** for label generation only. |
| Does `core_om_delta_30d` compute L1? | **No.** `core_om_delta_30d` is an L2 feature (total normalized change over 30 days). L1 uses **raw total_score** from two assessment events with MCID = 5. |
| Which subscales are NOT used in L1–L5? | **Wellbeing** and **functioning** — they appear in recovery rules R3/R4 only, not relapse. |
| When does L5 run? | Only when there is **no** CORE-OM follow-up in [T+21, T+45] but GAD-7 follow-up exists. |

**Worked example — computing all L rules for one user:**

```
Snapshot T = 2024-10-01

Baseline CORE-OM (2024-10-01):
  total_score = 18
  subscales.problems.normalized = 0.30
  subscales.risk.normalized = 0.25

Follow-up CORE-OM (2024-10-31):
  total_score = 19
  subscales.problems.normalized = 0.45
  subscales.risk.normalized = 0.72

L1: 19 − 18 = +1        → FAIL (need ≥ +5)
L2: 0.45 − 0.30 = +0.15 → PASS (≥ +0.10)
L3: risk = 0.72         → PASS (≥ 0.70)
L4: 0.72 − 0.25 = +0.47 → PASS (≥ +0.15)

→ relapse_label = 1 (L2, L3, and L4 all pass — only one needed)
→ recovery_label = 0 (relapse checked first)
```

**Where this runs in the pipeline:**

| Stage | What happens |
|-------|----------------|
| **L0** | User completes CORE-OM / GAD-7 → `assessment_completed` event stored in `raw` |
| **Label job** (offline) | Pairs assessments at T and follow-up → evaluates L1–L5 → writes `relapse_label` to `ml.training_labels` |
| **L2** | Copies **latest** assessment values into feature row (separate purpose) |
| **L4 ML** | Trains relapse model using L2 features; **target** = `relapse_label` from label job |

See also: [§4.3.6](#436-relapse-label-relapse_label), [Appendix B.1 Decision tree B](#decision-tree-a--clinical-labels-recovery_label-relapse_label).

All three conditions below must be true for `recovery_label = 1`:

| # | Condition | Meaning |
|---|-----------|---------|
| 1 | **Improvement detected (R1–R4)** | At least **one** recovery rule shows meaningful clinical improvement between T and follow-up |
| 2 | **Risk guard passes** | `risk_norm` at follow-up is **below 0.70** |
| 3 | **Not a relapse** | **None** of L1–L5 fired — relapse was checked first |

```
IF no follow-up in [T+21, T+45]:
    recovery_label = null          ← unknown / censored

ELSE IF any relapse rule L1–L5 is true:
    recovery_label = 0               ← relapse takes precedence (relapse_label = 1)

ELSE IF (any of R1–R4 is true) AND (risk at follow-up < 0.70):
    recovery_label = 1               ← meaningful improvement

ELSE:
    recovery_label = 0               ← stable, no meaningful change
```

#### 2.2.6 Label values — what 1, 0, and null mean

| Value | Meaning | When it happens |
|-------|---------|-----------------|
| **`1`** | Positive outcome for that label | Recovery: meaningful improvement + guards pass. Relapse: any L1–L5 fired. |
| **`0`** | Negative outcome **or** stable | Recovery: follow-up exists but no R1–R4 (stable), OR relapse blocked recovery. Relapse: follow-up exists but no L1–L5. |
| **`null`** | **Unknown / censored** | No valid CORE-OM (or GAD-7 secondary path) in assessment window. **Exclude** from clinical model training — do not treat as 0. |

**Example — label rows in training data:**

| user_id | snapshot_date | core_om_total | recovery_label | relapse_label | Rule triggered | Notes |
|---------|---------------|---------------|----------------|---------------|----------------|-------|
| 1001 | 2024-10-01 | 22 | 1 | 0 | **R1** (22→16, −6) | Total + problems improved; risk 0.15 |
| 1002 | 2024-10-01 | 18 | 0 | 0 | — | Stable: follow-up exists, no R1–R4, no L1–L5 |
| 1003 | 2024-10-01 | 25 | null | null | — | Censored: no follow-up in [T+21, T+45] |
| 1004 | 2024-10-01 | 18 | 0 | 1 | **L3** (risk 0.72) | Total +1 only; risk elevation → relapse wins |
| 1005 | 2024-10-01 | 20 | 1 | 0 | **R2** (problems −0.17) | Total flat; problems subscale drove recovery |

*Full rule definitions: [§2.2.3 R1–R4](#223-recovery-rules-r1r4--detailed-with-examples), [§2.2.4 L1–L5](#224-relapse-rules-l1l5--detailed-with-examples). Authoritative spec: [§4.3](#43-clinical-outcome-labels--production-specification).*

### 2.3 Determinism rule

Same inputs + same `score_version` + same model versions → **identical outputs**.

- Batch pipeline and API must use the same scoring code path.
- LLM/chat layer **must read** precomputed scores — never invent numbers.

### 2.4 Unified architecture — three score types coexist

| Score type | Formula family | Purpose | When primary |
|------------|---------------|---------|--------------|
| **CRS v2 (ML)** | 0.4×P(recovery) + 0.2×(1−P(dropout)) + … | Predict future trajectory | `days_active > 30`, models mature |
| **CRS readiness (Part1)** | 5-category weighted inputs (§6.6) | Same-day mental readiness | Cold start, explainability fallback |
| **Pillar scores (Part1)** | Per-pillar category weights (§7.6) | "Where am I right now?" state | Always on dashboard |
| **Trend metrics** | 7 trajectory composites (§8) | Direction of change | Always alongside state |

**Do not merge** Part1 category weights into CRS v2 probability formula — they answer different questions (today vs future).

---

## 3. The three-layer model: state, trajectory, narrative

### 3.0 Layer overview

| Layer | Engine Part1 question | Output |
|-------|----------------------|--------|
| **State** | Where am I right now? | 4 pillars (0–100 each) |
| **Trajectory** | Where am I heading? | CRS v2 + 7 trends |
| **Narrative** | Why / Aware / Risk / Next? | API text blocks §10.4 |

### 3.1 State layer — "Where am I right now?"

Four pillar scores (0–100 each) — meanings from **Engine Part1.docx**:

| Pillar | Meaning (product) | Primary question |
|--------|-------------------|------------------|
| **Clarity** | Mental sharpness, focus, attention, recall, cognitive organisation | Can the user think clearly and organise daily life? |
| **Emotional Balance** | Emotional steadiness, distress load, mood volatility, regulation | Are emotions stable and within a healthy range? |
| **Resilience** | Recovery capacity, adaptability, coping strength, bounce-back from stress | Can the user recover from setbacks? |
| **Capacity** | Available functional bandwidth — work, relationships, routine, daily demands | Does the user have energy and engagement to act? |

**CRS (Cognitive Readiness Score)** — overall mental readiness: how prepared the user is to think, regulate, perform, and sustain daily demands. Combines biological, behavioural, and assessment signals (§6).

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

### 3.4 Narrative layer — "Why / Aware / Risk / Next?" (Engine Part1)

The narrative layer translates scores into actionable copy. Generated by L1 pattern engine using L3 snapshot inputs.

| Narrative block | Inputs | Example output |
|-----------------|--------|----------------|
| `why_summary` | Top 3 SHAP drivers mapped to category (Assessment / Lifestyle / Tools / Forms / Therapist) | "Your score is influenced by improved sleep and lower anxiety on your last assessment." |
| `awareness_flags` | Trends with `direction_7d = declining` or volatility flags | "Motivation has declined 18% over 7 days." |
| `risk_summary` | `relapse_probability`, `core_om_risk`, risk cap status | "Risk indicators are elevated — consider reaching out to your therapist." |
| `next_actions` | L1 pattern matches | ["Complete today's check-in", "Review sleep consistency tips"] |

Spec: §10.4 API fields. Must respect risk cap — suppress positive readiness copy when `risk_elevated = true`.

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

### 4.3 Clinical outcome labels — production specification

CORE-OM is the **primary clinical anchor** for recovery and relapse labels but is **not sufficient alone**. This section defines production-grade labels aligned with ENGINE-POC G7 (CORE-OM subscales) and D3 (GAD-7 in v1). For a one-page clinical review summary, see [Appendix B.1](#appendix-b1--clinical-label-decision-tree-for-sign-off).

#### 4.3.1 Design principles

| Principle | Requirement |
|-----------|-------------|
| **Clinical ground truth** | Labels derived from assessments and program events, not CRS itself |
| **Subscale-aware** | Use `core_om_wellbeing`, `core_om_problems`, `core_om_functioning`, `core_om_risk` — not total score only |
| **Sparse-safe** | No follow-up assessment → `label = null` (censored), never default to 0 |
| **Mutually exclusive** | Relapse evaluated before recovery; at most one positive clinical label per snapshot |
| **Point-in-time** | Label at T uses only assessments with `occurred_at ≤ T + horizon` |
| **Auditable** | Store `label_version`, thresholds, and assessment IDs used |

#### 4.3.2 Why CORE-OM alone is insufficient

| Gap | Risk if ignored | Mitigation in this spec |
|-----|-----------------|-------------------------|
| Infrequent reassessment | Most users lack T+30 CORE-OM → biased training | Assessment window + censoring |
| Total score masks mixed change | Problems improve, functioning worsens → false neutral | Subscale rules |
| Anxiety-specific recovery | GAD-7 improves, CORE-OM unchanged | GAD-7 confirmer for recovery |
| Relapse ≠ only score increase | Risk subscale may elevate first | `core_om_risk` in relapse rule |
| Behavioral recovery lag | Mood/sleep improve before next CORE-OM | Secondary confirmer (optional v1.1) |

#### 4.3.3 Configuration constants (clinical sign-off required)

| Constant | Default | Owner | Description |
|----------|---------|-------|-------------|
| `CORE_OM_MCID_TOTAL` | 5 | Clinical | Min meaningful change on total score (raw points) |
| `CORE_OM_MCID_SUBSCALE_NORM` | 0.10 | Clinical | Min change on normalized subscale (0–1) |
| `GAD7_MCID` | 4 | Clinical | Min change on GAD-7 raw score |
| `CORE_OM_RISK_RELAPSE_THRESHOLD` | 0.70 | Clinical | Normalized risk ≥ this → relapse signal |
| `ASSESSMENT_HORIZON_DAYS` | 30 | Product | Target follow-up period |
| `ASSESSMENT_WINDOW_MIN_DAYS` | 21 | Product | Earliest valid follow-up |
| `ASSESSMENT_WINDOW_MAX_DAYS` | 45 | Product | Latest valid follow-up |
| `DROPOUT_HORIZON_DAYS` | 60 | Product | Dropout observation window |
| `DROPOUT_INACTIVE_DAYS` | 30 | Product | No app activity threshold |
| `ENGAGEMENT_LOSS_RELATIVE_DROP` | 0.50 | Product | 50% drop vs 30d baseline |
| `LABEL_VERSION` | `label_v2.0.0` | Engineering | Bump on rule change |

**Note:** Lower CORE-OM total = lower distress = improvement.

#### 4.3.4 Assessment pairing logic

Follow-up assessment must fall in **[T + 21d, T + 45d]** (configurable window around 30d horizon).

**Pseudocode — assessment pairing:**

```
FUNCTION get_followup_assessment(user_id, snapshot_date, instrument, window):
  candidates = assessments(user_id, instrument)
    WHERE occurred_at BETWEEN snapshot_date + window.min
                          AND snapshot_date + window.max
  RETURN candidate with MIN(abs(occurred_at - (snapshot_date + 30 days)))
         OR NULL if no candidates  → censored
```

**Censoring examples:**

| Case | recovery_label | relapse_label | Training action |
|------|----------------|---------------|-----------------|
| CORE-OM at T and T+30 in window | 0 or 1 | 0 or 1 | Include row |
| CORE-OM at T only, no follow-up | `null` | `null` | **Exclude** from clinical model training |
| User dropped out before window | `null` | `null` | Exclude; use dropout_label separately |
| Only GAD-7 follow-up, no CORE-OM | GAD-7 confirmer path (§4.3.6) | Partial | Flag `label_confidence=secondary` |

#### 4.3.5 Recovery label (`recovery_label`)

> **Primer:** For glossary (MCID, subscale, censoring) and worked examples of each rule, see [§2.2.1–§2.2.4](#221-glossary--terms-used-in-label-rules).

**Primary criteria (any ONE required + safety guard):**

| # | Criterion | Formula |
|---|-----------|---------|
| R1 | Total CORE-OM improvement | `(total_T+30 - total_T) ≤ -CORE_OM_MCID_TOTAL` |
| R2 | Problems subscale improvement | `(problems_T+30 - problems_T) ≤ -CORE_OM_MCID_SUBSCALE_NORM` |
| R3 | Wellbeing subscale improvement | `(wellbeing_T+30 - wellbeing_T) ≥ +CORE_OM_MCID_SUBSCALE_NORM` |
| R4 | Functioning subscale improvement | `(functioning_T+30 - functioning_T) ≥ +CORE_OM_MCID_SUBSCALE_NORM` |

**Safety guard (all recovery paths):**

```
core_om_risk_T+30 < CORE_OM_RISK_RELAPSE_THRESHOLD
AND NOT relapse_criteria_met (§4.3.6)
```

**GAD-7 confirmer (when CORE-OM follow-up missing but GAD-7 exists in window):**

```
recovery_label = 1 IF (gad7_T+30 - gad7_T) <= -GAD7_MCID
                 AND mood_slope_7d at T+30 > 0
                 AND label_confidence = "secondary"
```

**Worked example — recovery via problems subscale:**

```
Snapshot T (Jan 1):
  core_om_total=22, problems_norm=0.55, wellbeing_norm=0.45, functioning_norm=0.50, risk_norm=0.20
Snapshot T+30 (Jan 31):
  core_om_total=17, problems_norm=0.38, wellbeing_norm=0.52, functioning_norm=0.55, risk_norm=0.15

Delta total = -5  → meets R1 (MCID=5)
Risk at T+30 = 0.15 < 0.70  → guard pass
→ recovery_label = 1
```

**Worked example — censored:**

```
CORE-OM at T = 20
No CORE-OM or GAD-7 in [T+21, T+45]
→ recovery_label = null, relapse_label = null (exclude from training)
```

#### 4.3.6 Relapse label (`relapse_label`)

> **Primer:** For detailed L1–L5 examples, see [§2.2.4](#224-relapse-rules-l1l5--detailed-with-examples).

**Evaluated before recovery.** If any criterion true → `relapse_label=1`, `recovery_label=0`.

| # | Criterion | Formula |
|---|-----------|---------|
| L1 | Total CORE-OM worsening | `(total_T+30 - total_T) ≥ +CORE_OM_MCID_TOTAL` |
| L2 | Problems subscale worsening | `(problems_T+30 - problems_T) ≥ +CORE_OM_MCID_SUBSCALE_NORM` |
| L3 | Risk elevation | `core_om_risk_T+30 ≥ CORE_OM_RISK_RELAPSE_THRESHOLD` |
| L4 | Risk increase | `(risk_T+30 - risk_T) ≥ +0.15` |
| L5 | GAD-7 worsening (confirmer) | `(gad7_T+30 - gad7_T) ≥ +GAD7_MCID` when CORE-OM absent |

**Worked example — relapse via risk elevation:**

```
T:   total=18, risk_norm=0.25
T+30: total=19, risk_norm=0.72

Total delta = +1 (below MCID) but risk_T+30 ≥ 0.70
→ relapse_label = 1, recovery_label = 0
```

**Worked example — mixed trajectory (subscale importance):**

```
T → T+30:
  problems: 0.60 → 0.42  (improved)
  functioning: 0.55 → 0.40  (worsened)
  total: unchanged

→ relapse=0, recovery=0 (stable), NOT censored
```

#### 4.3.7 Dropout label (`dropout_label`)

**Independent of clinical labels.** Program/business outcome — answers: *“Did this user leave the program within 60 days after snapshot T?”*

```
dropout_label = 1 IF ANY of:
  - user_churned event within [T, T + DROPOUT_HORIZON_DAYS]
  - no app_session AND no therapy_attended for DROPOUT_INACTIVE_DAYS consecutive days
  - therapy program status = 'terminated'
ELSE 0
```

##### What `user_churned event within [T, T + DROPOUT_HORIZON_DAYS]` means

| Term | Meaning |
|------|---------|
| **`user_churned`** | An **L0 ingested event** (`event_type = "user_churned"`) emitted when the user **officially leaves** the MindPeers program — e.g. cancels subscription, closes account, or is marked churned in CRM. Source: `auth_crm`. See [Data Ingestion §12.2](./Data-Ingestion-Layer-Production-Spec.md#122-example--dropout-label). |
| **Event** | One row in `raw.events` with `user_id`, `occurred_at` (when churn happened), and payload fields such as `churn_reason`, `last_session_date`. |
| **T** | Snapshot date — the training row date we are labeling. |
| **`DROPOUT_HORIZON_DAYS`** | Observation window after T. Default = **60 days**. |
| **`[T, T + 60 days]`** | Inclusive date range: churn must happen **on or after T** and **on or before T+60**. |

**In plain language:** For a training row dated **1 Jan**, if the system records a **`user_churned` event anytime from 1 Jan through 2 Mar** (60 days later), that row gets **`dropout_label = 1`**.

**Example — churn inside window → dropout = 1:**

```
Snapshot T           = 2025-01-01
DROPOUT_HORIZON_DAYS = 60
Window               = 2025-01-01 to 2025-03-02 (inclusive)

user_churned event:
  occurred_at = 2025-02-01
  payload.churn_reason = "voluntary_exit"
  payload.last_session_date = "2025-01-28"

Feb 1 is inside [Jan 1, Mar 2]  →  dropout_label = 1
```

**Example — churn after window → dropout = 0 (for this rule):**

```
Snapshot T = 2025-01-01
user_churned occurred_at = 2025-04-15   (105 days after T)

Apr 15 is AFTER T+60  →  this rule does NOT fire
                         (check other dropout rules: inactivity, terminated)
```

**Example — no churn event but user went inactive:**

```
No user_churned event
But no app_session AND no therapy_attended for 30 consecutive days
→ dropout_label = 1 via the inactivity rule (second bullet)
```

**What `user_churned` is NOT:**

| Not this | Why |
|----------|-----|
| Low engagement for a few days | Needs 30 consecutive inactive days OR explicit churn event |
| Missing mood check-ins only | Inactivity rule requires **both** no app sessions **and** no therapy attendance |
| `recovery_label` or `relapse_label` | Dropout is a **program retention** outcome, not a clinical assessment outcome |
| An L2 feature column | It is a **source event**; the label job reads it offline to set `dropout_label` |

**Typical `user_churned` payload (from ingestion):**

```json
{
  "event_type": "user_churned",
  "user_id": "1003",
  "occurred_at": "2025-02-01T00:00:00+00:00",
  "payload": {
    "churn_reason": "voluntary_exit",
    "last_session_date": "2025-01-28"
  }
}
```

Common `churn_reason` values (product-defined): `voluntary_exit`, `payment_failed`, `admin_removed`, `program_completed_early`.

#### 4.3.8 Engagement loss label (`engagement_loss_label`)

```
baseline = engagement_rate_7d at T
future   = engagement_rate_7d at T + 14d

engagement_loss_label = 1 IF future <= baseline * (1 - ENGAGEMENT_LOSS_RELATIVE_DROP)
ELSE 0
```

#### 4.3.9 Label precedence and storage

**Evaluation order at snapshot T:**

```
1. If no valid clinical follow-up in window → recovery=null, relapse=null
2. Else if relapse_criteria → relapse=1, recovery=0
3. Else if recovery_criteria → recovery=1, relapse=0
4. Else → recovery=0, relapse=0
5. Compute dropout_label and engagement_loss_label independently
```

**Training table:** `ml.training_labels` — columns: `user_id`, `snapshot_date`, `recovery_label`, `relapse_label`, `dropout_label`, `engagement_loss_label`, `label_version`, `label_confidence`, `label_censored_reason`.

**Inference:** Labels are **never** on production feature rows — only model probabilities.

#### 4.3.10 Label generation service specification

Labels are produced **offline** by a batch job (`ml.label_generation_daily`) — not at inference time. This section is the canonical specification; engineering implements against these contracts.

**Job inputs**

| Input | Source | Required |
|-------|--------|----------|
| Snapshot rows | `ml.snapshots` at `(user_id, snapshot_date)` | Yes |
| CORE-OM assessments | `raw.assessment_completed` (instrument = CORE-OM) | For primary path |
| GAD-7 assessments | `raw.assessment_completed` (instrument = GAD-7) | For confirmer path |
| Engagement series | L2 `engagement_rate_7d` | For engagement_loss_label |
| Program events | churn, therapy termination, inactivity rollup | For dropout_label |
| Config | `LabelConfig` (§4.3.3 constants) | Yes |

**Job output — table `ml.training_labels`**

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | User identifier |
| `snapshot_date` | date | Label anchor date T |
| `recovery_label` | int \| null | 0, 1, or null (censored) |
| `relapse_label` | int \| null | 0, 1, or null (censored) |
| `dropout_label` | int | 0 or 1 |
| `engagement_loss_label` | int | 0 or 1 |
| `label_version` | string | e.g. `label_v2.0.0` |
| `label_confidence` | enum | `primary` \| `secondary` \| null |
| `label_censored_reason` | enum \| null | `no_followup_in_window`, `dropout_before_window` |
| `recovery_criteria_met` | string[] | R1–R4 IDs when applicable |
| `relapse_criteria_met` | string[] | L1–L5 IDs when applicable |
| `baseline_assessment_id` | string \| null | CORE-OM at T |
| `followup_assessment_id` | string \| null | CORE-OM in window |
| `computed_at` | timestamp | Audit |

**Pseudocode — clinical labels (recovery + relapse):**

```
FUNCTION compute_clinical_labels(user_id, snapshot_date, config):
  baseline = nearest CORE-OM on or before snapshot_date
  IF user_churned before assessment window:
    RETURN recovery=null, relapse=null, censored=dropout_before_window

  followup = get_followup_assessment(user_id, snapshot_date, CORE-OM, config.window)

  IF followup IS NULL:
    IF gad7_confirmer_path_satisfied(user_id, snapshot_date, config):
      RETURN recovery=1, relapse=0, confidence=secondary
    RETURN recovery=null, relapse=null, censored=no_followup_in_window

  relapse_met = evaluate L1–L5(baseline, followup, config)
  IF relapse_met NOT EMPTY:
    RETURN relapse=1, recovery=0, confidence=primary

  recovery_met = evaluate R1–R4(baseline, followup, config)
  IF recovery_met NOT EMPTY AND followup.risk < config.risk_threshold:
    RETURN recovery=1, relapse=0, confidence=primary

  RETURN recovery=0, relapse=0, confidence=primary
```

**Pseudocode — dropout and engagement (independent):**

```
dropout_label = 1 IF churn OR therapy_terminated OR inactive >= DROPOUT_INACTIVE_DAYS
                ELSE 0

engagement_loss_label = 1 IF engagement_rate_7d(T+14) <= engagement_rate_7d(T) × 0.50
                        ELSE 0
```

**Operational requirements**

| Requirement | Rule |
|-------------|------|
| Determinism | Same inputs + `label_version` → identical labels |
| Idempotency | Upsert on `(user_id, snapshot_date, label_version)` |
| Schedule | Daily after L2 feature job (02:15 UTC); only snapshots with `snapshot_date ≤ today − 45d` for clinical labels |
| Exclusion | Rows with `recovery_label IS NULL` excluded from recovery/relapse model training |
| Lineage | Store assessment IDs used; retain for model audit |
| Version bump | Any threshold or rule change → new `label_version`; re-backfill optional |

**Acceptance criteria**

- [ ] Worked examples in §4.3.5–§4.3.6 produce expected labels when run through job  
- [ ] Censoring rate reported monthly; alert if > 40%  
- [ ] Relapse always evaluated before recovery  
- [ ] No label columns exposed on production inference API  

#### 4.3.11 ML training rules

| Label | Expected positive rate | Handling |
|-------|------------------------|----------|
| recovery_label | 25–40% (non-censored) | Class weights |
| relapse_label | 8–15% (non-censored) | Monitor AUC-PR |
| dropout_label | 15–20% | Standard |
| engagement_loss_label | 20–25% | Standard |

**Censoring target:** < 40% for clinical models at 30d+ maturity. Report monthly.

#### 4.3.12 Clinical governance checklist

- [ ] MCID thresholds signed by clinical lead  
- [ ] Risk threshold aligned with escalation policy  
- [ ] Censoring rate monitored; reassessment cadence defined  
- [ ] Labels not presented as diagnosis to end users  
- [ ] `label_version` in model registry matches training data  
- [ ] Clinical lead has reviewed [Appendix B.1 — Clinical label decision tree](#appendix-b1--clinical-label-decision-tree-for-sign-off)

---

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
Target: recovery_label per §4.3 (subscale-aware, not total-only)
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

**Interpretation:** 82% predicted probability of clinically meaningful improvement per §4.3 rules.

### 5.4 Model 2 — Relapse probability

**Training:**

```
Target: relapse_label per §4.3 (subscale, risk, GAD-7 confirmers)
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

## 6. CRS calculation — dual model (ML v2 + rule-based readiness)

CRS v3 exposes **two complementary CRS computations**. Production headline uses v2 when available; readiness score always computed for explainability and cold start.

### 6.1 CRS v2 — ML composite (primary at maturity)

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

### 6.6 CRS readiness — rule-based same-day score (Engine Part1)

When ML models are immature or for explainability, compute **`crs_readiness_score`** from five input categories. Source: **Engine Part1.docx** Table 6.

**Category weights (CRS readiness):**

| Input category | Weight | Parameters (normalized 0–100 per parameter, equal weight within block) |
|----------------|--------|------------------------------------------------------------------------|
| **Assessment** | 30% | CORE-OM overall, functioning, problems, wellbeing, risk, anxiety, depression, trauma |
| **Lifestyle + Biomarker** | 30% | Sleep, fatigue, HRV, pulse, cortisol, blood sugar, thyroid/TSH, hydration, nutrition |
| **Tools / Behavioural** | 15% | Mood, motivation check-in, Memory Game, Connect Four, app engagement |
| **Forms** | 15% | Therapy intent, primary concern, work-stress pattern, routine disruption, check-in completion |
| **Therapist / Session** | 10% | Session attendance, therapist inputs (see therapist sheet) |

**Formula:**

```
block_score = mean(normalized parameters in block that are non-null)
crs_readiness = 0.30×Assessment + 0.30×Lifestyle + 0.15×Tools + 0.15×Forms + 0.10×Therapist
                (renormalize weights if a block has no data)
```

**v3 display selection:**

| Condition | `cognitive_readiness_score` (headline) | Also expose |
|-----------|----------------------------------------|-------------|
| `data_maturity_stage = full` AND models loaded | CRS v2 (§6.1) | `crs_readiness_score`, `crs_v2_score` |
| Cold start / early | `crs_readiness_score` | `crs_v2_score = null` |
| Shadow period | Both | `crs_primary` field indicates which is headline |

Apply **risk cap (§7.7)** to both scores before API output.

---

## 7. Pillar scores (state layer) — Engine Part1 model

Pillar scores represent **current state** ("Where am I right now?"). Engine Part1 defines **five input categories** per pillar with explicit weights. v3 uses Part1 category model as **canonical rule-based approach**; ML pillar models are optional enhancements (§7.1).

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

### 7.6 Five-category weight model per pillar (Engine Part1)

Each pillar score = weighted sum of **five blocks**. Within each block, parameters are normalized 0–100 and averaged (missing parameters excluded; block weight renormalized).

**Clarity (Engine Part1 Table 7):**

| Category | Weight | Key parameters |
|----------|--------|----------------|
| Tools / Behavioural | 30% | Memory Game, Connect Four, focus behaviour, completion patterns |
| Lifestyle + Biomarker | 25% | Sleep, fatigue, hydration, nutrition, HRV, pulse, blood sugar, thyroid, Vitamin D |
| Assessment | 20% | CORE-OM functioning, problems, anxiety, ADHD if available |
| Forms | 15% | Overthinking, decision fatigue, brain fog, work pressure |
| Therapist / Session | 10% | Therapist sheet inputs |

**Emotional Balance (Table 8):** Assessment 35%, Forms 20%, Tools 20%, Lifestyle 20%, Therapist 5%

**Resilience (Table 9):** Lifestyle 30%, Assessment 25%, Forms 20%, Tools 15%, Therapist 10%

**Capacity (Table 10):** Assessment 30%, Lifestyle 30%, Forms 20%, Therapist 10%, Tools 10%

**Pillar formula (generic):**

```
PillarScore = Σ (category_weight × block_mean_score)
            → apply risk cap §7.7
            → round to integer 0–100
```

Full parameter lists: [Appendix F — Engine Part1 input registry](#appendix-f--engine-part1-input-registry).

### 7.7 CORE-OM risk cap and override rules (Engine Part1)

Engine Part1: *"CORE-OM Risk Score should act as a cap/override if elevated."* Applied to **all user-facing scores** before API response.

| Condition | Action |
|-----------|--------|
| `core_om_risk >= 0.70` | Set `risk_elevated = true`; cap CRS and all pillars at **max 40** (configurable `RISK_CAP_CEILING`) |
| `core_om_risk >= 0.70` | Force `risk_band = "Elevated"`; trigger L1 Risk Watch pattern |
| `core_om_risk >= 0.70` | Suppress positive readiness copy in narrative §10.4 |
| `core_om_risk` increased ≥ 0.15 in 30d | Add `awareness_flags`: "Risk indicators have increased" |
| Relapse label L3/L4 would fire | Same cap behaviour at inference time when risk subscale high |

**Pseudocode:**

```
FUNCTION apply_risk_cap(scores, core_om_risk, ceiling=40):
  IF core_om_risk >= 0.70:
    scores.crs = MIN(scores.crs, ceiling)
    scores.clarity = MIN(scores.clarity, ceiling)
    scores.emotional_balance = MIN(scores.emotional_balance, ceiling)
    scores.resilience = MIN(scores.resilience, ceiling)
    scores.capacity = MIN(scores.capacity, ceiling)
    scores.risk_elevated = true
  RETURN scores
```

Clinical sign-off required for `RISK_CAP_CEILING` and escalation workflow.

### 7.8 Input availability matrix (v1 / v1.1 / future)

| Parameter group | v1 (L2 today) | v1.1 (ingestion backlog) | Future |
|-----------------|---------------|--------------------------|--------|
| CORE-OM subscales + GAD-7 | Yes | — | PHQ-9, trauma scores |
| Sleep, HRV, mood, engagement | Yes | fatigue, pulse | — |
| Games (Memory, Connect Four) | — | Yes | Whack A Mole |
| Journaling NLP | — | Partial | Full tone/themes |
| Forms / intake | — | Yes | — |
| Biomarkers (cortisol, TSH, etc.) | — | Yes | — |
| Therapist sheet params | Partial (attendance) | Full sheet sync | — |

When v1.1 parameters are missing, block weights renormalize over available parameters — same as L2 cold-start policy §13.

**Mandatory policy:** All Engine Part1 attributes (70 canonical — see [Engine Part1 Full Attribute Binding Spec](./final/Engine-Part1-Full-Attribute-Binding-Spec.md)) **must** be wired to state and trajectory layers. Partial implementation is allowed by phase; spec coverage is **100%**.

### 7.9 State layer — complete Part1 attribute binding

Every attribute in Engine Part1 maps to **at least one** of: CRS readiness, Clarity, Emotional Balance, Resilience, Capacity. Binding uses five category blocks per score (§7.6) with **all** parameters in each block — not a subset.

| Score | Part1 table | Category weights | Attribute count |
|-------|-------------|------------------|-----------------|
| CRS readiness | Table 1 + 6 | 30/30/15/15/10 | 25+ |
| Clarity | Table 2 + 7 | 30/25/20/15/10 | 20+ |
| Emotional Balance | Table 3 + 8 | 35/20/20/20/5 | 22+ |
| Resilience | Table 4 + 9 | 30/25/20/15/10 | 20+ |
| Capacity | Table 5 + 10 | 30/30/20/10/10 | 22+ |

**Full matrix:** [final/Engine-Part1-Full-Attribute-Binding-Spec.md §3](./final/Engine-Part1-Full-Attribute-Binding-Spec.md)

```
StateScore = Σ category_weight × mean(normalized Part1 attributes in category)
         → apply_risk_cap(core_om_risk)
```

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

### 8.9 Trajectory layer — complete Part1 attribute binding

Trend metrics **must** use all trajectory-relevant Part1 attributes — not only the minimal v1 subset in §8.2–§8.8. When `feature_version >= feature_v2.0.0` (all Part1 waves complete), trend formulas **expand** as below.

| Trend | Part1 attributes (canonical IDs) | Contribution type |
|-------|----------------------------------|-------------------|
| **Recovery Readiness** | A11 Sleep, A13 HRV, A12 Fatigue⁻, A15 Exercise, A19 Sun, A21 Cortisol⁻, A24 Vit D, A06 CORE-OM delta | Level + slope |
| **Stress Load** | A07–A09 Anxiety/Depression/Trauma, A13–A14 HRV/Pulse, A21–A23 Cortisol/Glucose/TSH, A27 mood volatility | Level + inverted slopes |
| **Sleep Consistency** | A11 Sleep variance, A12 Fatigue correlation | Volatility |
| **Energy Rhythm** | A12 Fatigue, A15–A18 Lifestyle, A23 Glucose, A28 Motivation slope, A37 Engagement slope | Level + slope |
| **Emotional Stability** | A27–A29 check-ins, A33–A36 journals, A07–A09 assessments, A54 triggers | Volatility + slope |
| **Motivation Momentum** | A28 Motivation, A37–A39 engagement/guides, A42 check-in drop-off, A61 burnout forms | Slope |
| **Cognitive Momentum** | A30–A31 games, A02 functioning, A12 Fatigue⁻, A50–A52 brain fog forms, A10 ADHD | Slope + level |

**Full trajectory matrix:** [final/Engine-Part1-Full-Attribute-Binding-Spec.md §4](./final/Engine-Part1-Full-Attribute-Binding-Spec.md)

**Upgrade rule:**

| `feature_version` | Trend formula |
|-------------------|---------------|
| `feature_v1.0.0` | Minimal features (§8.2–§8.8) — Phase 1 |
| `feature_v2.0.0` | **Full Part1 attribute bindings** — after Phase 5 waves W1–W7 |

---

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
  "score_version": "crs_v3.0.0",
  "model_bundle_version": "outcome_models_v1.2.0",
  "confidence_tier": "High",
  "data_maturity_stage": "full",
  "crs_primary": "v2",

  "cognitive_readiness_score": 81.2,
  "crs_v2_score": 81.2,
  "crs_readiness_score": 74.5,
  "crs_band": "High",
  "risk_elevated": false,

  "pillars": {
    "clarity_score": 73,
    "clarity_meaning": "Mental sharpness, focus, and cognitive organisation",
    "emotional_balance_score": 69,
    "emotional_balance_meaning": "Emotional steadiness and regulation",
    "resilience_score": 68,
    "resilience_meaning": "Recovery capacity and adaptability",
    "capacity_score": 59,
    "capacity_meaning": "Functional bandwidth for daily demands"
  },

  "pillar_category_breakdown": {
    "clarity": { "tools_pct": 32, "lifestyle_pct": 28, "assessment_pct": 22, "forms_pct": 12, "therapist_pct": 6 },
    "emotional_balance": { "assessment_pct": 38, "forms_pct": 18, "tools_pct": 20, "lifestyle_pct": 19, "therapist_pct": 5 }
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

### 10.4 Narrative fields — five report questions (Engine Part1)

Maps §1.5 product questions to API fields. Generated by L1 pattern + L3 driver service. **Never invent scores** — narrative references precomputed snapshot only.

```json
{
  "narrative": {
    "where_now": "Your readiness is High (81). Emotional Balance and Resilience are moderate; Capacity is your lowest pillar today.",
    "why_summary": "This is influenced by strong recovery probability (82%), consistent sleep, and improved CORE-OM problems score.",
    "awareness_flags": [
      { "severity": "warning", "text": "Motivation Momentum declined 15 points in 7 days." },
      { "severity": "info", "text": "Capacity is below your 30-day average." }
    ],
    "risk": {
      "risk_elevated": false,
      "core_om_risk": 0.15,
      "relapse_probability": 0.15,
      "summary": "Clinical risk indicators are within normal range.",
      "escalation_recommended": false
    },
    "next_actions": [
      { "action_id": "complete_checkin", "label": "Complete today's check-in", "priority": 1 },
      { "action_id": "review_sleep", "label": "Review sleep consistency tips", "priority": 2 }
    ]
  },
  "score_meanings": {
    "cognitive_readiness_score": "Overall mental readiness — prepared to think, regulate, perform, and sustain daily demands",
    "clarity_score": "Mental sharpness, focus, attention, recall, cognitive organisation",
    "emotional_balance_score": "Emotional steadiness, distress load, mood volatility, regulation",
    "resilience_score": "Recovery capacity, adaptability, coping strength",
    "capacity_score": "Available functional bandwidth for work, relationships, and routine"
  }
}
```

**Risk-elevated narrative override** (`core_om_risk >= 0.70`):

```json
{
  "narrative": {
    "where_now": "Your scores are capped while risk indicators are elevated.",
    "why_summary": "CORE-OM risk subscale is elevated. Please speak with your therapist or support team.",
    "awareness_flags": [{ "severity": "critical", "text": "Risk indicators require attention." }],
    "risk": { "risk_elevated": true, "escalation_recommended": true },
    "next_actions": [{ "action_id": "contact_support", "label": "Contact your therapist", "priority": 1 }]
  }
}
```

**Driver category mapping (for `why_summary`):**

| SHAP domain | Engine Part1 category |
|-------------|----------------------|
| biological | Lifestyle + Biomarker |
| behavioral | Tools / Behavioural |
| psychological | Assessment + Forms |
| clinical | Assessment |
| therapy | Therapist / Session |

---

## 11. Normalization, bands, direction, and risk caps

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

### 11.4 Risk cap normalization (Engine Part1)

After all scores computed, apply §7.7 before band assignment:

```
1. Compute crs_v2, crs_readiness, pillars (uncapped)
2. IF core_om_risk >= RISK_THRESHOLD (0.70):
     cap all display scores at RISK_CAP_CEILING (40)
     set risk_elevated = true
     override crs_band to "Low" for display
3. Assign bands from capped scores
4. Generate narrative §10.4 with risk override if elevated
```

| Config key | Default | Owner |
|------------|---------|-------|
| `RISK_THRESHOLD` | 0.70 | Clinical |
| `RISK_CAP_CEILING` | 40 | Clinical + Product |

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

## 15. Migration and score coexistence

v3 unified spec supports **three coexisting CRS formulations** plus Part1 pillars. Migration is additive — do not deprecate pillars when promoting CRS v2.

### 15.1 Score comparison matrix

| Score | Formula | Source doc | Primary use |
|-------|---------|------------|-------------|
| **CRS v2 (ML)** | 0.4×P(recovery) + 0.2×(1−P(dropout)) + … | CRS trends doc | Headline trajectory score |
| **CRS readiness (Part1)** | 5-category weighted inputs §6.6 | Engine Part1 | Same-day readiness, cold start |
| **CRS v1 (POC)** | 0.25 × (Clarity + Balance + Resilience + Capacity) | ENGINE-POC | Legacy — replace with Part1 pillars |
| **Pillars (Part1)** | Per-pillar category weights §7.6 | Engine Part1 | State layer — always shown |

### 15.2 Comparison — CRS v2 vs CRS readiness vs pillars

| Aspect | CRS v2 (ML) | CRS readiness (Part1) | Pillars (Part1) |
|--------|-------------|----------------------|-----------------|
| Question | Where am I **heading**? | How ready am I **today**? | How am I in each **domain**? |
| Inputs | L2 features → ML models | 5 categories, 30+ parameters | 5 categories per pillar |
| Training | Yes (4 outcome labels) | No | Optional ML later |
| Cold start | Cohort prior / unavailable | Always computable | Always computable |
| Risk cap | Yes §7.7 | Yes §7.7 | Yes §7.7 |

### 15.3 Recommended migration phases (v3)

| Phase | Timeline | Action |
|-------|----------|--------|
| **Phase 1** | Weeks 1–4 | Ship Part1 pillar scores (§7.6) + CRS readiness (§6.6) + trends |
| **Phase 2** | Weeks 5–8 | Train CRS v2 outcome models; label job §4.3 |
| **Phase 3** | Weeks 9–10 | Shadow CRS v2 alongside readiness; narrative §10.4 |
| **Phase 4** | Week 11+ | `crs_primary = v2` when mature; keep readiness + pillars |
| **Phase 5** | Ongoing | Ingest v1.1 inputs (Appendix F/G); expand pillar blocks |

### 15.4 Dual/triple-score API example

```json
{
  "score_version": "crs_v3.0.0",
  "crs_primary": "v2",
  "cognitive_readiness_score": 81.2,
  "crs_v2_score": 81.2,
  "crs_readiness_score": 74.5,
  "crs_v1_legacy_score": null,
  "risk_elevated": false,
  "pillars": {
    "clarity_score": 73,
    "emotional_balance_score": 69,
    "resilience_score": 68,
    "capacity_score": 59
  }
}
```

During Phase 3, clients may show both CRS v2 and readiness with footnote explaining difference (trajectory vs today).

### 15.5 Legacy POC reference

ENGINE-POC `CRS_v1 = 0.25 × (Clarity + Balance + Resilience + Capacity)` is superseded by Part1 per-pillar category weights. Do not use equal 25% pillar blend for new implementations.

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

Implements §4.3 subscale-aware rules. Adjust schema/table names to your warehouse.

```sql
-- Pair baseline snapshot with nearest CORE-OM in [T+21, T+45]
WITH followup AS (
    SELECT
        s.user_id,
        s.snapshot_date,
        s.core_om_total       AS total_t,
        s.core_om_problems    AS problems_t,
        s.core_om_wellbeing   AS wellbeing_t,
        s.core_om_functioning AS functioning_t,
        s.core_om_risk        AS risk_t,
        f.core_om_total       AS total_f,
        f.core_om_problems    AS problems_f,
        f.core_om_wellbeing   AS wellbeing_f,
        f.core_om_functioning AS functioning_f,
        f.core_om_risk        AS risk_f,
        ROW_NUMBER() OVER (
            PARTITION BY s.user_id, s.snapshot_date
            ORDER BY ABS(f.snapshot_date - (s.snapshot_date + INTERVAL '30 days'))
        ) AS rn
    FROM ml.snapshots s
    JOIN ml.snapshots f
      ON s.user_id = f.user_id
     AND f.snapshot_date BETWEEN s.snapshot_date + INTERVAL '21 days'
                             AND s.snapshot_date + INTERVAL '45 days'
     AND f.core_om_total IS NOT NULL
    WHERE s.core_om_total IS NOT NULL
)
SELECT
    user_id,
    snapshot_date,
    CASE
        WHEN total_f IS NULL THEN NULL  -- censored
        WHEN risk_f >= 0.70
          OR (total_f - total_t) >= 5
          OR (problems_f - problems_t) >= 0.10
          OR (risk_f - risk_t) >= 0.15
        THEN 0  -- relapse=1 handled in relapse_label column
        WHEN (total_f - total_t) <= -5
          OR (problems_f - problems_t) <= -0.10
          OR (wellbeing_f - wellbeing_t) >= 0.10
          OR (functioning_f - functioning_t) >= 0.10
        THEN CASE WHEN risk_f < 0.70 THEN 1 ELSE 0 END
        ELSE 0
    END AS recovery_label,
    CASE
        WHEN total_f IS NULL THEN NULL
        WHEN risk_f >= 0.70
          OR (total_f - total_t) >= 5
          OR (problems_f - problems_t) >= 0.10
          OR (risk_f - risk_t) >= 0.15
        THEN 1
        ELSE 0
    END AS relapse_label
FROM followup
WHERE rn = 1;
```

**Note:** SQL above is reference logic for data teams; the canonical rules remain §4.3.5–§4.3.9. Any warehouse implementation must produce identical labels to the pseudocode in §4.3.10 for a given `label_version`.

### Appendix B.1 — Clinical label decision tree (for sign-off)

**Purpose:** One-page reference for clinical, product, and ML teams. Full rules in [§4.3](#43-clinical-outcome-labels--production-specification).  
**Label version:** `label_v2.0.0`  
**Anchor:** Snapshot date **T** = training row date; follow-up window = **[T+21d, T+45d]** (target T+30d).

---

#### Threshold quick reference (defaults — clinical sign-off required)

| Symbol | Value | Used in |
|--------|-------|---------|
| CORE-OM total MCID | **5 points** (raw) | R1, L1 |
| Subscale MCID | **0.10** (normalized 0–1) | R2–R4, L2 |
| GAD-7 MCID | **4 points** (raw) | Recovery confirmer, L5 |
| Risk relapse threshold | **≥ 0.70** (normalized) | L3, recovery guard |
| Risk increase | **≥ +0.15** (normalized delta) | L4 |
| Engagement loss drop | **≥ 50%** relative vs baseline | engagement_loss |
| Dropout inactivity | **30** consecutive days | dropout |
| Dropout horizon | **60** days from T | dropout |

**Direction rule:** Lower CORE-OM total = improvement. Higher `problems` norm = worse. Higher `wellbeing` / `functioning` norm = better.

---

#### Decision tree A — Clinical labels (`recovery_label`, `relapse_label`)

```
                              START: snapshot date T
                                        │
                    ┌───────────────────┴───────────────────┐
                    │ User churned before follow-up window? │
                    └───────────────────┬───────────────────┘
                          YES           │           NO
                            │           │
                            ▼           ▼
              recovery = NULL     CORE-OM follow-up in [T+21, T+45]?
              relapse  = NULL              │
              censored: dropout              ├── YES ──► Compare baseline (T) vs follow-up
              before_window                  │
                                             └── NO ───► GAD-7 confirmer path? (§4.3.5)
                                                           │
                                              ┌────────────┴────────────┐
                                              │                         │
                                           YES │                      NO │
                                              ▼                         ▼
                                    recovery=1, relapse=0      recovery=NULL, relapse=NULL
                                    confidence=secondary       censored: no_followup_in_window
                                    (needs GAD-7 Δ≤−4 AND
                                     mood_slope_7d > 0)

── When CORE-OM follow-up EXISTS ──

                              ┌─ RELAPSE CHECK (first) ─┐
                              │ Any L1–L5 true?         │
                              └───────────┬─────────────┘
                                    YES   │   NO
                                      │   │
                                      ▼   ▼
                            relapse=1     ┌─ RECOVERY CHECK ─┐
                            recovery=0    │ Any R1–R4 true   │
                                          │ AND risk < 0.70? │
                                          └────────┬─────────┘
                                               YES │ NO
                                                 │  │
                                                 ▼  ▼
                                          recovery=1   recovery=0
                                          relapse=0      relapse=0
                                                         (stable)
```

**Relapse criteria (L1–L5) — ANY one → relapse = 1**

| ID | Condition |
|----|-----------|
| L1 | Total CORE-OM increased by ≥ 5 |
| L2 | Problems subscale increased by ≥ 0.10 |
| L3 | Risk subscale at follow-up ≥ 0.70 |
| L4 | Risk subscale increased by ≥ 0.15 |
| L5 | GAD-7 increased by ≥ 4 *(only when CORE-OM follow-up absent)* |

**Recovery criteria (R1–R4) — ANY one + guard → recovery = 1**

| ID | Condition |
|----|-----------|
| R1 | Total CORE-OM decreased by ≥ 5 |
| R2 | Problems subscale decreased by ≥ 0.10 |
| R3 | Wellbeing subscale increased by ≥ 0.10 |
| R4 | Functioning subscale increased by ≥ 0.10 |
| Guard | Risk at follow-up **< 0.70** AND relapse criteria **not** met |

**Mutual exclusivity:** When not censored, `recovery_label` and `relapse_label` cannot both be 1.

---

#### Decision tree B — `dropout_label` (independent)

```
START: snapshot date T
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ dropout_label = 1 IF ANY within [T, T+60]:                 │
│   • user_churned event                                     │
│   • therapy program status = terminated                    │
│   • no app_session AND no therapy_attended for 30 days     │
└────────────────────────────────────────────────────────────┘
         │
         └── ELSE dropout_label = 0
```

Never null. Used for retention model — not a clinical assessment outcome.

---

#### Decision tree C — `engagement_loss_label` (independent)

```
START: snapshot date T
         │
         ▼
  baseline = engagement_rate_7d at T
  future   = engagement_rate_7d at T + 14 days
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ engagement_loss_label = 1 IF:                            │
│   future ≤ baseline × 0.50   (50% relative drop)           │
└────────────────────────────────────────────────────────────┘
         │
         └── ELSE engagement_loss_label = 0
```

Never null. Measures behavioral disengagement, not clinical change.

---

#### Worked outcomes (clinical review)

| Scenario | recovery | relapse | Notes |
|----------|----------|---------|-------|
| Total 22→17, risk 0.20→0.15 | **1** | 0 | R1 + guard pass |
| Total 18→19, risk 0.25→0.72 | 0 | **1** | L3 despite small total change |
| Problems ↓, functioning ↓, total flat | 0 | 0 | Stable — subscales offset |
| CORE-OM at T only | **null** | **null** | Censored — exclude from clinical training |
| GAD-7 ↓4+, mood slope ↑, no CORE-OM F/U | **1** | 0 | Secondary confidence |
| Churned day 10, no assessment | **null** | **null** | Censored; dropout likely **1** |

---

#### Clinical sign-off checklist

| # | Item | Sign-off | Date |
|---|------|----------|------|
| 1 | Total MCID = 5 points acceptable for program population | ☐ Clinical lead | |
| 2 | Subscale MCID = 0.10 (normalized) acceptable | ☐ Clinical lead | |
| 3 | Risk threshold 0.70 aligned with escalation policy | ☐ Clinical lead | |
| 4 | Assessment window T+21 to T+45 acceptable vs reassessment cadence | ☐ Clinical + Product | |
| 5 | GAD-7 secondary recovery path acceptable when CORE-OM missing | ☐ Clinical lead | |
| 6 | Censoring (null labels) preferred over defaulting to 0 | ☐ ML + Clinical | |
| 7 | Labels used for ML training only — not shown as diagnosis to users | ☐ Product + Legal | |
| 8 | `label_v2.0.0` registered in model governance | ☐ Engineering | |

**Approved by:** _________________________ **Date:** _____________

---

### Appendix C — CRS unified quick-reference card (v3)

```
┌──────────────────────────────────────────────────────────────────┐
│                    CRS UNIFIED (v3)                               │
├──────────────────────────────────────────────────────────────────┤
│  HEADLINE (mature):  CRS v2 = 0.40×P(recovery)                  │
│                           + 0.20×(1−P(dropout))                  │
│                           + 0.20×(1−P(engagement_loss))          │
│                           + 0.20×(1−P(relapse))                  │
│                                                                  │
│  READINESS (always): Part1 5-category blend (§6.6)              │
│                                                                  │
│  STATE:  Clarity | Emotional Balance | Resilience | Capacity     │
│          (Part1 category weights §7.6)                           │
│                                                                  │
│  TRAJECTORY: 7 trends + direction (↑ ↓ →)                      │
│                                                                  │
│  NARRATIVE: Where / Why / Aware / Risk / Next (§10.4)            │
│                                                                  │
│  SAFETY: IF core_om_risk ≥ 0.70 → cap scores at 40 (§7.7)       │
│                                                                  │
│  Scale: 0–100 | Bands: Low (0-33) Mod (34-66) High (67+)        │
└──────────────────────────────────────────────────────────────────┘
```

### Appendix D — Glossary

| Term | Definition |
|------|-----------|
| **CRS v2** | ML-composite headline score from four outcome probabilities (§6.1) |
| **CRS readiness** | Part1 rule-based same-day readiness from 5 input categories (§6.6) |
| **Pillar** | One of four state scores: Clarity, Emotional Balance, Resilience, Capacity |
| **Input category** | Engine Part1 grouping: Assessment, Lifestyle+Biomarker, Tools, Forms, Therapist |
| **Risk cap** | When `core_om_risk ≥ 0.70`, all display scores capped at 40 (§7.7) |
| **Narrative layer** | API text blocks answering Why / Aware / Risk / Next (§10.4) |
| **Trend metric** | Time-series composite measuring direction of change |
| **Snapshot** | One row of features + labels for a user on a specific date |
| **Outcome model** | ML classifier predicting a binary business/clinical label |
| **SHAP** | SHapley Additive exPlanations — feature attribution for model predictions |
| **Direction** | 7-day trend of a metric: improving, stable, or declining |
| **Band** | Categorical label (Low/Moderate/High) derived from score range |
| **Cohort prior** | Default score (50) used during cold start for missing features |
| **Censored label** | `recovery_label` or `relapse_label` = null when no valid follow-up |
| **MCID** | Minimum Clinically Important Difference — see §2.2.1 |
| **Subscale** | CORE-OM section (wellbeing, problems, functioning, risk) — see §2.2.2 |
| **Label version** | Immutable identifier (e.g. `label_v2.0.0`) for audit |

### Appendix F — Engine Part1 input registry

Complete parameter catalog from **Engine Part1.docx**. Tag: **v1** = in L2 today; **v1.1** = ingestion backlog; **future** = not yet scoped.

#### F.1 CRS readiness — all parameters (Table 1)

| Parameter | Source screen | v1? | Why it matters |
|-----------|---------------|-----|----------------|
| CORE-OM Overall Score | Assessment | Yes | Overall psychological wellbeing and distress |
| CORE-OM Life Functioning | Assessment | Yes | Daily/work functioning |
| CORE-OM Problems Score | Assessment | Yes | Symptom burden |
| CORE-OM Wellbeing Score | Assessment | Yes | Emotional/mental wellbeing state |
| CORE-OM Risk Score | Assessment | Yes | Cap/override if elevated §7.7 |
| Anxiety Score | Assessment | Partial (GAD-7) | Reduces readiness and clarity |
| Depression Score | Assessment | v1.1 (PHQ-9) | Reduces motivation and capacity |
| Trauma Score | Assessment | v1.1 | Affects regulation, sleep, resilience |
| Sleep, Fatigue, HRV, Pulse | Lifestyle Tracker | Partial | Biological readiness anchors |
| Exercise, Nutrition, Hydration | Lifestyle Tracker | v1.1 | Energy and regulation |
| Cortisol, Thyroid/TSH, Blood Sugar | Biomarker | v1.1 | Stress-load and metabolic context |
| Mood, Motivation, Confidence check-in | Daily Check-in | Yes | Emotional trends and engagement |
| Memory Game, Connect Four | Games | v1.1 | Cognitive and behavioural signals |
| Journaling tone/themes | Journal | future | Emotional tone and recovery signals |
| Therapy intent, concerns, patterns | Forms | v1.1 | Contextual severity |
| Therapist / session inputs | Therapy | Partial | Attendance + sheet sync v1.1 |

#### F.2 Clarity parameters (Table 2)

Memory Game, Connect Four, Sleep, Fatigue, HRV, Pulse, Hydration, Nutrition, Hunger, Blood Sugar, Thyroid/TSH, Vitamin D, CORE-OM Functioning, CORE-OM Problems, Motivation Check-In.

#### F.3 Emotional Balance parameters (Table 3)

Mood, Motivation, Confidence check-ins; Blank Slate / Letter to Self / Gratitude journals; Whack A Mole; CORE-OM wellbeing, problems, risk; Anxiety, Depression, Trauma scores; Sleep, Fatigue, Libido; Cortisol, Blood Sugar, Thyroid/TSH.

#### F.4 Resilience parameters (Table 4)

HRV, Sleep, Exercise, Fatigue, Sun Exposure, Nutrition, Hydration, Cortisol, Vitamin D, Thyroid/TSH, CORE-OM delta/previous scores, CORE-OM functioning, CORE-OM risk, Gratitude journal, Motivation check-in, App engagement, Guides usage.

#### F.5 Capacity parameters (Table 5)

CORE-OM functioning, overall, problems, risk; Sleep, Fatigue, HRV, Pulse, Exercise, Nutrition, Hydration, Hunger, Blood Sugar, Thyroid/TSH, HbA1c, Weight Change; Motivation, Confidence check-ins; Session booking / therapy engagement.

**Therapist input sheet:** [Google Sheet — therapist parameters](https://docs.google.com/spreadsheets/d/1yXdZRUPRWBpzAOD4MToN2tVtHtmu312ofC2c3-bTBIc/edit?usp=sharing) (Engine Part1 reference).

### Appendix G — Screen → L0 → L2 lineage

| Product screen | Part1 parameters | L0 `event_type` | L2 column(s) | Pillar / CRS use |
|----------------|------------------|-----------------|--------------|------------------|
| Daily Check-in | Mood, motivation, confidence | `mood_checkin`, `motivation_checkin`, `confidence_checkin` | `mood_avg_14d`, `mood_volatility_14d`, `mood_slope_7d` | Emotional Balance, trends |
| Assessment | CORE-OM, GAD-7, PHQ-9, trauma | `assessment_completed` | `core_om_*`, `gad7_normalized_latest` | All pillars, labels §4.3 |
| Lifestyle Tracker | Sleep, HRV, fatigue, pulse, exercise | `sleep_session`, `heart_rate_daily`, lifestyle events | `sleep_avg_7d`, `hrv_avg`, etc. | CRS readiness, Resilience, Clarity |
| Games | Memory Game, Connect Four | `game_session_completed` (v1.1) | `game_*_score_7d` (v1.1) | Clarity |
| Journal | Tone, themes, gratitude | `journal_entry`, `journal_features_computed` | `journal_sentiment_*` (v1.1) | Emotional Balance, Resilience |
| Forms | Intent, concerns, burnout | `intake_form_submitted` (v1.1) | `form_*` features (v1.1) | All pillars — Forms block |
| Therapy | Sessions, attendance | `session_attended`, `session_missed` | `therapy_attendance_rate` | Capacity, dropout label |
| CRM | User churn | `user_churned` | — (label job only) | `dropout_label` §4.3.7 |
| Biomarkers | Cortisol, TSH, glucose, Vit D | `biomarker_result` (v1.1) | `biomarker_*` (v1.1) | Lifestyle+Biomarker block |

Cross-reference: [Data-Ingestion-Layer-Production-Spec.md §18 Appendix A](./Data-Ingestion-Layer-Production-Spec.md#appendix-a--event-type-catalog).

### Appendix F.6 — Complete attribute index (70 canonical)

**Authoritative binding document:** [final/Engine-Part1-Full-Attribute-Binding-Spec.md](./final/Engine-Part1-Full-Attribute-Binding-Spec.md)

| Scope | Count | State | Trajectory |
|-------|-------|-------|------------|
| Assessment + CORE-OM | A01–A10 | All 5 scores | Stress, Emotional, Cognitive |
| Lifestyle + wearable | A11–A20 | All pillars + CRS | Recovery, Energy, Sleep, Emotional |
| Biomarkers | A21–A26 | CRS, Clarity, Balance, Capacity | Stress, Energy |
| Check-ins | A27–A29 | All scores | Emotional, Motivation, Energy |
| Games | A30–A32 | Clarity, Balance | Cognitive, Emotional |
| Journals | A33–A36 | Balance, Resilience | Emotional, Cognitive |
| App / platform | A37–A42 | CRS, Resilience, Capacity | Motivation, Energy |
| Therapy / sessions | A43, A66–A67 | Capacity, CRS | Motivation |
| Forms (intake) | A44–A65 | Per pillar §3 | Motivation, Emotional, Cognitive |
| Therapist sheet | A68–A70 | All scores (therapist block) | Engagement |

**Policy:** 100% of rows above required in production at `feature_v2.0.0`. Phase 1 ships W1 subset; Phase 5 completes W2–W7.

### Appendix E — Revision history

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| **3.0.0 Unified** | 2026-06-05 | Engine | Merged CRS v2 + Engine Part1; §7.9 §8.9 full attribute binding; Appendix F.6 |
| 2.0.0 | 2026-06-05 | Engineering | Clinical labels v2 (§4.3), Appendix B.1 decision tree |
| 1.0.0 | 2026-06-05 | Engineering | Initial production spec from CRS Calculation with trends.docx |

---

*This document is the **authoritative unified specification** for CRS v3. For the v2-only reference (without Engine Part1 integration), see [CRS-Calculation-and-Trends-Production-Spec.md](./CRS-Calculation-and-Trends-Production-Spec.md). For L0/L2 implementation details, see Data Ingestion and L2 Feature Store specs.*
