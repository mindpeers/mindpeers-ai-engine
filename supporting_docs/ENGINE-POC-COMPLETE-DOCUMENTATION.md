# Mental Health Engine — Complete POC Documentation

**Version:** 3.0 (consolidated)  
**Date:** May 20, 2026  
**Status:** Single source of truth — specification complete, ready for implementation  
**Audience:** Product, engineering, data science, clinical/design reviewers

> **This document replaces** the split POC markdown files. Supporting assets:
> - Sample data: `Engine-POC-Sample-Dataset.xlsx` (sheet `All_Columns_Complete_Sample`)
> - L4 reference: `poc_extract.txt`
> - Validate columns: `python scripts/validate_dataset_columns.py <your-file.xlsx>`

---

## Table of contents

1. [How to use this document](#part-1--program-overview)
2. [Program context & architecture](#part-1--program-overview)
3. [Gap register & product decisions](#part-2--gaps-and-decisions)
4. [Gap deep dive (G1–G15)](#part-3--gap-deep-dive)
5. [L2 — Feature registry & computation](#part-4--l2--feature-registry--computation)
6. [L3 — Scoring service](#part-5--l3--scoring-service)
7. [L1 — Engine snapshot & batch API](#part-6--l1--engine-snapshot--batch-api)
8. [L1 — Patterns & actions](#part-7--l1--patterns--actions)
9. [Dataset columns & validation](#part-8--dataset-columns--validation)
10. [Implementation roadmap & appendices](#part-9--roadmap-and-appendices)

---

---

# Part 1 — Program overview

## 1. How to use this document

This document is the **only consolidated proof of truth** for how the **Engine PRD** (user-facing Cognitive Readiness report) relates to the **Data Contextualization POC** (hybrid ML + LLM intelligence layer) and the **datasets / pillar specifications**.

**Use it when you need to:**

- Decide what to build in v1 vs defer  
- Onboard engineers, PMs, or clinical stakeholders without re-reading four separate files  
- Trace a PRD requirement to a POC intent, dataset column, or gap ID  
- Write tickets: each gap (G1–G15) includes acceptance criteria  

**How gaps are classified**

| Priority | Meaning |
|----------|---------|
| **P0** | Blocks shipping the user-facing Engine report as described in the PRD |
| **P1** | Required for PRD fidelity (copy, charts, clinical trust); can ship a reduced scope only with explicit product sign-off |
| **P2** | Quality, scale, or Phase 2 (org/therapist); does not block a minimal viable Engine |

**Conventions**

- **Aligned** = specification exists and is consistent enough to implement without new product definition  
- **Partial** = direction is clear but schema, formula, or UX detail is missing  
- **Gap** = must be designed and built (see §9)  
- **POC closed** = specification complete in layer POC doc; coding not started

---

## 2. Program context

### 2.1 What the product promises (PRD)

The Engine delivers an **AI-powered mental health report** centered on:

- **Cognitive Readiness Score (CRS)** — single 0–100 score  
- **Four pillars** — Clarity, Emotional Balance, Resilience, Capacity (each 0–100)  
- **Six trend metrics** — Recovery Readiness, Stress Load, Sleep Consistency, Energy Rhythm, Emotional Stability, Motivation & Confidence Momentum  
- **AI insight modules** — patterns, risk watch, driver breakdown, confidence labels  
- **Action layer** — what to do next, tools/resources, self-help, next therapy session  

The report must answer five user questions: *Where am I? Why am I here? What should I be aware of? What is the risk? What should I do next?*

### 2.2 What the POC built

The POC defines a **production-style intelligence pipeline**:

1. Compute **contextual features** (windows, baselines, slopes, flags, cohort percentiles)  
2. Classify **intent** (what kind of answer is needed)  
3. Optionally run **ML models** (dropout, regression, engagement decay, prioritization, ROI)  
4. Generate **LLM explanations** from fixed templates and guardrails  
5. Handle **cold start** via data maturity stages (0–7, 7–30, 30+ days)  

The POC is strong for **dynamic Q&A, risk prediction, and therapist/org operations**. It does **not** define the fixed dashboard scores the PRD shows on every load.

### 2.3 The missing middle layer

Between POC features and PRD UI sits a **Scoring Service** (Layer 3) that:

- Aggregates features into pillar and CRS scores  
- Produces the six named trend composites  
- Computes driver attribution and confidence tiers  
- Feeds both the **dashboard API** and the **LLM context**  

**L3 POC is specified** in [L3-Scoring-Service-POC.md](#part-5--l3--scoring-service). Implementation still required to connect PRD and POC in production.

---

## 3. Source artifacts (detailed)

| ID | File | Owner (typical) | What it contains | How this doc uses it |
|----|------|-----------------|------------------|----------------------|
| **A1** | `Engine Document.docx` | Product | Full PRD: inputs (biological, behavioral, CORE-OM), outputs, trend copy, graph types, AI pattern types, recommendation areas | Defines **Layer 1** requirements |
| **A2** | `Contextuliazation.xlsx` | Product / clinical | Per-pillar data points and rationale; six trend metrics with pillar tags | **Scoring input map** for Layer 3 |
| **A3** | `Data contexualization extended.docx` | Engineering / DS | Architecture, cold start, intent taxonomy, JSON routing config, prompt templates, guardrails | Defines **Layer 4** |
| **A4** | `Data contexualization Datasets.xlsx` | Data / DS | `User_Column_Definitions`, `Business_Column_Definitions`, label logic, math formulas, sample rows | Defines **Layer 2** contract |
| **A5** | `PRD-POC-Alignment-and-Gaps.md` | Program | This document | **Single proof of truth** |
| **A6** | `POC-Documentation-Index.md` + layer POCs | Program / Eng | L2, L3, L1 specs (no code) | **Implementation contracts** |

**Important note on A4 (datasets file):** Sheets named `User_ML_Dataset_50K` and `Business_ML_Dataset_1K` contain **only illustrative rows** for schema review. **Production already holds sufficient real data** at the intended scale. The spreadsheet is the **column and label contract**, not evidence of data shortage.

---

## 4. Executive summary

### 4.1 Layer status

| Layer | Description | PRD | POC | Datasets | Verdict |
|-------|-------------|-----|-----|----------|---------|
| **L1 — Product Engine** | CRS, pillars, trends, patterns, actions | Fully specified | Not implemented | No score columns | **POC closed** — [L1-Engine-Snapshot-POC.md](#part-6--l1--engine-snapshot--batch-api), [L1-Patterns-and-Actions-POC.md](#part-7--l1--patterns--actions) |
| **L2 — Feature store** | Per-user / per-program computed features | Inputs listed | Groups in JSON | Column defs + production data | **POC closed** — [L2-Feature-Registry-POC.md](#part-4--l2--feature-registry--computation) |
| **L3 — Scoring service** | Formulas, weights, trends, drivers | Implied by Excel | Absent in code | Partial formulas | **POC closed** — [L3-Scoring-Service-POC.md](#part-5--l3--scoring-service) |
| **L4 — Intelligence router** | Intent → ML → LLM | Narratives only | Fully specified | Labels match models | **Aligned** — wire to L1 snapshot (G5 POC) |

### 4.2 One-sentence conclusion

**Reuse the POC and production datasets as the intelligence backbone; implement L2 → L3 → L1 batch snapshot per POC package ([POC-Documentation-Index.md](#)).**

### 4.3 Gap status (POC level)

| Status | Count | IDs |
|--------|-------|-----|
| **POC closed** (spec ready) | 15 | G1–G15 |
| **Implementation pending** | 15 | Same — engineering builds to spec |

All gaps have written acceptance criteria in layer POC docs. Code is the next phase.

---

## 5. Target architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│ L1 — PRODUCT ENGINE (PRD + Contextuliazation.xlsx)                        │
│  • Cognitive Readiness Score                                              │
│  • 4 pillars • 6 trends • pattern cards • driver % • confidence          │
│  • Recommendations • content • session prompts                            │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ reads scores + trends daily
┌───────────────────────────────▼──────────────────────────────────────────┐
│ L3 — SCORING SERVICE  ◄── PRIMARY BUILD (G1, G2, G4, G9, G12)          │
│  • Normalize features → 0–100                                           │
│  • Pillar weights • CRS blend • trend composites • attribution            │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ reads features
┌───────────────────────────────▼──────────────────────────────────────────┐
│ L2 — FEATURE STORE (Datasets.xlsx + ingestion + production pipelines)     │
│  • 7d / 14d / 30d windows • flags • cohort percentiles • maturity        │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ on-demand + batch context
┌───────────────────────────────▼──────────────────────────────────────────┐
│ L4 — INTELLIGENCE ROUTER (POC doc + JSON config)                          │
│  • Intent classify → feature fetch → ML? → LLM template → response       │
└──────────────────────────────────────────────────────────────────────────┘
```

**Data flow (steady state):**

1. Raw events (wearables, app, assessments, therapy) → feature pipeline → **L2**  
2. Nightly (or on refresh): **L2** → **L3** → persist scores/trends/drivers → **L1** API  
3. User opens report: **L1** reads precomputed scores; optional chat uses **L4** with same context  
4. Therapist/org views: **L4** operational intents + business features (Phase 2)

---

## 6. Alignment reference (what already fits)

Each item below is **ready to reuse** without re-litigating architecture. Brief explanation is included so reviewers understand *why* it counts as aligned.

### 6.1 Architecture & routing

| # | Aligned item | Explanation |
|---|--------------|-------------|
| A1 | **Hybrid LLM + ML + deterministic features** | POC correctly separates *prediction* (ML), *explanation* (LLM), and *measurement* (features). Matches PRD need for both fixed numbers and natural-language insight. |
| A2 | **Intent taxonomy** (Effectiveness / Guidance / Operational) | Maps 1:1 to PRD question types and to different execution paths (trend vs risk vs recommendation). |
| A3 | **Declarative JSON config** (intent → feature groups → model → template) | Ensures routing is testable and versioned; LLM must not decide which model runs. |
| A4 | **Safety guardrails** (no diagnosis, no medication, uncertainty language) | Required for mental health compliance; templates already embed constraints. |

### 6.2 Data & features

| # | Aligned item | Explanation |
|---|--------------|-------------|
| A5 | **Windowed features** (7d slope, 14d avg, 30d delta) | Same time horizons PRD uses for “last week” / “vs baseline” copy. |
| A6 | **Derived flags** (`withdrawal_flag`, `sleep_mood_coupled_decline`, etc.) | Directly support PRD pattern cards and early warning. |
| A7 | **Cohort percentiles** | Support “compare to similar users” and cold-start imputation per POC. |
| A8 | **`data_completeness_score` + `weeks_in_program`** | Operationalize PRD “confidence in insight” and cold-start messaging. |
| A9 | **Production ML volume** (~50K user, ~1K business) | Sufficient for training and validation; shared xlsx is schema-only (see §10). |

### 6.3 ML & labels

| # | Aligned item | Explanation |
|---|--------------|-------------|
| A10 | **User labels** (dropout 14d, engagement decay 7d, regression 30d) | Definitions in `Label_Generation_logic` match POC model config; trainable today. |
| A11 | **Business labels** (ROI trend, program effective, dropout spike) | Supports org/therapist Phase 2; not required for end-user CRS but aligned with POC scope. |

### 6.4 Product mapping

| # | Aligned item | Explanation |
|---|--------------|-------------|
| A12 | **Pillar → input list** (`Contextuliazation.xlsx`) | Product-approved mapping of which signals feed Clarity, Balance, Resilience, Capacity. |
| A13 | **Six trend metric names** (Excel + PRD) | Naming is stable; need formulas (G2), not renaming. |
| A14 | **Risk Watch narrative path** | `EARLY_WARNING` + risk ML + `risk_explain_v1` template covers PRD “What is the risk?” partially. |

---

## 7. PRD ↔ POC ↔ data mapping

### 7.1 User questions → system behavior

| PRD question | User need | POC category | Primary intents | What user sees |
|--------------|-----------|--------------|-----------------|----------------|
| Where am I right now? | Current state | Effectiveness | `STATUS_CHECK` | CRS, pillars, trend cards |
| Why am I here? | Causes | Guidance | `CORRELATION_ANALYSIS`, `ROOT_CAUSE_ANALYSIS` | Pattern cards, driver % |
| What should I be aware of? | Emerging issues | Guidance | `EARLY_WARNING`, `PATTERN_DETECTION` | Pattern Spotlight, Risk Watch |
| What is the risk? | Forward-looking harm | Operational + Guidance | `RISK_PREDICTION_*` | Risk Watch, probability copy |
| What should I do next? | Actions | Guidance | `GUIDANCE`, `NEXT_BEST_ACTION` | Recommendations, exercises, booking |

### 7.2 Scores and trends — mapping table

| PRD output | Excel (A2) | Dataset columns (A4) | POC (A3) | Gap ID |
|------------|--------------|------------------------|----------|--------|
| CRS | Implied aggregate of pillars | None | None | G1 |
| Clarity | sleep, HRV, routine, CORE-OM functioning | `sleep_*`, `resting_hr_relative`, `activity_slope_7d`, `core_om_delta_30d` | Partial features | G1, G6, G7 |
| Emotional Balance | CORE-OM wellbeing/problems, stress, irregularity | mood, GAD-7, flags | Partial | G1, G7 |
| Resilience | HRV, recovery, sleep consistency, distress trend | sleep, mood persistence, HR | Partial | G1, G6 |
| Capacity | recovery, sleep, functioning, activity, drift | sleep, activity, engagement | Partial | G1, G7 |
| Recovery Readiness | Biological trend | sleep_delta, HR relative | No composite | G2, G6 |
| Stress Load | Biological trend | cortisol_flag, HR | No episodes | G2, G6 |
| Sleep Consistency | Bio + behavioral | sleep_avg, persistence | No bed/wake variance | G2 |
| Energy Rhythm | Behavioral | activity_slope, engagement | No 24h curve | G2 |
| Emotional Stability | Psychological | mood_volatility, mood_slope | Can compute | G2 |
| Motivation & Confidence Momentum | Psych + behavioral | **Missing in A4** | In JSON only | G2, G8 |

---

---

# Part 2 — Gaps and decisions

## 8. Gap register — summary table

| ID | Priority | Title | POC status | Spec |
|----|----------|-------|------------|------|
| G1 | P0 | No CRS or pillar scoring engine | **Closed** | [L3 §7](#part-5--l3--scoring-service) |
| G2 | P0 | No six PRD trend composites | **Closed** | [L3 §8](#part-5--l3--scoring-service) |
| G3 | P0 | Feature registry / naming inconsistency | **Closed** | [L2 §2](#part-4--l2--feature-registry--computation) |
| G4 | P0 | Incomplete feature computation spec | **Closed** | [L2 §3](#part-4--l2--feature-registry--computation) |
| G5 | P0 | Dashboard requires batch pipeline | **Closed** | [L1 Snapshot](#part-6--l1--engine-snapshot--batch-api) |
| G6 | P1 | Wearable / biological field gaps | **Closed** (proxy v1) | [L3 §8](#part-5--l3--scoring-service), D1 |
| G7 | P1 | CORE-OM subscore granularity | **Closed** | [L2 §3.2](#part-4--l2--feature-registry--computation) |
| G8 | P1 | Motivation / confidence not in dataset | **Closed** | [L2 §3.4](#part-4--l2--feature-registry--computation) |
| G9 | P1 | Driver breakdown % undefined | **Closed** | [L3 §9](#part-5--l3--scoring-service) |
| G10 | P1 | Structured AI pattern module | **Closed** | [L1 Patterns §1](#part-7--l1--patterns--actions) |
| G11 | P1 | Recommendations & content catalog | **Closed** | [L1 Patterns §2](#part-7--l1--patterns--actions) |
| G12 | P2 | Composite risk weights undefined | **Closed** | [L3 §9.3](#part-5--l3--scoring-service) |
| G13 | P2 | Visualization / chart layer | **Closed** (heatmap v1.1) | [L1 Snapshot §3](#part-6--l1--engine-snapshot--batch-api) |
| G14 | P2 | Business ML not in user Engine PRD | **Closed** (Phase 2) | §10 below |
| G15 | P2 | `system_type` channel handling | **Closed** | [L3 §5](#part-5--l3--scoring-service) |

---

## 9. Gap deep dive (full explanations)

---

### G1 — No CRS or pillar scoring engine (P0)

**Summary:** The PRD’s primary deliverable is four pillar scores (0–100) and a Cognitive Readiness Score. None of the artifacts define how to calculate these numbers from features.

**Current state**

| Artifact | State |
|----------|--------|
| PRD (A1) | Requires CRS + Clarity, Emotional Balance, Resilience, Capacity |
| Excel (A2) | Lists *inputs* per pillar and why each matters; no weights or formula |
| Datasets (A4) | Feature columns only; no `clarity_score`, `crs`, etc. |
| POC (A3) | Uses features in LLM context; does not output product scores |

**Why it matters**

- Without deterministic scores, the dashboard cannot render the main UI spec.  
- LLM-only scores would be non-reproducible, hard to regulate clinically, and impossible to trend chart consistently.  
- Pillars are the bridge between raw data and user-understandable mental performance framing.

**Recommended solution**

1. Product/clinical sign-off on **pillar weights** per `Contextuliazation.xlsx` rows (e.g. Clarity = weighted mix of sleep efficiency, HRV/recovery proxy, routine consistency, CORE-OM functioning).  
2. Engineering implements **Scoring Service (L3)**:
   - Normalize each input to 0–100 (personal baseline if maturity ≥ 30d, else cohort prior).  
   - Compute each pillar as weighted average of normalized inputs.  
   - Compute **CRS** = weighted average of four pillars (default: equal 25% until product specifies otherwise).  
3. Persist daily: `clarity_score`, `emotional_balance_score`, `resilience_score`, `capacity_score`, `cognitive_readiness_score`, `score_version`, `confidence_tier`.  
4. Pass scores into LLM context for narratives (Pattern Spotlight, STATUS_CHECK).

**Dependencies:** G3 (canonical feature names), G4 (feature computation), cold-start rules from POC.

**Acceptance criteria**

- [ ] Given a user with full maturity, API returns all five scores 0–100 for today  
- [ ] Given cold-start user, scores use cohort prior and return `confidence_tier = Limited`  
- [ ] Same inputs produce identical scores across batch and API (deterministic)  
- [ ] Unit tests cover min/max/missing input behavior  

**Suggested owners:** Product (weights), Data science (normalization), Engineering (service)

---

### G2 — No six PRD trend composites (P0)

**Summary:** The PRD defines six named trend metrics with specific card copy and charts. The feature store has primitives (e.g. `mood_volatility_14d`) but not the six composite scores the UI labels use.

**Current state**

| Trend (PRD) | Available primitives | Missing for full PRD |
|-------------|---------------------|----------------------|
| Recovery Readiness | `sleep_delta_30d`, `resting_hr_relative` | HRV, recovery score, strain vs baseline |
| Stress Load | `cortisol_flag`, HR relative | Stress episodes, duration above baseline, recovery lag |
| Sleep Consistency | `sleep_avg_7d`, `sleep_persistence_low_days` | Bedtime/wake variance, sleep debt |
| Energy Rhythm | `activity_slope_7d`, engagement | 24h activity/engagement curve, circadian metric |
| Emotional Stability | `mood_volatility_14d`, `mood_slope_7d` | Mostly computable |
| Motivation & Confidence Momentum | POC JSON only | Dataset columns (G8) |

**Why it matters**

- Trend section is ~40% of the PRD UX (cards + dual-line graphs + heatmaps).  
- Users expect consistent labels (“Recovery Readiness: Moderate”) not raw feature values.  
- Trend composites must be time-series for charts (7–30 day history).

**Recommended solution**

1. Define **trend composite spec** (one doc or sheet) with per-metric:
   - Input features (from registry)  
   - Formula (weighted sum, min/max cap, categorical band: Low/Moderate/High)  
   - Minimum data required (maturity gate)  
2. Implement in L3 alongside pillars; store `trend_recovery_readiness`, etc., with history table.  
3. Map PRD card copy templates to score bands (e.g. 0–33 = Low).  
4. For metrics blocked by missing wearables (G6), either compute **proxy** or hide card with explanation.

**Dependencies:** G1 (shared normalization), G6/G8 (inputs), G5 (batch for history).

**Acceptance criteria**

- [ ] All six trends exposed via API with score, band label, and 14d history where maturity allows  
- [ ] Emotional Stability computable from existing features without wearable data  
- [ ] Trends with insufficient data return `available: false` and PRD-aligned message  

**Suggested owners:** Product (bands + copy), Data science (formulas), Engineering (pipeline)

---

### G3 — Feature registry / naming inconsistency (P0)

**Summary:** The same concepts appear under different names or exist in only one artifact. Building L2 and L3 without a canonical registry will cause silent bugs in ML, scoring, and LLM context.

**Known drift (non-exhaustive)**

| Concept | Datasets (A4) | POC JSON (A3) | Action |
|---------|---------------|---------------|--------|
| 14-day mood average | `avg_mood_14d` | `mood_avg_14d` | Pick `mood_avg_14d` |
| Motivation / confidence | Missing | Present | Add to A4 + pipeline |
| CORE-OM level score | Missing | `core_om_normalized_score` | Add to A4 |
| PHQ-9, PTSD, ASRS | Missing | Present | Add or mark out-of-scope for v1 |
| Journaling concern | `journaling_concern_score_7d` | Missing | Add to POC groups |

**Why it matters**

- Training pipelines, scoring service, and LLM prompts must reference **one** column name.  
- Refactors after launch are expensive when models and dashboards are live.

**Recommended solution**

1. Publish **`feature_registry_v1.json`** (or table) as authoritative:
   - `canonical_name`, `type`, `window`, `computation_ref`, `source_system`, `maturity_min_days`, `used_by` (pillars, trends, models, intents)  
2. CI check: production export columns ⊆ registry; registry entries used in code must exist.  
3. Bump `feature_version` when registry changes.

**Acceptance criteria**

- [ ] Single registry file approved by data + engineering  
- [ ] Zero naming mismatches between datasets column defs and POC JSON  
- [ ] Scoring and ML configs load features by canonical name only  

---

### G4 — Incomplete feature computation specification (P0)

**Summary:** `Feature_computation_logic` in A4 documents only six features explicitly. `User_Column_Definitions` describes ~35 columns mostly in prose. Engineers cannot implement L2 consistently without full rules.

**Why it matters**

- Different developers will implement deltas/slopes differently (edge cases: gaps in data, timezone, session boundaries).  
- Reproducibility between training snapshots and online features breaks model quality.  
- Scoring layer (G1) depends on stable upstream features.

**Recommended solution**

1. Extend A4 (or registry) so **every** feature has:
   - Window (e.g. 7d, 30d)  
   - Formula (reference `Mathematical_Formulas` patterns)  
   - Null handling (skip vs impute vs cohort prior)  
   - Example SQL/pseudocode  
2. Priority order: features used in pillars → trends → ML models → optional.  
3. Align threshold rules with existing examples:
   - `withdrawal_flag`: `engagement_rate_7d < 0.25`  
   - `sleep_mood_coupled_decline`: `sleep_delta_30d < -1.5 AND mood_slope_7d < -0.3`

**Acceptance criteria**

- [ ] 100% of registry features have computation reference  
- [ ] Backtest: recomputing features for sample users matches production snapshot within tolerance  

---

### G5 — Dashboard requires batch pipeline, not query-only POC (P0)

**Summary:** The POC execution model is `handle_query(query, user_id)` — intelligence on demand. The PRD Engine is a **always-on report**: scores, trends, and 2–4 pattern cards must exist when the user opens the app without asking a question.

**Why it matters**

- Latency: computing full feature + score + pattern set on each page load is too slow and costly at scale.  
- Consistency: all users see the same daily snapshot; narratives match displayed numbers.  
- Offline/mobile: precomputed API enables caching.

**Recommended solution**

1. **Batch job** (daily or on significant data refresh):
   - Compute L2 features → L3 scores/trends → pattern selection → store in `user_engine_snapshot`  
2. **Read API** for mobile/web: GET `/users/{id}/engine/report?date=`  
3. **Chat/query** path still uses L4 but **must read the same snapshot** as context (no divergent LLM numbers).  
4. Pattern rotation: store `pattern_cards[]` with `pattern_id`, `type`, `expires_at` to avoid flicker.

**Acceptance criteria**

- [ ] Report loads from snapshot in &lt; 200ms p95 (excluding network)  
- [ ] Chat answers reference same CRS/pillars as dashboard for that date  
- [ ] Batch failure alerts; stale snapshot shows “last updated” timestamp  

---

### G6 — Wearable / biological field gaps (P1)

**Summary:** PRD §2.1 lists extensive wearable fields (HRV, REM/deep %, stress episodes, skin temp, etc.). User dataset contract (A4) covers basic sleep, HR relative, activity slope, and `cortisol_flag` only.

**Why it matters**

- **Recovery Readiness**, **Stress Load**, and **Resilience** PRD copy assume richer physiology.  
- Without HRV/stress episodes, biological trend charts and heatmaps cannot match PRD fidelity.  
- Product may still ship v1 with proxies if scope is explicit.

**Options (product decision — see §11)**

| Option | Tradeoff |
|--------|----------|
| **A — Full wearable v1** | Extend ingestion + schema; longest timeline |
| **B — Reduced biological v1** | Proxy scores from sleep + HR; update PRD copy; faster ship |
| **C — Phased** | Ship B; add wearables in v1.1 with score version bump |

**Recommended solution (if Option B)**

- Document v1 biological scope in PRD addendum.  
- Recovery Readiness = f(sleep_delta, sleep_persistence, resting_hr_relative).  
- Stress Load = f(cortisol_flag, HR elevation duration proxy from available data).  
- Hide heatmaps that require sub-day stress episodes.

**Acceptance criteria**

- [ ] Signed scope doc (A, B, or C)  
- [ ] Trends not shown when required inputs missing (no fake precision)  

---

### G7 — CORE-OM subscore granularity (P1)

**Summary:** PRD requires wellbeing, problems/symptoms, functioning, and risk sub-scores plus deltas. Production features include only `core_om_delta_30d` (aggregate change).

**Why it matters**

- Excel maps **functioning** to Clarity and Capacity, **wellbeing/problems** to Emotional Balance.  
- Aggregate delta alone cannot drive pillar splits or clinically meaningful copy.  
- Risk sub-score is called out in PRD for “What is the risk?”

**Recommended solution**

1. Ingest per-subscale normalized scores: `core_om_wellbeing`, `core_om_problems`, `core_om_functioning`, `core_om_risk`.  
2. Add 30d deltas per subscale.  
3. Wire into pillar formulas (G1) per Excel mapping.  
4. Use risk subscale in operational rules (escalation), not as diagnosis (guardrails).

**Acceptance criteria**

- [ ] All four subscales in feature registry and daily snapshot  
- [ ] Pillar scores change when only functioning moves, holding others constant (test case)  

---

### G8 — Motivation / confidence features missing from dataset contract (P1)

**Summary:** POC JSON includes `motivation_avg_14d`, `motivation_slope_7d`, `confidence_avg_14d`, `confidence_slope_7d`. These feed PRD **Motivation & Confidence Momentum** but are absent from `User_Column_Definitions`.

**Why it matters**

- PRD trend #6 and psychological section depend on these signals.  
- LLM intents for TREND_ANALYSIS and GUIDANCE expect them in context.

**Recommended solution**

1. Define source: check-in questions, in-app sliders, or derived from engagement proxies.  
2. Add columns to A4 + production pipeline with same window semantics as mood.  
3. Add to `emotional_core` feature group in POC JSON.  
4. Include in trend composite (G2).

**Acceptance criteria**

- [ ] Motivation/confidence features in registry and production parity  
- [ ] Trend “Motivation & Confidence Momentum” computable for users with check-in history  

---

### G9 — Driver breakdown % undefined (bio / behavior / psych) (P1)

**Summary:** PRD shows “Biological influence: 42% | Behavioral: 31% | Psychological: 27%”. POC mentions `composite_risk = weighted_sum(domain_features)` without published weights or mapping to pillars.

**Why it matters**

- Users trust the report when they understand *what is driving* readiness.  
- Must not feel arbitrary; should tie to same inputs as pillars.  
- Regulatory/comms: present as “influence” not causal medical claim.

**Recommended solution**

1. **Approach 1 (rule-based):** Attribute ΔCRS over 7d to pillar groups tagged biological / behavioral / psychological per Excel.  
2. **Approach 2 (model-based):** SHAP on CRS model — heavier lift, needs careful validation.  
3. Normalize to 100%; hide section if `confidence_tier = Limited` or maturity &lt; 7d.  
4. Align domain feature lists with G12 weights where possible.

**Acceptance criteria**

- [ ] Driver percents sum to 100% ± rounding  
- [ ] Copy uses “may be influenced by” per guardrails  
- [ ] Section hidden when insufficient data  

---

### G10 — Structured AI pattern module (P1)

**Summary:** PRD specifies six pattern types (correlation, time-based, warning, positive, drift, recovery) and modules: Pattern Spotlight, Risk Watch, Improvement Signal. POC has flags and `CORRELATION_ANALYSIS` but no pattern taxonomy or rotation rules.

**Why it matters**

- Patterns are the main “AI feels smart” surface without exposing raw ML scores.  
- Rotation (2–4 cards max) prevents clutter and stale insights.

**Recommended solution**

1. **Pattern catalog** table: `pattern_type`, `rule_definition`, `min_maturity`, `priority`, `template_id`.  
2. **Rule engine** evaluates rules on snapshot (deterministic).  
3. **LLM** only generates natural-language from structured match (not discovery).  
4. Examples:
   - Correlation: `sleep_mood_coupled_decline == 1`  
   - Drift: `mood_slope_7d < -0.2` for 14d  
   - Warning: `label_regression_30d` model prob &gt; 0.6  
   - Positive: sleep consistency up 3 days + volatility down  
5. Rotate: max 4 active; deprioritize shown in last 7d.

**Acceptance criteria**

- [ ] Each pattern type has at least one implemented rule  
- [ ] Dashboard shows 2–4 cards; no duplicate `pattern_id` within 7d  
- [ ] LLM output passes guardrail automated checks  

---

### G11 — Recommendations, self-help, and next session (P1)

**Summary:** PRD bottom sections require actionable next steps: exercises, worksheets, videos, self-help library, therapy booking. POC `GUIDANCE` intent produces generic bullets without a content catalog or booking integration.

**Why it matters**

- Closes the loop on “What should I do next?”  
- Differentiates product from read-only analytics.  
- Requires CMS/integration work beyond ML.

**Recommended solution**

1. **Content catalog** with tags: pillar deficit, risk tier, modality (video, worksheet), contraindications.  
2. **Recommendation rules**: e.g. low Clarity + poor sleep → sleep hygiene resource ID.  
3. Optional: LLM re-ranks top 3 from catalog (never invent new medical advice).  
4. **Next session**: integrate scheduling API; trigger when risk &gt; threshold or user request.

**Acceptance criteria**

- [ ] At least N curated items per pillar theme  
- [ ] Recommendations deterministic for same snapshot (LLM optional polish only)  
- [ ] Booking CTA works for eligible users  

---

### G12 — Composite risk weights undefined (P2)

**Summary:** `composite_risk_percentile` exists in data but formula weights across domains are not documented. PRD driver breakdown (G9) should align with same domain definitions.

**Why it matters**

- Therapist prioritization and Risk Watch may use composite risk.  
- Inconsistent weights between ML training and user-facing drivers erode trust.

**Recommended solution**

1. Document weight vector (e.g. emotional 0.35, behavioral 0.30, physiological 0.20, clinical 0.15).  
2. Version alongside `feature_version`.  
3. Use same domains in G9 attribution.

**Acceptance criteria**

- [ ] Published formula matches production feature computation  
- [ ] Versioned change process documented  

---

### G13 — Visualization / chart layer (P2)

**Summary:** PRD specifies dual-line trends, baseline deviation bars, stress heatmaps, sleep band graphs, mood volatility bands. No chart API or time-series contract exists yet.

**Why it matters**

- Large part of user value is temporal context, not single numbers.  
- Charts need consistent time-series keys from G2 batch history.

**Recommended solution**

1. API: `GET .../engine/trends/{metric}/series?days=30`  
2. Return `{ date, value, baseline, band }` per PRD graph type.  
3. Frontend renders; heatmaps need sub-day stress data (G6).

**Acceptance criteria**

- [ ] Dual-line Recovery vs Stress renders from API data  
- [ ] Charts respect maturity (no fake baseline before day 30)  

---

### G14 — Business ML track outside user Engine PRD (P2)

**Summary:** Business dataset and POC intents (`ORG_ROI_ANALYSIS`, `PRIORITIZATION`) serve orgs and therapists. Engine PRD is end-user focused.

**Why it matters**

- Prevents scope creep on Engine MVP.  
- Still valuable Phase 2 revenue/analytics surface.

**Recommended solution**

- Track as **Phase 2** program; reuse L2 feature store aggregations at program level.  
- Do not block G1–G5 on business models.

**Acceptance criteria**

- [ ] Phase 2 roadmap ticket exists with separate PRD or section  

---

### G15 — `system_type` (web-only vs full) channel handling (P2)

**Summary:** Dataset defines `system_type`: 1 = Normal, 0 = Only web. Web-only users lack wearable fields; same formulas would mislead.

**Why it matters**

- Feature completeness and confidence differ by channel.  
- Cold-start priors may differ for web-only cohort.

**Recommended solution**

1. Registry marks features `requires_wearable: true/false`.  
2. Scoring excludes biological inputs when unavailable; adjust confidence.  
3. Separate cohort priors optional for `system_type = 0`.

**Acceptance criteria**

- [ ] Web-only user never shown HRV-based copy  
- [ ] `data_completeness_score` reflects channel  

---

## 11. Product decisions (closed)

All decisions resolved for v1 POC. Override requires version bump on `score_version` / `feature_version`.

| ID | Decision | Chosen option | Date | Impacts |
|----|----------|---------------|------|---------|
| D1 | Wearables in v1? | **Phased (C):** proxy biological v1; full wearables v1.1 | 2026-05-20 | G6, G2, G13 heatmap |
| D2 | CRS formula | **Equal 25%** per pillar | 2026-05-20 | G1 |
| D3 | Clinical instruments | **CORE-OM subscales + GAD-7**; PHQ-9/PTSD/ASRS v1.1 | 2026-05-20 | G7 |
| D4 | Cohort comparison | **Therapist-only** on end-user Engine | 2026-05-20 | UX, privacy |
| D5 | Driver visibility | **Hide** when Limited or &lt; 7 days | 2026-05-20 | G9 |
| D6 | Recommendations | **Rules-first**; optional LLM polish from catalog | 2026-05-20 | G11 |

---

---

# Part 3 — Gap deep dive

## 9. Gap deep dive (full explanations)

---

### G1 — No CRS or pillar scoring engine (P0)

**Summary:** The PRD’s primary deliverable is four pillar scores (0–100) and a Cognitive Readiness Score. None of the artifacts define how to calculate these numbers from features.

**Current state**

| Artifact | State |
|----------|--------|
| PRD (A1) | Requires CRS + Clarity, Emotional Balance, Resilience, Capacity |
| Excel (A2) | Lists *inputs* per pillar and why each matters; no weights or formula |
| Datasets (A4) | Feature columns only; no `clarity_score`, `crs`, etc. |
| POC (A3) | Uses features in LLM context; does not output product scores |

**Why it matters**

- Without deterministic scores, the dashboard cannot render the main UI spec.  
- LLM-only scores would be non-reproducible, hard to regulate clinically, and impossible to trend chart consistently.  
- Pillars are the bridge between raw data and user-understandable mental performance framing.

**Recommended solution**

1. Product/clinical sign-off on **pillar weights** per `Contextuliazation.xlsx` rows (e.g. Clarity = weighted mix of sleep efficiency, HRV/recovery proxy, routine consistency, CORE-OM functioning).  
2. Engineering implements **Scoring Service (L3)**:
   - Normalize each input to 0–100 (personal baseline if maturity ≥ 30d, else cohort prior).  
   - Compute each pillar as weighted average of normalized inputs.  
   - Compute **CRS** = weighted average of four pillars (default: equal 25% until product specifies otherwise).  
3. Persist daily: `clarity_score`, `emotional_balance_score`, `resilience_score`, `capacity_score`, `cognitive_readiness_score`, `score_version`, `confidence_tier`.  
4. Pass scores into LLM context for narratives (Pattern Spotlight, STATUS_CHECK).

**Dependencies:** G3 (canonical feature names), G4 (feature computation), cold-start rules from POC.

**Acceptance criteria**

- [ ] Given a user with full maturity, API returns all five scores 0–100 for today  
- [ ] Given cold-start user, scores use cohort prior and return `confidence_tier = Limited`  
- [ ] Same inputs produce identical scores across batch and API (deterministic)  
- [ ] Unit tests cover min/max/missing input behavior  

**Suggested owners:** Product (weights), Data science (normalization), Engineering (service)

---

### G2 — No six PRD trend composites (P0)

**Summary:** The PRD defines six named trend metrics with specific card copy and charts. The feature store has primitives (e.g. `mood_volatility_14d`) but not the six composite scores the UI labels use.

**Current state**

| Trend (PRD) | Available primitives | Missing for full PRD |
|-------------|---------------------|----------------------|
| Recovery Readiness | `sleep_delta_30d`, `resting_hr_relative` | HRV, recovery score, strain vs baseline |
| Stress Load | `cortisol_flag`, HR relative | Stress episodes, duration above baseline, recovery lag |
| Sleep Consistency | `sleep_avg_7d`, `sleep_persistence_low_days` | Bedtime/wake variance, sleep debt |
| Energy Rhythm | `activity_slope_7d`, engagement | 24h activity/engagement curve, circadian metric |
| Emotional Stability | `mood_volatility_14d`, `mood_slope_7d` | Mostly computable |
| Motivation & Confidence Momentum | POC JSON only | Dataset columns (G8) |

**Why it matters**

- Trend section is ~40% of the PRD UX (cards + dual-line graphs + heatmaps).  
- Users expect consistent labels (“Recovery Readiness: Moderate”) not raw feature values.  
- Trend composites must be time-series for charts (7–30 day history).

**Recommended solution**

1. Define **trend composite spec** (one doc or sheet) with per-metric:
   - Input features (from registry)  
   - Formula (weighted sum, min/max cap, categorical band: Low/Moderate/High)  
   - Minimum data required (maturity gate)  
2. Implement in L3 alongside pillars; store `trend_recovery_readiness`, etc., with history table.  
3. Map PRD card copy templates to score bands (e.g. 0–33 = Low).  
4. For metrics blocked by missing wearables (G6), either compute **proxy** or hide card with explanation.

**Dependencies:** G1 (shared normalization), G6/G8 (inputs), G5 (batch for history).

**Acceptance criteria**

- [ ] All six trends exposed via API with score, band label, and 14d history where maturity allows  
- [ ] Emotional Stability computable from existing features without wearable data  
- [ ] Trends with insufficient data return `available: false` and PRD-aligned message  

**Suggested owners:** Product (bands + copy), Data science (formulas), Engineering (pipeline)

---

### G3 — Feature registry / naming inconsistency (P0)

**Summary:** The same concepts appear under different names or exist in only one artifact. Building L2 and L3 without a canonical registry will cause silent bugs in ML, scoring, and LLM context.

**Known drift (non-exhaustive)**

| Concept | Datasets (A4) | POC JSON (A3) | Action |
|---------|---------------|---------------|--------|
| 14-day mood average | `avg_mood_14d` | `mood_avg_14d` | Pick `mood_avg_14d` |
| Motivation / confidence | Missing | Present | Add to A4 + pipeline |
| CORE-OM level score | Missing | `core_om_normalized_score` | Add to A4 |
| PHQ-9, PTSD, ASRS | Missing | Present | Add or mark out-of-scope for v1 |
| Journaling concern | `journaling_concern_score_7d` | Missing | Add to POC groups |

**Why it matters**

- Training pipelines, scoring service, and LLM prompts must reference **one** column name.  
- Refactors after launch are expensive when models and dashboards are live.

**Recommended solution**

1. Publish **`feature_registry_v1.json`** (or table) as authoritative:
   - `canonical_name`, `type`, `window`, `computation_ref`, `source_system`, `maturity_min_days`, `used_by` (pillars, trends, models, intents)  
2. CI check: production export columns ⊆ registry; registry entries used in code must exist.  
3. Bump `feature_version` when registry changes.

**Acceptance criteria**

- [ ] Single registry file approved by data + engineering  
- [ ] Zero naming mismatches between datasets column defs and POC JSON  
- [ ] Scoring and ML configs load features by canonical name only  

---

### G4 — Incomplete feature computation specification (P0)

**Summary:** `Feature_computation_logic` in A4 documents only six features explicitly. `User_Column_Definitions` describes ~35 columns mostly in prose. Engineers cannot implement L2 consistently without full rules.

**Why it matters**

- Different developers will implement deltas/slopes differently (edge cases: gaps in data, timezone, session boundaries).  
- Reproducibility between training snapshots and online features breaks model quality.  
- Scoring layer (G1) depends on stable upstream features.

**Recommended solution**

1. Extend A4 (or registry) so **every** feature has:
   - Window (e.g. 7d, 30d)  
   - Formula (reference `Mathematical_Formulas` patterns)  
   - Null handling (skip vs impute vs cohort prior)  
   - Example SQL/pseudocode  
2. Priority order: features used in pillars → trends → ML models → optional.  
3. Align threshold rules with existing examples:
   - `withdrawal_flag`: `engagement_rate_7d < 0.25`  
   - `sleep_mood_coupled_decline`: `sleep_delta_30d < -1.5 AND mood_slope_7d < -0.3`

**Acceptance criteria**

- [ ] 100% of registry features have computation reference  
- [ ] Backtest: recomputing features for sample users matches production snapshot within tolerance  

---

### G5 — Dashboard requires batch pipeline, not query-only POC (P0)

**Summary:** The POC execution model is `handle_query(query, user_id)` — intelligence on demand. The PRD Engine is a **always-on report**: scores, trends, and 2–4 pattern cards must exist when the user opens the app without asking a question.

**Why it matters**

- Latency: computing full feature + score + pattern set on each page load is too slow and costly at scale.  
- Consistency: all users see the same daily snapshot; narratives match displayed numbers.  
- Offline/mobile: precomputed API enables caching.

**Recommended solution**

1. **Batch job** (daily or on significant data refresh):
   - Compute L2 features → L3 scores/trends → pattern selection → store in `user_engine_snapshot`  
2. **Read API** for mobile/web: GET `/users/{id}/engine/report?date=`  
3. **Chat/query** path still uses L4 but **must read the same snapshot** as context (no divergent LLM numbers).  
4. Pattern rotation: store `pattern_cards[]` with `pattern_id`, `type`, `expires_at` to avoid flicker.

**Acceptance criteria**

- [ ] Report loads from snapshot in &lt; 200ms p95 (excluding network)  
- [ ] Chat answers reference same CRS/pillars as dashboard for that date  
- [ ] Batch failure alerts; stale snapshot shows “last updated” timestamp  

---

### G6 — Wearable / biological field gaps (P1)

**Summary:** PRD §2.1 lists extensive wearable fields (HRV, REM/deep %, stress episodes, skin temp, etc.). User dataset contract (A4) covers basic sleep, HR relative, activity slope, and `cortisol_flag` only.

**Why it matters**

- **Recovery Readiness**, **Stress Load**, and **Resilience** PRD copy assume richer physiology.  
- Without HRV/stress episodes, biological trend charts and heatmaps cannot match PRD fidelity.  
- Product may still ship v1 with proxies if scope is explicit.

**Options (product decision — see §11)**

| Option | Tradeoff |
|--------|----------|
| **A — Full wearable v1** | Extend ingestion + schema; longest timeline |
| **B — Reduced biological v1** | Proxy scores from sleep + HR; update PRD copy; faster ship |
| **C — Phased** | Ship B; add wearables in v1.1 with score version bump |

**Recommended solution (if Option B)**

- Document v1 biological scope in PRD addendum.  
- Recovery Readiness = f(sleep_delta, sleep_persistence, resting_hr_relative).  
- Stress Load = f(cortisol_flag, HR elevation duration proxy from available data).  
- Hide heatmaps that require sub-day stress episodes.

**Acceptance criteria**

- [ ] Signed scope doc (A, B, or C)  
- [ ] Trends not shown when required inputs missing (no fake precision)  

---

### G7 — CORE-OM subscore granularity (P1)

**Summary:** PRD requires wellbeing, problems/symptoms, functioning, and risk sub-scores plus deltas. Production features include only `core_om_delta_30d` (aggregate change).

**Why it matters**

- Excel maps **functioning** to Clarity and Capacity, **wellbeing/problems** to Emotional Balance.  
- Aggregate delta alone cannot drive pillar splits or clinically meaningful copy.  
- Risk sub-score is called out in PRD for “What is the risk?”

**Recommended solution**

1. Ingest per-subscale normalized scores: `core_om_wellbeing`, `core_om_problems`, `core_om_functioning`, `core_om_risk`.  
2. Add 30d deltas per subscale.  
3. Wire into pillar formulas (G1) per Excel mapping.  
4. Use risk subscale in operational rules (escalation), not as diagnosis (guardrails).

**Acceptance criteria**

- [ ] All four subscales in feature registry and daily snapshot  
- [ ] Pillar scores change when only functioning moves, holding others constant (test case)  

---

### G8 — Motivation / confidence features missing from dataset contract (P1)

**Summary:** POC JSON includes `motivation_avg_14d`, `motivation_slope_7d`, `confidence_avg_14d`, `confidence_slope_7d`. These feed PRD **Motivation & Confidence Momentum** but are absent from `User_Column_Definitions`.

**Why it matters**

- PRD trend #6 and psychological section depend on these signals.  
- LLM intents for TREND_ANALYSIS and GUIDANCE expect them in context.

**Recommended solution**

1. Define source: check-in questions, in-app sliders, or derived from engagement proxies.  
2. Add columns to A4 + production pipeline with same window semantics as mood.  
3. Add to `emotional_core` feature group in POC JSON.  
4. Include in trend composite (G2).

**Acceptance criteria**

- [ ] Motivation/confidence features in registry and production parity  
- [ ] Trend “Motivation & Confidence Momentum” computable for users with check-in history  

---

### G9 — Driver breakdown % undefined (bio / behavior / psych) (P1)

**Summary:** PRD shows “Biological influence: 42% | Behavioral: 31% | Psychological: 27%”. POC mentions `composite_risk = weighted_sum(domain_features)` without published weights or mapping to pillars.

**Why it matters**

- Users trust the report when they understand *what is driving* readiness.  
- Must not feel arbitrary; should tie to same inputs as pillars.  
- Regulatory/comms: present as “influence” not causal medical claim.

**Recommended solution**

1. **Approach 1 (rule-based):** Attribute ΔCRS over 7d to pillar groups tagged biological / behavioral / psychological per Excel.  
2. **Approach 2 (model-based):** SHAP on CRS model — heavier lift, needs careful validation.  
3. Normalize to 100%; hide section if `confidence_tier = Limited` or maturity &lt; 7d.  
4. Align domain feature lists with G12 weights where possible.

**Acceptance criteria**

- [ ] Driver percents sum to 100% ± rounding  
- [ ] Copy uses “may be influenced by” per guardrails  
- [ ] Section hidden when insufficient data  

---

### G10 — Structured AI pattern module (P1)

**Summary:** PRD specifies six pattern types (correlation, time-based, warning, positive, drift, recovery) and modules: Pattern Spotlight, Risk Watch, Improvement Signal. POC has flags and `CORRELATION_ANALYSIS` but no pattern taxonomy or rotation rules.

**Why it matters**

- Patterns are the main “AI feels smart” surface without exposing raw ML scores.  
- Rotation (2–4 cards max) prevents clutter and stale insights.

**Recommended solution**

1. **Pattern catalog** table: `pattern_type`, `rule_definition`, `min_maturity`, `priority`, `template_id`.  
2. **Rule engine** evaluates rules on snapshot (deterministic).  
3. **LLM** only generates natural-language from structured match (not discovery).  
4. Examples:
   - Correlation: `sleep_mood_coupled_decline == 1`  
   - Drift: `mood_slope_7d < -0.2` for 14d  
   - Warning: `label_regression_30d` model prob &gt; 0.6  
   - Positive: sleep consistency up 3 days + volatility down  
5. Rotate: max 4 active; deprioritize shown in last 7d.

**Acceptance criteria**

- [ ] Each pattern type has at least one implemented rule  
- [ ] Dashboard shows 2–4 cards; no duplicate `pattern_id` within 7d  
- [ ] LLM output passes guardrail automated checks  

---

### G11 — Recommendations, self-help, and next session (P1)

**Summary:** PRD bottom sections require actionable next steps: exercises, worksheets, videos, self-help library, therapy booking. POC `GUIDANCE` intent produces generic bullets without a content catalog or booking integration.

**Why it matters**

- Closes the loop on “What should I do next?”  
- Differentiates product from read-only analytics.  
- Requires CMS/integration work beyond ML.

**Recommended solution**

1. **Content catalog** with tags: pillar deficit, risk tier, modality (video, worksheet), contraindications.  
2. **Recommendation rules**: e.g. low Clarity + poor sleep → sleep hygiene resource ID.  
3. Optional: LLM re-ranks top 3 from catalog (never invent new medical advice).  
4. **Next session**: integrate scheduling API; trigger when risk &gt; threshold or user request.

**Acceptance criteria**

- [ ] At least N curated items per pillar theme  
- [ ] Recommendations deterministic for same snapshot (LLM optional polish only)  
- [ ] Booking CTA works for eligible users  

---

### G12 — Composite risk weights undefined (P2)

**Summary:** `composite_risk_percentile` exists in data but formula weights across domains are not documented. PRD driver breakdown (G9) should align with same domain definitions.

**Why it matters**

- Therapist prioritization and Risk Watch may use composite risk.  
- Inconsistent weights between ML training and user-facing drivers erode trust.

**Recommended solution**

1. Document weight vector (e.g. emotional 0.35, behavioral 0.30, physiological 0.20, clinical 0.15).  
2. Version alongside `feature_version`.  
3. Use same domains in G9 attribution.

**Acceptance criteria**

- [ ] Published formula matches production feature computation  
- [ ] Versioned change process documented  

---

### G13 — Visualization / chart layer (P2)

**Summary:** PRD specifies dual-line trends, baseline deviation bars, stress heatmaps, sleep band graphs, mood volatility bands. No chart API or time-series contract exists yet.

**Why it matters**

- Large part of user value is temporal context, not single numbers.  
- Charts need consistent time-series keys from G2 batch history.

**Recommended solution**

1. API: `GET .../engine/trends/{metric}/series?days=30`  
2. Return `{ date, value, baseline, band }` per PRD graph type.  
3. Frontend renders; heatmaps need sub-day stress data (G6).

**Acceptance criteria**

- [ ] Dual-line Recovery vs Stress renders from API data  
- [ ] Charts respect maturity (no fake baseline before day 30)  

---

### G14 — Business ML track outside user Engine PRD (P2)

**Summary:** Business dataset and POC intents (`ORG_ROI_ANALYSIS`, `PRIORITIZATION`) serve orgs and therapists. Engine PRD is end-user focused.

**Why it matters**

- Prevents scope creep on Engine MVP.  
- Still valuable Phase 2 revenue/analytics surface.

**Recommended solution**

- Track as **Phase 2** program; reuse L2 feature store aggregations at program level.  
- Do not block G1–G5 on business models.

**Acceptance criteria**

- [ ] Phase 2 roadmap ticket exists with separate PRD or section  

---

### G15 — `system_type` (web-only vs full) channel handling (P2)

**Summary:** Dataset defines `system_type`: 1 = Normal, 0 = Only web. Web-only users lack wearable fields; same formulas would mislead.

**Why it matters**

- Feature completeness and confidence differ by channel.  
- Cold-start priors may differ for web-only cohort.

**Recommended solution**

1. Registry marks features `requires_wearable: true/false`.  
2. Scoring excludes biological inputs when unavailable; adjust confidence.  
3. Separate cohort priors optional for `system_type = 0`.

**Acceptance criteria**

- [ ] Web-only user never shown HRV-based copy  
- [ ] `data_completeness_score` reflects channel  

---

---

# Part 4 — L2 — Feature registry & computation

## 1. Purpose

Canonical naming and computation rules for all features used by L2 pipelines, L3 scoring, and L4 ML/LLM. **No code** — implementation references this doc.

---

## 2. G3 — Canonical registry (closed)

### 2.1 Rules

- **Single canonical name** per concept; production may alias on ingest.  
- `feature_version`: `feat_v1.0.0` — bump on breaking rename.  
- CI (when coded): export columns ⊆ registry; scoring/ML configs use canonical names only.

### 2.2 Alias map (ingest → canonical)

| Ingest / A4 legacy | Canonical |
|--------------------|-----------|
| `avg_mood_14d` | `mood_avg_14d` |

### 2.3 v1 registry (scoring + POC ML)

| Canonical | Type | Window | Maturity (days) | Used by |
|-----------|------|--------|-----------------|---------|
| `mood_avg_14d` | continuous | 14d | 7 | pillars, trends, L4 |
| `mood_slope_7d` | slope | 7d | 7 | pillars, trends, L4 |
| `mood_volatility_14d` | continuous | 14d | 7 | pillars, trends |
| `mood_delta_30d` | delta | 30d | 30 | L4 optional |
| `motivation_avg_14d` | continuous | 14d | 7 | pillars, trends, L4 |
| `motivation_slope_7d` | slope | 7d | 7 | trends, L4 |
| `confidence_avg_14d` | continuous | 14d | 7 | trends, L4 |
| `confidence_slope_7d` | slope | 7d | 7 | trends, L4 |
| `core_om_wellbeing` | clinical | latest | 0 | pillars |
| `core_om_problems` | clinical | latest | 0 | pillars |
| `core_om_functioning` | clinical | latest | 0 | pillars |
| `core_om_risk` | clinical | latest | 0 | escalation, L4 |
| `core_om_delta_30d` | delta | 30d | 30 | pillars, L4 |
| `gad7_normalized_latest` | clinical | latest | 0 | pillars (v1) |
| `engagement_rate_7d` | rate | 7d | 7 | pillars, trends, ML |
| `engagement_slope_7d` | slope | 7d | 7 | trends, ML |
| `engagement_delta_30d` | delta | 30d | 30 | pillars |
| `therapy_attendance_rate_30d` | rate | 30d | 7 | pillars |
| `sleep_avg_7d` | continuous | 7d | 7 | pillars, trends |
| `sleep_delta_30d` | delta | 30d | 30 | pillars, trends |
| `sleep_slope_7d` | slope | 7d | 7 | pillars, trends |
| `sleep_persistence_low_days` | count | 14d | 7 | pillars, trends |
| `resting_hr_relative` | relative | 7d | 7 | pillars, trends |
| `activity_slope_7d` | slope | 7d | 7 | pillars, trends |
| `cortisol_flag` | flag | 7d | 0 | pillars, trends |
| `withdrawal_flag` | flag | 7d | 7 | L4, patterns |
| `sleep_mood_coupled_decline` | flag | 30d | 30 | L4, patterns |
| `journaling_concern_score_7d` | continuous | 7d | 7 | L4 (add to `emotional_core` group) |
| `data_completeness_score` | meta | — | 0 | L3 confidence |
| `days_active` | meta | — | 0 | L3 maturity |
| `system_type` | meta | — | 0 | L3 G15 |

### 2.4 Out of scope v1 (explicit)

| POC JSON name | Status |
|---------------|--------|
| `phq9_normalized_score` | v1.1 — not on user Engine report (D3) |
| `ptsd_normalized_score` | v1.1 |
| `asrs_partA_normalized` | v1.1 |
| `core_om_normalized_score` | Replaced by subscales (G7) |

---

## 3. G4 — Computation spec (closed)

**Null handling default:** If insufficient events in window → `null` + `{feature}_missing = 1`. L3 imputes per maturity rules.

**Timezone:** User-local calendar day boundaries; store `as_of_date` in UTC with user TZ metadata.

### 3.1 Continuous & slopes

| Feature | Formula | Null if |
|---------|---------|---------|
| `mood_avg_14d` | `mean(mood_daily) over last 14 days` | &lt; 3 mood entries in 14d |
| `mood_slope_7d` | `OLS_slope(mood_daily, 7d)` | &lt; 4 points in 7d |
| `mood_volatility_14d` | `std(mood_daily, 14d)` | &lt; 5 points |
| `motivation_avg_14d` | `mean(motivation_checkin) over 14d` | &lt; 3 check-ins (G8) |
| `motivation_slope_7d` | `OLS_slope(motivation, 7d)` | &lt; 4 points |
| `confidence_avg_14d` | `mean(confidence_checkin) over 14d` | &lt; 3 check-ins |
| `confidence_slope_7d` | `OLS_slope(confidence, 7d)` | &lt; 4 points |
| `sleep_avg_7d` | `mean(sleep_hours) over 7d` | &lt; 3 nights |
| `sleep_delta_30d` | `sleep_avg_7d_now − sleep_avg_7d_baseline_30d` | maturity &lt; 30d |
| `sleep_slope_7d` | `OLS_slope(sleep_hours, 7d)` | &lt; 4 nights |
| `sleep_persistence_low_days` | `count(days sleep_hours < 6 in last 14d)` | — |
| `resting_hr_relative` | `(hr_7d_mean − hr_30d_baseline) / hr_30d_baseline` | maturity &lt; 30d or no wearable |
| `activity_slope_7d` | `OLS_slope(daily_steps_or_active_mins, 7d)` | &lt; 4 days |
| `engagement_rate_7d` | `active_days / 7` (app open or task completed) | — |
| `engagement_slope_7d` | `OLS_slope(daily_engagement_score, 7d)` | &lt; 4 days |
| `engagement_delta_30d` | `engagement_rate_7d − engagement_rate_7d_at_day_-30` | maturity &lt; 30d |
| `therapy_attendance_rate_30d` | `attended / scheduled` in 30d | no sessions scheduled |

### 3.2 Clinical (G7)

| Feature | Formula | Null if |
|---------|---------|---------|
| `core_om_wellbeing` | `normalize(CORE-OM wellbeing subscale)` → 0–1 | no assessment |
| `core_om_problems` | `normalize(CORE-OM problems subscale)` → 0–1 | no assessment |
| `core_om_functioning` | `normalize(CORE-OM functioning subscale)` → 0–1 | no assessment |
| `core_om_risk` | `normalize(CORE-OM risk items)` → 0–1 | no assessment |
| `core_om_delta_30d` | `core_om_total_now − core_om_total_30d_ago` (normalized) | maturity &lt; 30d |
| `gad7_normalized_latest` | `GAD-7 score / max_score` → 0–1 | no GAD-7 in 90d |

### 3.3 Flags

| Feature | Rule |
|---------|------|
| `withdrawal_flag` | `1 if engagement_rate_7d < 0.25 else 0` |
| `sleep_mood_coupled_decline` | `1 if sleep_delta_30d < -1.5 AND mood_slope_7d < -0.3 else 0` |
| `cortisol_flag` | `1 if cortisol_elevation_detected else 0` (wearable or survey proxy) |

### 3.4 G8 — Motivation / confidence source (closed)

| Field | Source | Scale |
|-------|--------|-------|
| `motivation_*` | In-app check-in: “How motivated do you feel?” | 0–5 daily |
| `confidence_*` | In-app check-in: “How confident do you feel?” | 0–5 daily |

**Fallback (cold start only):** If &lt; 3 check-ins, do not impute; trend #6 `available: false`. Optional v1.1 proxy: `0.6 × mood_avg_14d + 0.4 × engagement_rate_7d` with `confidence_tier` capped at Moderate.

### 3.5 Meta

| Feature | Formula |
|---------|---------|
| `data_completeness_score` | `count(populated_scoring_features) / count(required_for_maturity_stage)` |
| `days_active` | `calendar_days since registration` |
| `system_type` | `1` = wearable + app; `0` = web-only |

---

## 4. Acceptance (G3, G4)

- [x] Registry table approved (this doc)  
- [x] All L3 inputs have computation reference  
- [ ] Implementation: CI + backtest (engineering, later)

---

---

# Part 5 — L3 — Scoring service

## 1. Purpose

Layer 3 is the **missing middle** between:

- **L2** — deterministic contextual features (windows, slopes, flags, cohort percentiles)  
- **L1** — fixed PRD dashboard (CRS, four pillars, six trends, driver %, confidence)  
- **L4** — POC intelligence router (intent → ML → LLM)

This POC defines **what L3 must compute**, **how**, and **what it returns** — so engineering can implement without re-deriving product logic from four separate artifacts.

**In scope:** Scoring formulas, normalization rules, cold-start behavior, API contract, batch outputs, sample walkthroughs.  
**Out of scope:** Code, pipelines, databases, chart APIs (G13), content catalog (G11), pattern catalog (G10).

---

## 2. Position in architecture

```
L1 Product Engine (PRD UI)
        ↑  reads daily snapshot
L3 Scoring Service  ← THIS POC
        ↑  reads normalized features
L2 Feature Store (datasets + pipelines)
        ↑
L4 Intelligence Router (uses same scores in LLM context)
```

**Steady-state flow**

1. L2 computes features per user per day.  
2. L3 reads features → outputs scores, trends, drivers, confidence.  
3. Snapshot persisted for L1 (G5 batch — separate POC).  
4. L4 chat/query **must** use the same snapshot values (no divergent LLM numbers).

---

## 3. Outputs (L3 contract)

| Output | Type | Range | Persisted field (proposed) |
|--------|------|-------|----------------------------|
| Cognitive Readiness Score (CRS) | float | 0–100 | `cognitive_readiness_score` |
| Clarity | float | 0–100 | `clarity_score` |
| Emotional Balance | float | 0–100 | `emotional_balance_score` |
| Resilience | float | 0–100 | `resilience_score` |
| Capacity | float | 0–100 | `capacity_score` |
| Six trend composites | float + band | 0–100 + Low/Moderate/High | `trend_{name}_score`, `trend_{name}_band` |
| Driver breakdown | % × 3 domains | sum = 100 | `driver_biological_pct`, etc. |
| Confidence tier | enum | Limited / Moderate / High | `confidence_tier` |
| Metadata | — | — | `score_version`, `computed_at`, `data_maturity_stage` |

**Determinism rule:** Same feature vector + same `score_version` → identical outputs (batch and API).

---

## 4. Inputs

### 4.1 Required meta (from L2)

| Field | Use |
|-------|-----|
| `user_id` | Identity |
| `days_active` | Maturity stage (0–7 / 7–30 / 30+) |
| `data_completeness_score` | Confidence tier |
| `system_type` | 1 = full (wearable); 0 = web-only (G15) |
| `feature_version` | Audit |

### 4.2 Feature inputs

Canonical names per POC JSON and Appendix C of alignment doc. Alias: `avg_mood_14d` → `mood_avg_14d`.

**Pillar & trend features** (minimum v1 set):

| Domain | Features |
|--------|----------|
| Biological | `sleep_avg_7d`, `sleep_delta_30d`, `sleep_slope_7d`, `sleep_persistence_low_days`, `resting_hr_relative`, `cortisol_flag`, `activity_slope_7d` |
| Behavioral | `engagement_rate_7d`, `engagement_slope_7d`, `engagement_delta_30d`, `therapy_attendance_rate_30d`, `withdrawal_flag` |
| Psychological | `mood_avg_14d`, `mood_slope_7d`, `mood_volatility_14d`, `motivation_avg_14d`, `motivation_slope_7d`, `confidence_avg_14d`, `confidence_slope_7d`, `core_om_wellbeing`, `core_om_problems`, `core_om_functioning`, `core_om_delta_30d`, `gad7_normalized_latest` |

**G7 (closed):** `core_om_wellbeing`, `core_om_problems`, `core_om_functioning`, `core_om_risk` required in L2 (see [L2-Feature-Registry-POC.md](#part-4--l2--feature-registry--computation)). Risk subscale feeds escalation/patterns, not CRS directly.

---

## 5. Data maturity & cold start

Aligned with POC three-stage model:

| Stage | `days_active` | Normalization baseline | Confidence cap |
|-------|---------------|------------------------|------------------|
| Cold start | 0–7 | Cohort prior (50) for missing features | **Limited** |
| Early | 7–30 | Mix: available features + cohort prior for gated features | **Moderate** max |
| Full | 30+ | Personal feature values; cohort prior only if null | **High** possible |

**Feature maturity gates:** Features with `maturity_min_days` (e.g. `sleep_delta_30d` = 30) are **excluded** from weighted average until gate met; remaining weights **renormalized** to sum to 1.

**Web-only (`system_type = 0`):** Exclude `requires_wearable` inputs; renormalize pillar/trend weights; never surface HRV-only copy upstream.

**Cohort prior default:** `50` on 0–100 scale (product can tune per cohort later).

---

## 6. Normalization (feature → 0–100)

Each raw feature maps to `normalized_score ∈ [0, 100]` before pillar/trend aggregation.

| Pattern | Applies to | Formula (conceptual) |
|---------|------------|-------------------|
| **Linear scale** | Bounded metrics (mood 0–5, engagement 0–1, sleep hours 4–9) | `100 × clamp((value − min) / (max − min), 0, 1)`; invert if lower is better |
| **Slope / delta centered** | `*_slope_7d`, `*_delta_30d` | `50 + 50 × clamp(value / span, −1, 1)`; invert if negative slope is good (e.g. `core_om_delta_30d` distress) |
| **Flag penalty** | `withdrawal_flag`, `cortisol_flag`, `sleep_mood_coupled_decline` | If active: score = `100 − penalty` (e.g. 25–30); else 100 |
| **Percentile direct** | `*_percentile_cohort` | Use as 0–100 |
| **Clinical inverted** | `core_om_problems`, `gad7_*`, `core_om_normalized_score` | Higher raw distress → lower normalized score |

**Missing value:** If null and maturity allows imputation → cohort prior 50; else exclude from weighted sum and renormalize weights.

---

## 7. Pillar scores (G1)

### 7.1 Generic formula

```
pillar_score = Σ (weight_i × normalized_i) / Σ weight_i   (over available inputs only)
```

All weights below are **within-pillar** (sum = 1.0 per pillar).

### 7.2 Clarity

*PRD intent: sleep, recovery proxy, routine/activity, functioning.*

| Input | Weight | Wearable required |
|-------|--------|-------------------|
| `sleep_avg_7d` | 0.30 | No |
| `sleep_slope_7d` | 0.15 | No |
| `resting_hr_relative` | 0.15 | Yes |
| `activity_slope_7d` | 0.15 | No |
| `core_om_functioning` | 0.25 | No |

### 7.3 Emotional Balance

| Input | Weight |
|-------|--------|
| `core_om_wellbeing` | 0.25 |
| `core_om_problems` | 0.20 |
| `mood_avg_14d` | 0.20 |
| `mood_volatility_14d` | 0.15 |
| `gad7_normalized_latest` | 0.10 |
| `cortisol_flag` | 0.10 |

### 7.4 Resilience

| Input | Weight |
|-------|--------|
| `sleep_persistence_low_days` | 0.20 |
| `sleep_delta_30d` | 0.20 |
| `resting_hr_relative` | 0.15 |
| `mood_slope_7d` | 0.20 |
| `core_om_delta_30d` | 0.15 |
| `therapy_attendance_rate_30d` | 0.10 |

### 7.5 Capacity

| Input | Weight |
|-------|--------|
| `sleep_avg_7d` | 0.20 |
| `engagement_rate_7d` | 0.20 |
| `activity_slope_7d` | 0.15 |
| `core_om_functioning` | 0.20 |
| `motivation_avg_14d` | 0.15 |
| `engagement_delta_30d` | 0.10 |

### 7.6 Cognitive Readiness Score (CRS)

**D2 closed:** equal blend (clinical weighting deferred to v1.1 if needed).

```
CRS = 0.25 × Clarity + 0.25 × Emotional_Balance + 0.25 × Resilience + 0.25 × Capacity
```

`score_version`: `crs_v1.0.0` — bump on weight or pillar input changes.

---

## 8. Six trend composites (G2)

Each trend = weighted normalized inputs → `trend_score` 0–100 → band label.

| Band | Score range |
|------|-------------|
| Low | 0–33 |
| Moderate | 34–66 |
| High | 67–100 |

PRD card copy maps to band + direction (improving/stable/declining) using 7d delta of `trend_score` (stored in history table when G5 batch exists).

### 8.1 Recovery Readiness

| Input | Weight | Notes |
|-------|--------|-------|
| `sleep_delta_30d` | 0.35 | Requires 30d maturity |
| `sleep_avg_7d` | 0.30 | |
| `resting_hr_relative` | 0.20 | Wearable; proxy if missing (G6 Option B) |
| `sleep_persistence_low_days` | 0.15 | Inverted (fewer low days = better) |

**D1/G6 closed (proxy v1):** If `system_type = 0` or HR null → drop `resting_hr_relative`; renormalize remaining weights (×1.25). Card shows footnote: “Based on sleep and mood signals.”

| Input (proxy mode) | Weight |
|--------------------|--------|
| `sleep_delta_30d` | 0.45 |
| `sleep_avg_7d` | 0.35 |
| `sleep_persistence_low_days` | 0.20 |

### 8.2 Stress Load

**D1 closed:** Stress is a **load index** 0–100 where **higher = more stress** (aligns with PRD “Stress Load: High”).

| Input | Weight |
|-------|--------|
| `cortisol_flag` | 0.40 |
| `resting_hr_relative` | 0.35 |
| `mood_volatility_14d` | 0.25 |

**Formula:**

```
stress_raw = weighted normalized inputs (flags/HR/volatility; higher raw = worse)
stress_load_score = stress_raw   # already oriented: high = high load
band = Low (0-33) | Moderate (34-66) | High (67-100) on stress_load_score
```

**Proxy v1 (no HR):** Weights → cortisol 0.55, volatility 0.45. Hide if both null.

### 8.3 Sleep Consistency

| Input | Weight |
|-------|--------|
| `sleep_avg_7d` | 0.40 |
| `sleep_persistence_low_days` | 0.35 |
| `sleep_slope_7d` | 0.25 |

### 8.4 Energy Rhythm

| Input | Weight |
|-------|--------|
| `activity_slope_7d` | 0.45 |
| `engagement_rate_7d` | 0.35 |
| `engagement_slope_7d` | 0.20 |

### 8.5 Emotional Stability

| Input | Weight |
|-------|--------|
| `mood_volatility_14d` | 0.45 |
| `mood_slope_7d` | 0.35 |
| `mood_avg_14d` | 0.20 |

*Mostly computable from existing L2 features — first trend to validate in pilot.*

### 8.6 Motivation & Confidence Momentum

| Input | Weight |
|-------|--------|
| `motivation_avg_14d` | 0.25 |
| `motivation_slope_7d` | 0.25 |
| `confidence_avg_14d` | 0.25 |
| `confidence_slope_7d` | 0.25 |

**G8 closed:** Source = daily check-ins (see L2 doc). If &lt; 3 check-ins in 14d → `available: false`, message: “Complete a few check-ins to unlock this trend.”

### 8.7 Trend availability

```json
{
  "trend_id": "emotional_stability",
  "score": 58,
  "band": "Moderate",
  "available": true,
  "direction_7d": "improving"
}
```

---

## 9. Driver breakdown (G9)

**Purpose:** PRD “Biological 42% | Behavioral 31% | Psychological 27%” — influence attribution, not causal medical claim.

### 9.1 Rule-based approach (POC default)

1. Tag each pillar’s inputs by domain (bio / behavioral / psychological) — see §7 tables.  
2. Compute **pillar-level domain contribution**:

```
domain_share[d] = Σ over pillars p: (crs_weight_p × pillar_p_score × pillar_domain_fraction[p][d])
```

3. Normalize to 100%:

```
driver_biological_pct = round(100 × domain_share[biological] / sum(domain_share))
```

**Pillar → domain fractions (for attribution blend):**

| Pillar | Biological | Behavioral | Psychological |
|--------|------------|------------|---------------|
| Clarity | 0.60 | 0.25 | 0.15 |
| Emotional Balance | 0.10 | 0.10 | 0.80 |
| Resilience | 0.35 | 0.25 | 0.40 |
| Capacity | 0.20 | 0.45 | 0.35 |

### 9.2 Visibility rules (D5 closed)

- `drivers_visible = false` if `confidence_tier = Limited` OR `days_active < 7`.  
- Copy template: “Your readiness **may be influenced by** biological (X%), behavioral (Y%), and psychological (Z%) factors.”

### 9.3 G12 — Composite risk domain weights (closed)

Used for `composite_risk_percentile` and aligned with driver domains:

| Domain | Weight |
|--------|--------|
| Psychological (emotional) | 0.35 |
| Behavioral | 0.30 |
| Physiological (biological) | 0.20 |
| Clinical (CORE-OM risk, assessments) | 0.15 |

`risk_version`: `risk_v1.0.0`

---

## 10. Confidence tier

| Tier | Conditions (any triggers Limited) |
|------|-----------------------------------|
| **Limited** | `days_active ≤ 7` OR `data_completeness_score < 0.4` |
| **Moderate** | `days_active ≤ 30` OR `data_completeness_score < 0.7` (and not Limited) |
| **High** | `days_active > 30` AND `data_completeness_score ≥ 0.7` |

Expose in L1 as “Confidence in insight: Limited / Moderate / High” per PRD.

---

## 11. Integration points

### 11.1 L2 → L3

- Input: single row per user per `as_of_date` from feature store.  
- Pre-check: resolve aliases; validate required meta present.

### 11.3 L3 → L1 (via G5 snapshot)

Snapshot row includes all §3 outputs + `score_version` + `as_of_date`. L1 never recomputes CRS.

### 11.4 L3 → L4 (LLM context)

Inject into STATUS_CHECK / TREND_ANALYSIS templates:

```
cognitive_readiness_score: 72
clarity_score: 68
emotional_balance_score: 74
...
trend_recovery_readiness_band: Moderate
driver_biological_pct: 42
confidence_tier: Moderate
```

LLM **must not** invent different numbers.

---

## 12. Sample walkthrough (paper POC)

**User:** `days_active = 45`, `system_type = 1`, `data_completeness_score = 0.82`

| Feature | Raw | Normalized (illustrative) |
|---------|-----|---------------------------|
| `mood_avg_14d` | 3.8 | 76 |
| `sleep_avg_7d` | 7.2 h | 64 |
| `engagement_rate_7d` | 0.72 | 72 |
| `core_om_functioning` | 0.7 | 70 |
| `cortisol_flag` | 0 | 100 |
| `mood_volatility_14d` | 0.4 | 80 |

**Pillar (approximate):**

- Clarity ≈ 68  
- Emotional Balance ≈ 74  
- Resilience ≈ 71  
- Capacity ≈ 70  

**CRS** ≈ `0.25 × (68+74+71+70)` = **70.75 → 71**

**Trends (examples):**

- Emotional Stability ≈ 62 → **Moderate**  
- Stress Load (inverted) ≈ **Low** band on load scale  
- Motivation & Confidence Momentum → **available** if G8 features present  

**Drivers (illustrative):** Biological 38% | Behavioral 34% | Psychological 28%

**Confidence:** **High**

---

## 13. Gap closure checklist

| ID | Status | Spec |
|----|--------|------|
| G1 | **Closed** | §7 |
| G2 | **Closed** | §8 |
| G6 | **Closed** (proxy v1) | §5, §8.1–8.2 |
| G7 | **Closed** | §4.2, §7; L2 doc |
| G8 | **Closed** | §8.6; L2 doc |
| G9 | **Closed** | §9 |
| G12 | **Closed** | §9.3 |
| G15 | **Closed** | §5 |

Implementation checkboxes (engineering, later): unit tests, API, batch wiring per [L1-Engine-Snapshot-POC.md](#part-6--l1--engine-snapshot--batch-api).

---

## 14. Closed product decisions (record)

| ID | Decision | Resolution |
|----|----------|------------|
| D1 | Wearables v1 | Phased: proxy v1 (sleep/HR/mood); full wearable v1.1 |
| D2 | CRS formula | Equal 25% per pillar |
| D3 | Clinical on report | CORE-OM subscales + GAD-7 in pillars |
| D4 | Cohort percentiles | Therapist-only on end-user Engine |
| D5 | Driver visibility | Hidden when Limited or &lt; 7 days |
| D6 | Recommendations | Rules-first; see L1 Patterns doc |

---

## 15. What engineering builds later

1. Scoring service module + `score_version` config loading  
2. Unit tests per §13  
3. Batch job writing `user_engine_snapshot` (G5)  
4. Registry CI check (G3)  
5. Full feature computation spec (G4) in L2  

---

## 16. Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-05-20 | Initial L3 POC spec |
| 2.0 | 2026-05-20 | All L3 gaps and D1–D6 decisions closed; G12 weights; proxy biological v1 |

---

*L3 POC specification is **complete**. See [POC-Documentation-Index.md](#) for full package.*

---

# Part 6 — L1 — Engine snapshot & batch API

## 1. Purpose

PRD Engine is **always-on** — not query-only. This POC defines the **batch snapshot** and **read API contract** connecting L2 → L3 → L1. L4 chat reads the same snapshot.

---

## 2. G5 — Batch pipeline (closed)

### 2.1 Schedule

| Job | Cadence | Trigger |
|-----|---------|---------|
| `engine_daily_snapshot` | Daily 02:00 user-local | Cron |
| `engine_on_demand_refresh` | Event-driven | New assessment, wearable sync, therapy session |

### 2.2 Pipeline steps

```
1. L2: compute / load feature row for user_id + as_of_date
2. L3: ScoringService.compute(features) → scores, trends, drivers, confidence
3. L1: PatternEngine.select(snapshot) → pattern_cards[] (max 4)
4. L1: RecommendationEngine.select(snapshot) → recommendations[] (top 3)
5. Persist user_engine_snapshot
```

### 2.3 Table: `user_engine_snapshot`

| Column | Type | Source |
|--------|------|--------|
| `user_id` | string | — |
| `as_of_date` | date | — |
| `computed_at` | timestamp | — |
| `score_version` | string | L3 |
| `feature_version` | string | L2 |
| `data_maturity_stage` | enum | cold_start / early / full |
| `cognitive_readiness_score` | float | L3 |
| `clarity_score` | float | L3 |
| `emotional_balance_score` | float | L3 |
| `resilience_score` | float | L3 |
| `capacity_score` | float | L3 |
| `confidence_tier` | enum | L3 |
| `driver_biological_pct` | int | L3 |
| `driver_behavioral_pct` | int | L3 |
| `driver_psychological_pct` | int | L3 |
| `drivers_visible` | bool | L3 rules |
| `trends_json` | JSON | six trends §2.4 |
| `pattern_cards_json` | JSON | G10 |
| `recommendations_json` | JSON | G11 |
| `snapshot_stale` | bool | job health |

### 2.4 `trends_json` shape

```json
{
  "recovery_readiness": { "score": 64, "band": "Moderate", "available": true, "direction_7d": "stable" },
  "stress_load": { "score": 28, "band": "Low", "available": true, "direction_7d": "improving" },
  "sleep_consistency": { "score": 71, "band": "High", "available": true, "direction_7d": "improving" },
  "energy_rhythm": { "score": 55, "band": "Moderate", "available": true, "direction_7d": "declining" },
  "emotional_stability": { "score": 62, "band": "Moderate", "available": true, "direction_7d": "improving" },
  "motivation_confidence_momentum": { "score": null, "band": null, "available": false, "message": "Complete a few check-ins to unlock this trend." }
}
```

### 2.5 History table: `user_trend_history`

| Column | Purpose |
|--------|---------|
| `user_id`, `trend_id`, `as_of_date`, `score` | 14–30d series for charts (G13) |

Populated by same batch job from L3 outputs.

### 2.6 Read API

```
GET /v1/users/{user_id}/engine/report?date=YYYY-MM-DD
```

**Response:** Full snapshot row + `last_updated`, `confidence_tier`.  
**SLO:** p95 &lt; 200ms server-side (cached read).

### 2.7 L4 consistency rule

`handle_query` loads snapshot for `user_id` + today; LLM prompt includes CRS/pillars/trends from snapshot — **never recomputes scores**.

### 2.8 Failure behavior

| Condition | UX |
|-----------|-----|
| Batch failed | `snapshot_stale=true`; show last good snapshot + “Last updated {computed_at}” |
| No snapshot ever | Empty state + onboarding cold-start copy |

---

## 3. G13 — Chart time-series API (closed)

```
GET /v1/users/{user_id}/engine/trends/{trend_id}/series?days=30
```

**Response:**

```json
{
  "trend_id": "emotional_stability",
  "points": [
    { "date": "2026-05-01", "value": 58, "baseline": 55, "band": "Moderate" }
  ],
  "maturity_sufficient": true
}
```

| PRD chart | `trend_id` | Notes |
|-----------|------------|-------|
| Dual-line recovery vs stress | `recovery_readiness` + `stress_load` | Two series calls or combined endpoint |
| Sleep band graph | `sleep_consistency` | `baseline` = 30d mean |
| Mood volatility band | `emotional_stability` | — |
| Stress heatmap | — | **Deferred v1.1** — requires sub-day stress (G6 phased) |

**Rule:** If `days_active < 30`, `baseline` null; frontend shows partial chart per PRD.

---

## 4. Acceptance (G5, G13)

- [x] Batch steps and schema defined  
- [x] Read API and trend series contract defined  
- [ ] Implementation: job + cache + alerts (engineering, later)

---

---

# Part 7 — L1 — Patterns & actions

# L1 — Patterns & Actions POC (Specification Only)

**Version:** 1.0 · **Date:** May 20, 2026  
**Closes:** G10, G11  
**Parent:** [PRD-POC-Alignment-and-Gaps.md](#part-2--gaps-and-decisions)

---

## 1. G10 — Pattern module (closed)

### 1.1 Principles

- **Deterministic rules** on snapshot features/scores — LLM only writes copy from template.  
- **Max 4** active cards; rotate; no duplicate `pattern_id` within 7 days.

### 1.2 Pattern catalog v1

| pattern_id | PRD type | Rule (evaluate on snapshot) | Priority | min maturity |
|------------|----------|----------------------------|----------|--------------|
| `corr_sleep_mood` | correlation | `sleep_mood_coupled_decline == 1` | 90 | early |
| `warn_withdrawal` | warning | `withdrawal_flag == 1` | 95 | early |
| `warn_regression` | warning | `label_regression_30d_prob >= 0.6` (ML) | 88 | early |
| `drift_mood_down` | drift | `mood_slope_7d < -0.2` for 14d | 70 | full |
| `positive_sleep_up` | positive | `sleep_slope_7d > 0.1` AND `mood_volatility_14d` improving | 60 | early |
| `recovery_engagement` | recovery | `engagement_slope_7d > 0.1` AND `crs` up 5+ pts vs 7d ago | 65 | full |
| `time_weekend_dip` | time-based | `weekend_mood_delta < -0.5` (v1.1 feature) | 50 | full |

**v1 ships:** first five rows; `time_weekend_dip` deferred.

### 1.3 `pattern_cards_json` shape

```json
[
  {
    "pattern_id": "corr_sleep_mood",
    "type": "correlation",
    "title": "Sleep and mood are moving together",
    "severity": "watch",
    "template_id": "pattern_correlation_v1",
    "expires_at": "2026-05-27"
  }
]
```

### 1.4 Module mapping

| PRD module | Source patterns |
|------------|-----------------|
| Pattern Spotlight | top 2 by priority (non-warning) |
| Risk Watch | `warn_*` types |
| Improvement Signal | `positive_*`, `recovery_*` |

---

## 2. G11 — Recommendations & actions (closed)

### 2.1 Principles (D6 closed)

- **Rules-first:** deterministic mapping snapshot → content IDs.  
- **LLM optional:** re-rank or polish wording from catalog only — never invent medical advice.

### 2.2 Content catalog (minimum v1)

| content_id | Type | Tags | Trigger rule |
|------------|------|------|--------------|
| `sleep_hygiene_101` | article | clarity, sleep | `clarity_score < 50` OR `sleep_avg_7d < 6` |
| `breathing_exercise_5m` | exercise | emotional_balance, stress | `stress_load band = High` |
| `engagement_reengage` | worksheet | capacity, behavioral | `withdrawal_flag == 1` |
| `therapy_booking_cta` | action | session | `core_om_risk > 0.7` OR user tap |
| `mood_checkin_reminder` | in-app | motivation | trend #6 `available: false` |

**Minimum:** 3 items per pillar theme (12+ total) — content team owns copy.

### 2.3 `recommendations_json` shape

```json
[
  { "content_id": "sleep_hygiene_101", "reason": "low_clarity_sleep", "rank": 1 },
  { "content_id": "breathing_exercise_5m", "reason": "elevated_stress", "rank": 2 }
]
```

### 2.4 Next session

- Trigger: `therapy_booking_cta` when `therapy_attendance_rate_30d < 0.5` OR risk subscale high.  
- Integrate scheduling API in implementation phase.

---

## 3. Acceptance (G10, G11)

- [x] Pattern types and rules defined  
- [x] Rotation and module mapping defined  
- [x] Recommendation rules + catalog schema defined  
- [ ] Implementation: engines + CMS (engineering, later)

---

*End — L1 Patterns & Actions POC*


---

# Part 8 — Dataset columns & validation

## Which file are you checking?

| Dataset | Expected row grain | Column count (v1) |
|---------|-------------------|-------------------|
| **User feature export (L2)** | 1 row per `user_id` + `as_of_date` | 34 feature/meta columns (see §1) |
| **Engine snapshot (L1 output)** | 1 row per user per day **after** batch | 20 columns (see §2) — usually **not** in ML export today |
| **Trend history (G13)** | 1 row per user + `trend_id` + date | 6 columns (see §3) |

Most teams validate the **L2 feature export** first.

---

## §1 — L2 user feature row — required columns (v1)

### 1A. Identity & meta (required)

| Column | Required | If missing |
|--------|----------|------------|
| `user_id` | **Yes** | Blocker |
| `as_of_date` | **Yes** | Blocker |
| `days_active` | **Yes** | Add or derive from registration |
| `system_type` | **Yes** | Add (1=full, 0=web-only) |
| `data_completeness_score` | **Yes** | Compute per L2 POC |
| `feature_version` | **Yes** | Set constant `feat_v1.0.0` |

### 1B. Rename (legacy A4 → canonical)

| Your column may be | Must be named |
|--------------------|---------------|
| `avg_mood_14d` | `mood_avg_14d` |

### 1C. Psychological / clinical (required for v1 scoring)

| Column | Required | Notes |
|--------|----------|-------|
| `mood_avg_14d` | **Yes** | |
| `mood_slope_7d` | **Yes** | |
| `mood_volatility_14d` | **Yes** | |
| `core_om_wellbeing` | **Yes** | **Often missing** in old A4 — add |
| `core_om_problems` | **Yes** | **Often missing** — add |
| `core_om_functioning` | **Yes** | **Often missing** — add |
| `core_om_risk` | **Yes** | For risk / patterns |
| `core_om_delta_30d` | **Yes** | Likely already present |
| `gad7_normalized_latest` | **Yes** | Per D3 |
| `motivation_avg_14d` | **Yes** | **Often missing** — add (G8) |
| `motivation_slope_7d` | **Yes** | |
| `confidence_avg_14d` | **Yes** | |
| `confidence_slope_7d` | **Yes** | |

### 1D. Behavioral (required)

| Column | Required |
|--------|----------|
| `engagement_rate_7d` | **Yes** |
| `engagement_slope_7d` | **Yes** |
| `engagement_delta_30d` | Yes (null until 30d maturity) |
| `therapy_attendance_rate_30d` | **Yes** |
| `withdrawal_flag` | **Yes** |

### 1E. Biological (required for proxy v1)

| Column | Required |
|--------|----------|
| `sleep_avg_7d` | **Yes** |
| `sleep_delta_30d` | Yes (null until 30d) |
| `sleep_slope_7d` | **Yes** |
| `sleep_persistence_low_days` | **Yes** |
| `resting_hr_relative` | Yes (null web-only / no wearable) |
| `activity_slope_7d` | **Yes** |
| `cortisol_flag` | **Yes** |
| `sleep_mood_coupled_decline` | **Yes** |

### 1F. Optional but recommended

| Column | Used for |
|--------|----------|
| `mood_delta_30d` | L4 ML / intents |
| `journaling_concern_score_7d` | L4 (may already be in A4) |
| `composite_risk_percentile` | G12 / therapist views |
| `sleep_percentile_cohort` | Cold start / therapist (not end-user CRS) |
| `engagement_percentile_cohort` | Same |
| `weeks_in_program` | Legacy; prefer `days_active` |

### 1G. Not required on L2 for v1 Engine (OK if absent)

`phq9_*`, `ptsd_*`, `asrs_*`, `core_om_normalized_score`, HRV, REM%, stress_episode_*, `clarity_score`, `crs` (scores come from L3 snapshot, not input ML row).

---

## §2 — `user_engine_snapshot` (outputs — after L3 batch)

Not expected in your current ML CSV unless you already run batch. Required **after** implementation:

`user_id`, `as_of_date`, `computed_at`, `score_version`, `feature_version`, `data_maturity_stage`,  
`cognitive_readiness_score`, `clarity_score`, `emotional_balance_score`, `resilience_score`, `capacity_score`,  
`confidence_tier`, `driver_biological_pct`, `driver_behavioral_pct`, `driver_psychological_pct`, `drivers_visible`,  
`trends_json`, `pattern_cards_json`, `recommendations_json`, `snapshot_stale`

---

## §3 — `user_trend_history` (charts)

`user_id`, `trend_id`, `as_of_date`, `score`, `band`, `baseline`

---

## §4 — Quick pass/fail for thousands of records

| Check | Pass criteria |
|-------|----------------|
| Column names | All §1A–1E present or aliased (`avg_mood_14d` → `mood_avg_14d`) |
| Row grain | One row per user per date (or per user if single latest snapshot) |
| `user_id` | No nulls |
| `days_active` | ≥ 0; varies across users |
| Maturity | Some users with `days_active` &lt; 7, 7–30, 30+ |
| `system_type` | Values 0 and 1 if you have web + wearable users |
| G8 columns | Non-null for users with check-in history |
| G7 columns | Non-null after CORE-OM assessment |
| Volume | Thousands of rows is **fine** for production (not a gap) |

---

## §5 — Column count summary

| Set | Count |
|-----|-------|
| L2 v1 canonical (sample Excel) | **34** |
| Engine snapshot | **20** |
| Trend history | **6** |

---

*Match this checklist to `User_Feature_Row_Sample` in Engine-POC-Sample-Dataset.xlsx.*

---

# Part 9 — Roadmap and appendices

## 12. Implementation roadmap

| Phase | Goal | Delivers | Resolves gaps | Depends on |
|-------|------|----------|---------------|------------|
| **0** | POC documentation | D1–D6 + G1–G15 specs | **Done** | POC index |
| **1** | Feature pipeline | Registry + computation in code | G3, G4 | [L2 POC](#part-4--l2--feature-registry--computation) |
| **2** | Scoring service | CRS, pillars, six trends, drivers | G1, G2, G9, G12, G15 | [L3 POC](#part-5--l3--scoring-service) |
| **3** | Report API | Batch snapshot + read API | G5 | [L1 Snapshot POC](#part-6--l1--engine-snapshot--batch-api) |
| **4** | Intelligence UX | Patterns + LLM narratives | G10 | [L1 Patterns POC](#part-7--l1--patterns--actions) |
| **5** | ML production | Risk models wired to snapshot | — | Phase 1 |
| **6** | Actions | Content catalog + booking | G11 | Phase 3–4 |
| **7** | Charts | Trend series + frontend | G13 | Phase 3 |
| **8** | Phase 2 org | Business ML surfaces | G14 | Out of Engine MVP |

---

## 13. Document maintenance

| Event | Action |
|-------|--------|
| Feature registry approved | Update §7, §9 G3, Appendix C |
| Scoring weights approved | Add Appendix D; close G1/G12 items |
| Product scope cut (wearables) | Update G6, D1 log |
| Gap closed | Mark acceptance criteria checked; note version |
| New artifact added | Add to §3; re-run alignment |

**Ownership:** Program lead maintains this file; technical leads propose edits via PR.

---

## 14. Appendices

### Appendix A — File inventory

```
mp_ai/
├── Engine Document.docx
├── Contextuliazation.xlsx
├── Data contexualization extended.docx
├── Data contexualization Datasets.xlsx
├── PRD-POC-Alignment-and-Gaps.md       ← this document
├── POC-Documentation-Index.md          ← start here
├── L2-Feature-Registry-POC.md
├── L3-Scoring-Service-POC.md
├── L1-Engine-Snapshot-POC.md
├── L1-Patterns-and-Actions-POC.md
├── Engine-POC-Sample-Dataset.xlsx   ← sample L2 + snapshot + history
└── poc_extract.txt
```

### Appendix B — Gap → PRD section index

| Gap | PRD area |
|-----|----------|
| G1 | §3 Output Scores |
| G2 | Biological / Behavioral / Psychological Trends |
| G5 | Entire report (implicit) |
| G6 | §2.1 Biological Inputs |
| G7 | §2.3 Assessment Inputs |
| G10 | Emerging Patterns, Pattern Spotlight, Risk Watch |
| G11 | What to do next, Tools, Self-Help, Next Session |
| G13 | Best graphs sections |

### Appendix C — Canonical feature naming (v1 proposal)

| Canonical | Dataset today | POC JSON |
|-----------|---------------|----------|
| `mood_avg_14d` | `avg_mood_14d` | `mood_avg_14d` |
| `motivation_avg_14d` | *add* | `motivation_avg_14d` |
| `confidence_avg_14d` | *add* | `confidence_avg_14d` |
| `core_om_normalized_score` | *add* | `core_om_normalized_score` |
| `core_om_wellbeing` | *add* | *add* |
| `core_om_functioning` | *add* | *add* |

### Appendix D — Scoring formulas (closed — see L3 POC)

**CRS (D2 closed):**

```
CRS = 0.25×Clarity + 0.25×EmotionalBalance + 0.25×Resilience + 0.25×Capacity
score_version: crs_v1.0.0
```

**Per-pillar weights:** Full tables in [L3-Scoring-Service-POC.md](#part-5--l3--scoring-service) §7–8.

**Composite risk (G12 closed):** emotional 0.35, behavioral 0.30, physiological 0.20, clinical 0.15 (`risk_v1.0.0`).

---

## 9.1 Implementation order (quick reference)

## Implementation order (when coding)

1. L2 registry + feature pipeline (L2 doc)  
2. L3 scoring service (L3 doc)  
3. L1 batch snapshot + read API (L1 Snapshot doc)  
4. L1 patterns + recommendations (L1 Patterns doc)  
5. Wire L4 to snapshot context  

---

## 9.2 Related files (repository)

```
mp_ai/
├── ENGINE-POC-COMPLETE-DOCUMENTATION.md  ← this file
├── Engine-POC-Sample-Dataset.xlsx
├── poc_extract.txt
├── scripts/validate_dataset_columns.py
├── scripts/generate_sample_dataset.py
└── (legacy split .md files — deprecated, see top of each)
```

---

*End of consolidated documentation — version 3.0*
