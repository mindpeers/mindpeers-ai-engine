# MindPeers Cognitive Readiness Engine — Stakeholder Roadmap

**Audience:** Product, Clinical, Leadership, Design, Operations  
**Version:** 1.5.0  
**Date:** 2026-06-24  
**Program kickoff:** 24 June 2026  
**Technical companion:** [Development-Roadmap.md](./Development-Roadmap.md) · [Engine-Part1-Full-Stack-Development-Roadmap.md](./Engine-Part1-Full-Stack-Development-Roadmap.md) (backend + frontend + engine — **complete Part1**)

---

## Complete Part1 (backend + frontend + engine)

If you need **everything** — all screens, app APIs, mobile/web UI, and the scoring engine:

| Stack | What | Team |
|-------|------|--------------------------|
| **Data & scoring engine** | Ingestion, ML, CRS, report API | 2 engineers 1 AI/ML Engineer |
| **Platform backend** | Check-in, forms, games, therapy, event gateway | 2 engineers |
| **Frontend** | Mobile + web — all Part1 screens + report dashboard | 1 engineer |
| **Design + QA** | Figma, E2E tests | 2-3 people |
| **Total** | **Complete Part1** | **~6-7 people** |

| Deadline | Feasible? |
|----------|-----------|
| **2 months** | **Yes** — Engine Part 1 |


---

## 2-month program (all phases)

**Kickoff:** 24 June 2026

If leadership requires **full launch + all 70 data inputs in ~2.5 months**:

| Item | Requirement |
|------|-------------|
| **Team** | **4 engineers** (6 h/day, 5 days/week) |
| **Week 8 (~15 Aug)** | Public launch with core inputs (~26%) |
| **Week 8–10** | **100% Part1 inputs** live (parallel enrichment) |
| **Key condition** | Phase 5 expansion runs **in parallel from week 2** (1 July) — not after launch |

---

## Resource distribution

**Working assumption:** Each engineer works **6 hours/day**, **5 days/week** (= **30 hours/week**).

---

### 2-months plan (4 engineers)

Two squads run **at the same time** from week 3:

#### Core squad (3-4 people) — builds launch path

| Role | Count | Responsibility | Weeks active |
|------|-------|----------------|--------------|
| **Engineering lead** | 1 | Program integration, launch, scoring orchestration | 1–9 |
| **Backend engineer** | 2 | Scores, report API, five questions, warnings | 1–9 |
| **Data engineer (platform)** | 1 | Core data pipes, daily rollups, feature pipeline | 1–9 |
| **ML engineer** | 1 | Outcome labels, 4 prediction models, final model update (week 5) | 5–9 |
| **DevOps** | 0.5–1 | Infrastructure, batch jobs, production monitoring | 9 |

#### Expansion squad (3–4 people) — connects remaining inputs in parallel

| Role | Count | Responsibility | Weeks active |
|------|-------|----------------|--------------|
| **Data engineer (inputs A + C)** | 1 | Lifestyle check-ins, brain games, extra assessments, Intake forms, lab results, therapist matching sheet  | 3–8 |
| **Backend / NLP engineer** | 2 | Journal sentiment, app behaviour signals | 3-8 |
| **QA / data analyst** (recommended) | 1 | Score checks, regression tests, sign-off evidence | 8-9 |

---

### Non-engineering resources

These roles are **not** counted in engineering headcount but are **required** for gates:

| Role | Typical commitment | Critical weeks |
|------|-------------------|--------------|
| **Clinical lead** | 4–8 h/week | 1, 4, 8 (sign-offs) |
| **Product manager** | 6–10 h/week | 1, 4, 8 (copy, launch) |
| **Design** | 4–8 h/week | 9–11 (report UI consuming API) |
| **Mobile / app team** | Separate squad | Must emit new event types per Phase 5 schedule |
| **Operations / support** | Ramp at launch | 10+ (runbooks, “why did my score change?”) |

---

### Hiring / allocation checklist (4-month plan)

- [ ] **3 engineers committed full program** (not 50% shared with other products)
- [ ] **1 ML+data engineer** minimum on expansion squad from week 3. Intern can be utilized.
- [ ] **1 ML+data engineer** dedicated from week 1 (ramp) / week 5 (full labels). Intern can be unitilized.
- [ ] **App team** aligned to ship lifestyle, forms, and game events by weeks 5–8
- [ ] **Clinical gates** booked in advance (weeks 1, 4, 8)
- [ ] **Float buffer:** hold 1 engineer unallocated weeks 5–8 for slip recovery (ideal)


---

## In one sentence

We are building a **daily mental-health readiness report** that tells each user **where they are today**, **where they are heading**, and **what to do next** — grounded in their real app activity, assessments, sleep, and therapy data.

---

## What the user will see

When complete, the MindPeers report answers five questions:

| Question | What it means for the user |
|----------|---------------------------|
| **Where am I now?** | Overall readiness score + four dimension scores (Clarity, Emotional Balance, Resilience, Capacity) |
| **Where am I heading?** | Seven trend arrows (e.g. sleep improving, motivation declining) |
| **Why is it like this?** | Plain-language explanation of what’s driving the scores |
| **What should I be aware of?** | Early warnings (e.g. “motivation has dropped this week”) |
| **What should I do next?** | Suggested actions (check-in, sleep tips, contact therapist) |

### The dashboard (simplified)

```
┌─────────────────────────────────────────────────────────────┐
│  TODAY (How you are now)      │  DIRECTION (Where you're    │
│                               │  heading)                   │
├───────────────────────────────┼─────────────────────────────┤
│  Readiness Score ....... 81   │  Recovery .............. ↑  │
│  Clarity ............... 78   │  Stress ................ ↓  │
│  Emotional Balance ..... 72   │  Sleep regularity ...... ↑  │
│  Resilience ............ 80   │  Energy ................ →  │
│  Capacity .............. 74   │  Emotional stability ... ↑  │
│                               │  Motivation ............ ↓  │
│                               │  Mental sharpness ...... ↑  │
└───────────────────────────────┴─────────────────────────────┘
```

Scores update **once per day** (overnight). The app reads the latest report — it does not recalculate on every screen tap.

---

## Two readiness scores (important to understand)

We use **two complementary scores** during rollout. They answer slightly different questions.

| Score | Plain meaning | When it’s the headline |
|-------|---------------|------------------------|
| **Same-day readiness** | “Based on what we know about you *right now*” — built from assessments, check-ins, sleep, engagement | New users; users with limited data; always available as backup |
| **Trajectory readiness (CRS v2)** | “Based on patterns that predict recovery, dropout, and relapse” — uses prediction models | Main headline for established users after launch |

**During weeks 9–10** we show both internally to validate they make sense together. **After launch**, trajectory readiness becomes the main number for most users; same-day readiness stays visible for transparency.

---

## Safety first

| Rule | What it means |
|------|----------------|
| **Risk cap** | If clinical risk indicators are high (CORE-OM risk), **all displayed scores are capped** and the report switches to supportive escalation messaging |
| **No diagnosis** | Copy uses probabilistic language (“may”, “suggests”) — never “you have depression” |
| **Human escalation** | High-risk users are directed toward therapist / support — not only an in-app score |

Clinical team signs off on risk thresholds before we go live.

---

## Clinical team sign-off checklist

Use this checklist at each gate. **Signatory:** Clinical lead (or delegate). **Reference:** [CRS Unified v3 §4.3 & Appendix B.1](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md#appendix-b1--clinical-label-decision-tree-for-sign-off).

### How to use

| Gate | Target week | Dates (2026) | Outcome |
|------|-------------|--------------|---------|
| **G1 — Pre-build** | 1 | 24–30 Jun | Build may start |
| **G2 — Risk cap QA** | 4 | ~21 Jul | Staging scores approved |
| **G3 — ML labels** | 6 | ~4 Aug | Models may train |
| **G4 — Narrative & shadow** | 7 | 5–14 Aug | Report copy approved |
| **G5 — Launch** | 8 | from 15 Aug | Production go-live |
| **G6 — Full inputs** | 8–10 | Jul–Aug | Baseline & window sign-off (70/70) |

---

### Clinical sign-off — MCID & label thresholds (G1 / G3)

**Signatory:** Clinical lead · **Label version:** `label_v2.0.0` · **Reference:** [CRS Unified v3 §4.3.3](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md#433-configuration-constants-clinical-sign-off-required), [Appendix B.1](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md#appendix-b1--clinical-label-decision-tree-for-sign-off)

Only **validated assessment outcomes** and **program label constants** require MCID sign-off. Confirm each **Value** or record an override below.

| Attribute | MCID | Value |
|-----------|------|-------|
| **A01** CORE-OM overall score | `CORE_OM_MCID_TOTAL` | **5** raw points (R1 improvement / L1 worsening) |
| **A02** CORE-OM life functioning | `CORE_OM_MCID_SUBSCALE_NORM` | **0.10** normalized (R4 — functioning ↑ = improvement) |
| **A03** CORE-OM problems | `CORE_OM_MCID_SUBSCALE_NORM` | **0.10** normalized (R2 / L2 — problems ↓ = improvement) |
| **A04** CORE-OM wellbeing | `CORE_OM_MCID_SUBSCALE_NORM` | **0.10** normalized (R3 — wellbeing ↑ = improvement) |
| **A05** CORE-OM risk | `CORE_OM_RISK_RELAPSE_THRESHOLD` | **≥ 0.70** normalized (L3 relapse, recovery guard, risk cap) |
| **A05** CORE-OM risk *(display cap)* | `RISK_CAP_CEILING` | **40** (max score when risk ≥ 0.70) |
| **A05** CORE-OM risk *(delta)* | Risk increase (L4) | **≥ +0.15** normalized change |
| **A06** CORE-OM 30-day delta | `CORE_OM_MCID_TOTAL` | **5** raw points (meaningful 30d total change) |
| **A06** CORE-OM follow-up window | `ASSESSMENT_WINDOW_MIN` / `MAX` | **T+21d** to **T+45d** (target **T+30d**) |
| **A07** GAD-7 anxiety | `GAD7_MCID` | **4** raw points (secondary recovery / L5) |

**Program-level label constants (sign once at G1)**

| Scope | Constant | Value |
|-------|----------|-------|
| Assessment horizon | `ASSESSMENT_HORIZON_DAYS` | **30** days |
| Dropout observation | `DROPOUT_HORIZON_DAYS` | **60** days from snapshot T |
| Dropout inactivity | `DROPOUT_INACTIVE_DAYS` | **30** consecutive days |
| Engagement loss | `ENGAGEMENT_LOSS_RELATIVE_DROP` | **50%** vs baseline at T |
| Engagement loss horizon | Engagement compare offset | **T+14 days** vs baseline at T |
| Direction rule | CORE-OM total | Lower = improvement |

**G1 MCID sign-off**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Date | _________________________ |
| Overrides (constant → new value) | _________________________ |

---

### Clinical sign-off — baselines, windows & trends (G1 / G2 / G6)

**Signatory:** Clinical lead + Product · **Reference:** [L2 Feature Store §7](../L2-Feature-Store-Production-Spec.md), [CRS Unified v3 §8, §13](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)

Scores use **contextual features** (averages, slopes, volatility) — not single raw events. Clinical signs off on **how many past days** each signal uses and **what counts as a meaningful trend**.

#### Global defaults (apply to all attributes)

| Parameter | What it controls | Default | ☐ Sign-off |
|-----------|------------------|---------|------------|
| **Trend arrow lookback** | Compare trend score now vs N days ago | **7** calendar days | ☐ |
| **Trend direction threshold** | Min score change to show ↑ / ↓ (not stable) | **3** points | ☐ |
| **Trend volatility window** | Std-dev for Emotional Stability etc. | **14** days | ☐ |
| **Cold-start cohort prior** | Default score when user has &lt; 7 days data | **50** (neutral) | ☐ |
| **Cold-start stage** | `days_active` 0–7 — Limited confidence | **7** days | ☐ |
| **Early maturity stage** | Mix personal + prior; Moderate confidence cap | **7–30** days | ☐ |
| **Full maturity stage** | Personal features only; High confidence possible | **30+** days | ☐ |
| **Limited confidence** | `days_active ≤ 7` OR completeness &lt; **0.4** | — | ☐ |
| **Moderate confidence** | `days_active ≤ 30` OR completeness &lt; **0.7** | — | ☐ |
| **High confidence** | `days_active > 30` AND completeness ≥ **0.7** | — | ☐ |
| **Assessment latest lookback** | Most recent CORE-OM / GAD-7 / PHQ-9 etc. | **90** days | ☐ |
| **Intake form lookback** | Latest form values (A44–A64) | **90** days | ☐ |
| **Biomarker latest lookback** | Most recent lab result | **90** days | ☐ |
| **Weight change delta** | A26 % change vs prior | **90** days | ☐ |
| **Crisis escalation** | A57 `form_crisis_marker_flag = true` | Immediate human support | ☐ |

#### Per-attribute windows & baselines

**Legend:** *Avg* = rolling mean · *Slope* = OLS trend · *Rate* = active days / window · *Latest* = most recent value in lookback · *Min days* = minimum data points before feature is non-null.

| Attribute | Level / avg window | Trend / slope window | Min days | Baseline / comparison | Default |
|-----------|-------------------|----------------------|----------|----------------------|---------|
| **A01–A05** CORE-OM subscales | Latest in **90d** | — | 0 | Latest assessment event | Current score |
| **A06** CORE-OM delta | **30d** delta | — | **30** | Score today vs **30d** ago | Paired assessments |
| **A07** GAD-7 | Latest in **90d** | — | 0 | Latest assessment | Current score |
| **A08** PHQ-9 | Latest in **90d** | — | 0 | Latest assessment | Current score |
| **A09** Trauma | Latest in **90d** | — | 0 | Latest assessment | Current score |
| **A10** ASRS (ADHD) | Latest in **90d** | — | 0 | Latest assessment | Current score |
| **A11** Sleep | **7d** avg (`sleep_avg_7d`) | **7d** slope; **14d** variance | **7** | Prior **7d** for slope; **7d vs 7d ago** for arrow | Hours/night mean |
| **A12** Fatigue | **7d** avg | — | **7** | Rolling **7d** mean | Self-report 0–5 |
| **A13** HRV | **7d** avg | **7d** trend (slope) | **7** | Prior **7d** for trend | Wearable RMSSD |
| **A14** Resting HR | **7d** avg | **7d** slope | **7** | **7d** vs **30d** relative baseline | BPM mean |
| **A15** Exercise | **7d** days + minutes | — | **7** | Active days in **7d** | Days + min/week |
| **A16** Nutrition | **7d** avg | — | **7** | Rolling **7d** mean | Quality 0–5 |
| **A17** Hydration | **7d** avg | — | **7** | Rolling **7d** mean | vs daily target |
| **A18** Hunger | **7d** avg | — | **7** | Rolling **7d** mean | 0–5 |
| **A19** Sun exposure | **7d** avg minutes | — | **7** | Rolling **7d** mean | Minutes/day |
| **A20** Libido | **14d** avg | — | **7** | Rolling **14d** mean | 0–5 |
| **A21–A25** Biomarkers | Latest in **90d** | — | 0 | Lab reference range | Latest result |
| **A26** Weight change | **90d** delta | — | **30** | % vs **90d** ago | Body weight |
| **A27** Mood | **14d** avg | **7d** slope; **14d** volatility | **7** | Slope over **7d**; arrow vs **7d** ago | 0–5 normalized |
| **A28** Motivation | **14d** avg | **7d** slope | **7** | Slope over **7d** | 0–5 normalized |
| **A29** Confidence | **14d** avg | **7d** slope | **7** | Slope over **7d** | 0–5 normalized |
| **A30** Memory game | **7d** avg score | **7d** slope | **7** | Game score trend **7d** | Normalized 0–100 |
| **A31** Connect Four | **7d** avg score | — | **7** | Rolling **7d** mean | Normalized 0–100 |
| **A32** Whack-a-Mole | **7d** avg + frustration | — | **7** | Rolling **7d** mean | Score + miss rate |
| **A33** Journal themes | **7d** sentiment | **7d** stress flag | **7** | NLP over **7d** entries | Sentiment −1..1 |
| **A34–A36** Journal types | **7d** sentiment each | — | **7** | Rolling **7d** NLP mean | Per journal type |
| **A37** App engagement | **7d** rate | **7d** slope; **30d** delta | **0** / **7** | Loss label: **50%** drop at **T+14** vs T | Sessions/active days |
| **A38** Support-seeking | **30d** rate | — | **7** | Events in **30d** | Rate 0–1 |
| **A39** Guide usage | **30d** rate | — | **7** | Content views in **30d** | Rate 0–1 |
| **A40** Focus sessions | **7d** rate | — | **7** | Sessions in **7d** | Rate 0–1 |
| **A41** Task completion | **7d** completion + drop-off | — | **7** | Rolling **7d** | Rate 0–1 |
| **A42** Check-in completion | **7d** rate | — | **7** | Check-ins completed **7d** | Rate 0–1 |
| **A43** Therapy attendance | **30d** rate | — | **7** | Sessions attended **30d** | Rate 0–1 |
| **A44–A55, A58–A64** Intake forms | Latest in **90d** | — | 0 | Most recent form submission | Normalized 0–1 |
| **A56** Self-talk (NLP) | **30d** composite | — | **7** | Form + journal NLP **30d** | Severity 0–1 |
| **A57** Crisis marker | Latest in **90d** | — | 0 | **Immediate** if flag true | Boolean escalation |
| **A65** Missed check-ins | **7d** count | — | **7** | Days missed in **7d** | Day count |
| **A66** Sessions missed | **30d** missed rate | — | **7** | Cancelled/no-show **30d** | Rate 0–1 |
| **A67** Days since session | — (point-in-time) | — | 0 | Days since last attended | Integer days |
| **A68–A70** Therapist sheet | Latest sync | — | 0 | Current therapist match row | Score 0–100 |

#### Seven trend metrics — composite windows (G2 sign-off)

Each trend arrow uses **direction_7d**: score today vs score **7 days ago**, threshold **±3** points.

| Trend metric | Primary inputs | Level windows | Slope / volatility windows |
|--------------|----------------|---------------|--------------------------|
| **Recovery Readiness** | A11, A13, A12, A06 | Sleep **7d**, HRV **7d** | Sleep slope **7d**, HRV trend **7d**, CORE-OM delta **30d** |
| **Stress Load** | A07–A09, A13–A14, A21–A23, A27 | GAD-7 latest, cortisol **90d** | HRV trend **7d**, mood volatility **14d** |
| **Sleep Consistency** | A11, A12 | Sleep **7d** avg | **14d** duration + bedtime variance |
| **Energy Rhythm** | A12, A15–A18, A28, A37 | Fatigue **7d**, exercise **7d** | Motivation slope **7d**, engagement slope **7d** |
| **Emotional Stability** | A27–A29, A07–A09, A33–A36 | Mood **14d** avg | Mood volatility **14d**, mood/confidence slope **7d** |
| **Motivation Momentum** | A28, A37–A39, A42, A61 | Motivation **14d**, engagement **7d** | Motivation + engagement slope **7d** |
| **Cognitive Momentum** | A30–A31, A02, A52, A10 | Game scores **7d**, functioning latest | Game memory slope **7d**, brain fog latest |

**G1 / G2 baseline & window sign-off**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Product | _________________________ |
| Date | _________________________ |
| Window overrides (e.g. mood avg 14d → 21d) | _________________________ |

---

### G1 — Pre-build (Week 1: 24–30 June 2026)

**Thresholds & rules** — MCID table: [Clinical sign-off — MCID & label thresholds](#clinical-sign-off--mcid--label-thresholds-g1--g3) · Windows: [baselines, windows & trends](#clinical-sign-off--baselines-windows--trends-g1--g2--g6)

- [ ] **CORE-OM risk cap** — `core_om_risk ≥ 0.70` caps all display scores at **40** (confirm or change threshold)
- [ ] **Risk relapse threshold** — normalized risk **≥ 0.70** at follow-up counts as relapse signal (L3)
- [ ] **CORE-OM total MCID** — default **5 raw points** for meaningful improvement/worsening (R1, L1)
- [ ] **CORE-OM subscale MCID** — default **0.10** normalized for problems / wellbeing / functioning (R2–R4, L2)
- [ ] **GAD-7 MCID** — default **4 raw points** for secondary recovery path and relapse (R4 confirmer, L5)
- [ ] **Assessment follow-up window** — **[T+21d, T+45d]** around 30-day horizon (confirm cadence with product)
- [ ] **Direction rule** — lower CORE-OM total = improvement; documented for ML and reporting teams

**Safety & governance**

- [ ] **Escalation workflow** — who is contacted when risk is elevated; response SLA agreed with operations
- [ ] **No diagnosis rule** — all user-facing copy uses probabilistic language only (“may”, “suggests”); no diagnostic labels
- [ ] **Scores are not therapy** — disclaimer that CRS/readiness is supportive information, not a clinical decision
- [ ] **Crisis pathway** — `form_crisis_marker` and high `core_om_risk` routes to human support (not in-app only)

**Instruments & data**

- [ ] **CORE-OM** — approved for ingestion, subscales used (wellbeing, problems, functioning, risk)
- [ ] **GAD-7** — approved as anxiety input and label confirmer
- [ ] **PHQ-9, PTSD, ASRS** — approved for Phase 5 / enrichment wave (if in 2.5-month scope)
- [ ] **Biomarker consent** — policy for lab results before Wave D (if in scope)

**Sign-off G1**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Date | _________________________ |
| Notes / threshold changes | _________________________ |

---

### G2 — Risk cap QA (Week 4: ~21 July 2026)

**Staging verification**

- [ ] Test user with `core_om_risk = 0.72` → **all** pillar, CRS, and trend display scores **≤ 40**
- [ ] Risk-elevated user sees **escalation messaging**, not positive “high readiness” copy
- [ ] `risk_elevated = true` in API when threshold met
- [ ] Risk cap applies to **both** same-day readiness and trajectory readiness (when live)
- [ ] Web-only user (no wearable) — scores still compute; no false risk signals from missing data
- [ ] Cold-start user — cohort prior behaviour acceptable; confidence tier shows “Limited” where appropriate
- [ ] **W1 window defaults** — sleep/mood **7–14d**, engagement **7d**, therapy **30d** per [baseline table](#per-attribute-windows--baselines)

**Sign-off G2**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Date | _________________________ |

---

### G3 — ML outcome labels (Week 6: ~4 August 2026)

**Label definitions (training only — not shown to users)**

- [ ] **Recovery rules R1–R4** reviewed — subscale-aware, not total-score only ([Appendix B.1](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md#appendix-b1--clinical-label-decision-tree-for-sign-off))
- [ ] **Relapse rules L1–L5** reviewed — relapse evaluated **before** recovery; mutually exclusive
- [ ] **Recovery safety guard** — no recovery label if `core_om_risk ≥ 0.70` at follow-up
- [ ] **Censoring policy** — no follow-up assessment → label = null (not 0); acceptable training exclusion
- [ ] **GAD-7 secondary path** — acceptable when CORE-OM follow-up missing; flagged `label_confidence=secondary`
- [ ] **Dropout label** — `user_churned` + **30-day** inactivity within **60-day** horizon
- [ ] **Engagement loss** — **≥50%** drop vs 30-day baseline engagement
- [ ] **Censoring rate** — reviewed monthly target **< 40%** for clinical models at 30d+ maturity
- [ ] **`label_version`** — `label_v2.0.0` recorded in model registry with signed thresholds

**Sign-off G3**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Date | _________________________ |

---

### G4 — Narrative & shadow report (Week 7: 5–14 August 2026)

**Five report questions (staging)**

- [ ] **Where am I now?** — accurate, non-diagnostic, reflects band (Low / Moderate / High)
- [ ] **Why is it like this?** — drivers use probabilistic language; no invented causes
- [ ] **What should I be aware of?** — trend warnings appropriate severity (info / warning / critical)
- [ ] **What is my risk?** — `relapse_probability` and `core_om_risk` explained without alarmism
- [ ] **What should I do next?** — actions safe and appropriate (check-in, sleep, contact therapist)

**Risk-elevated narrative override**

- [ ] When `core_om_risk ≥ 0.70`, narrative switches to **escalation copy** (not standard positive framing)
- [ ] `escalation_recommended = true` when policy requires human follow-up
- [ ] **Contact therapist / support** is priority action when risk elevated

**Dual scores (shadow period)**

- [ ] Same-day readiness vs trajectory readiness — clinical team comfortable with both being visible internally
- [ ] Large divergence (|v2 − readiness| > 20) — review process defined for outlier users

**Sign-off G4**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Product (copy) | _________________________ |
| Date | _________________________ |

---

### G5 — Production launch (Week 8+: from 15 August 2026)

**Go-live**

- [ ] **Trajectory readiness** as headline for mature users — clinical accepts maturity rules (readiness fallback for new users)
- [ ] **Score meanings** — pillar definitions (Clarity, Emotional Balance, Resilience, Capacity) approved for app
- [ ] **Trend arrows** — direction language (↑ improving / ↓ declining) clinically sensible
- [ ] **Support runbook** — ops can answer “why did my score change?” without clinical ticket for every user
- [ ] **Rollback** — clinical accepts `FORCE_CRS_PRIMARY=readiness` if model issues post-launch
- [ ] **Monitoring** — quarterly clinical review of thresholds scheduled

**Sign-off G5 (go / no-go)**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Product | _________________________ |
| Date | _________________________ |
| Decision | ☐ Go  ☐ No-go  ☐ Go with conditions: _______________ |

---

### G6 — Baselines & enrichment windows (Weeks 8–10 — parallel)

*Complete per-attribute window sign-off:* [baselines, windows & trends](#clinical-sign-off--baselines-windows--trends-g1--g2--g6)

- [ ] **Global defaults** — 7d trend lookback, 3pt arrow threshold, 7/30d maturity stages approved
- [ ] **W2–W7 attributes** — lifestyle **7d**, mood **14d** avg, forms **90d** latest, biomarkers **90d** lookback
- [ ] **PHQ-9 / PTSD / ASRS** — **90d** latest assessment window + instrument copy approved
- [ ] **Crisis marker (A57)** — escalation path tested (`form_crisis_marker_flag`)
- [ ] **Biomarkers** — **90d** lookback + consent + reference ranges; no diagnostic claims
- [ ] **Journal NLP** — **7d** sentiment window; pattern-only copy
- [ ] **70/70 traceability** — sample users: raw event → L2 window feature → pillar/trend score

**Sign-off G6**

| Field | Value |
|-------|-------|
| Clinical lead | _________________________ |
| Product | _________________________ |
| Date | _________________________ |
| Window overrides | _________________________ |

---

### Ongoing governance (post-launch)

- [ ] **Quarterly threshold review** — MCID, risk cap, label rates
- [ ] **Label drift alert** — ±5% change in positive label rate investigated with clinical
- [ ] **Model AUC drop** — >5% weekly decline triggers clinical + ML review
- [ ] **Reassessment cadence** — product nudges align with 21–45 day CORE-OM window

---

## Timeline overview

**Program kickoff:** **24 June 2026** (Week 1)  
**Target:** ~2.5 months to public launch (~early September 2026)

| Week | Dates (2026) | Phase |
|------|----------------|-------|
| 1 | 24 Jun – 30 Jun | Prepare — approvals & clinical sign-off |
| 2–4 | 1 Jul – 21 Jul | Build core report — first scores |
| 5–6 | 22 Jul – 4 Aug | Prediction models |
| 7 | 5 Aug – 14 Aug | Validate — dual scores + narrative |
| 8+ | 15 Aug onward | Public release |
| 2–8 (parallel) | 1 Jul – 14 Aug | Enrich data — games, forms, labs |

```mermaid
gantt
    title Stakeholder View - 2.5 Month Delivery Plan
    dateFormat YYYY-MM-DD
    axisFormat %b %d

    section Prepare
    Approvals and clinical sign-off      :prep, 2026-06-24, 7d

    section Build core report
    First working scores internal        :core, 2026-07-01, 21d

    section Add intelligence
    Prediction models trained            :ml, 2026-07-22, 14d

    section Validate
    Dual scores and personalized text    :val, 2026-08-05, 10d

    section Launch
    Public release                       :launch, 2026-08-15, 14d

    section Enrich data parallel
    More inputs games forms labs         :expand, 2026-07-01, 45d
```

---

## Phase-by-phase — what changes for users and the business

### Phase 0 — Prepare (Week 1 — starts 24 June 2026)

**What happens:** Specs, clinical thresholds, and data agreements are approved.

| You’ll see | You won’t see yet |
|------------|-------------------|
| Signed-off score meanings and risk rules | Any live user scores |

**We need from you:**

- Clinical: complete **[G1 checklist](#g1--pre-build-week-1-24-30-june-2026)** (risk cap, MCIDs, escalation)  
- Product: approve score labels and band copy (Low / Moderate / High)  

---

### Phase 1 — Foundation (Weeks 2–4 — 1 July to 21 July 2026)

**What happens:** We connect core data sources and produce the **first real scores** using rule-based logic (no AI predictions yet).

**What users get (internal / staging only):**

- Overall **same-day readiness** score  
- Four pillar scores (Clarity, Emotional Balance, Resilience, Capacity)  
- Seven trend directions  
- Risk cap when clinical risk is elevated  

**Which user data powers this phase (~26% of full product spec):**

| Included now | Coming later (Phase 5) |
|--------------|------------------------|
| CORE-OM & GAD-7 assessments | Depression (PHQ-9), trauma, ADHD screens |
| Mood, motivation, confidence check-ins | Lifestyle (fatigue, exercise, nutrition, hydration) |
| Sleep & heart-rate (wearables) | Lab biomarkers (cortisol, thyroid, glucose, etc.) |
| App engagement | Brain games scores |
| Therapy attendance | Intake forms (21 fields) |
| | Therapist matching sheet |
| | Advanced journal analysis |

> **Important:** Phase 1 delivers the **full scoring framework** but only **about one-quarter of all planned data inputs**. Missing inputs don’t break the report — weights adjust to use what’s available. This is intentional so we can ship a credible report early.

**Business milestone (Week 4 — ~21 July 2026):** First scores visible for test users in staging.

---

### Phase 2 — Prediction models (Weeks 5–6 — 22 July to 4 August 2026)

**What happens:** We train AI models on historical data to predict four real outcomes:

| Outcome | Plain question |
|---------|----------------|
| Recovery | Is the user likely to show meaningful clinical improvement? |
| Relapse | Is the user likely to worsen? |
| Dropout | Is the user likely to leave therapy or go inactive? |
| Engagement loss | Is the user likely to disengage from the app? |

**What users get:** Still the same-day readiness score publicly. Models run in the background — not yet the headline number.

**We need from you:**

- Clinical: review how “recovery” and “relapse” are defined from assessments  
- Leadership: patience — model quality depends on having enough historical follow-up data  

**Business milestone (Week 6 — ~4 August 2026):** Models pass quality checks and are approved for shadow testing.

---

### Phase 3 — Validate before launch (Week 7 — ~5–14 August 2026)

**What happens:** We combine prediction models into the **trajectory readiness score** and add **personalized report text** (the five questions).

**What users get (staging / internal QA):**

- Both scores side by side for comparison  
- “Where / Why / Aware / Risk / Next” narrative blocks  
- Early-warning flags (e.g. declining motivation)  

**We need from you:**

- Product: review all user-facing copy  
- Clinical: review risk and escalation messaging  
- Design: review report layout with real sample data  

**Business milestone (Week 7 — ~14 August 2026):** Go / no-go decision for public launch.

---

### Phase 4 — Public launch (Week 8+ — from ~15 August 2026)

**What happens:** Trajectory readiness becomes the **main headline score** for users with enough history. The report API goes live in production with monitoring and rollback plans.

**What users get:**

- Full daily report in the app  
- Trajectory readiness as primary score (when data maturity is sufficient)  
- Same-day readiness still visible for context  
- Personalized guidance and risk-aware messaging  

**We need from you:**

- Product & Clinical: final sign-off  
- Operations: support runbooks for “why did my score change?”  
- Leadership: communicate two-score story clearly in release notes  

---

### Phase 5 — Richer data (parallel from Week 2 — 1 July 2026)

**What happens:** We connect remaining data sources from the Engine Part1 product spec so scores use **100% of planned inputs**.

| Wave | What we add | User-visible benefit |
|------|-------------|---------------------|
| **A** | Lifestyle check-ins + brain games | Richer energy, recovery, and cognitive trends |
| **B** | Intake / onboarding forms | Better understanding of work stress, burnout, routines |
| **C** | Extra assessments (depression, trauma, ADHD) | More complete clinical picture |
| **D** | Lab results + therapist matching data | Deeper biological and therapy-fit signals |
| **E** | Journal sentiment analysis | Emotional patterns from writing |

**What users get over time:** Scores become **more personalized and stable** as more inputs flow in. Users who only use core features are unaffected.

**Business milestone:** 100% of planned inputs connected; trend arrows use full formula set.

---


## Frequently asked questions

**Q: Will Phase 1 mean Engine Part1 is “done”?**  
**A:** No. Phase 1 means the **report works** with core inputs (assessments, check-ins, sleep, engagement, therapy). The full Part1 input list completes in Phase 5. Formulas are ready from day one; data connections grow over time.

**Q: Can we launch without games, forms, and lab data?**  
**A:** Yes. Launch (Phase 4) is designed around core inputs. Phase 5 improves accuracy and personalization — it does not block launch.

**Q: Why two readiness scores?**  
**A:** Same-day readiness works from day one and is easy to explain. Trajectory readiness is more predictive but needs models and history. We use both during validation, then promote trajectory readiness for established users.

**Q: What if a user has no wearable?**  
**A:** The report still works. Sleep and heart-rate sections adjust; scores use check-ins, assessments, and app activity instead.

**Q: What if scores look wrong?**  
**A:** Every score is traceable to source data and versioned formulas. We can audit “why” for any user. Rollback switches are available if a model misbehaves after launch.

**Q: How often do scores update?**  
**A:** Once daily, typically ready by early morning UTC. Yesterday’s activity is included in today’s report.

**Q: Who owns clinical safety?**  
**A:** Clinical lead completes the [Clinical team sign-off checklist](#clinical-team-sign-off-checklist) at each gate (G1–G6). Engineering implements — Clinical governs.

---

## Your involvement — quick reference

| Role | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|------|---------|---------|---------|---------|---------|---------|
| **Clinical** | **[G1](#g1--pre-build-week-1-24-30-june-2026)** MCID + windows | **[G2](#g2--risk-cap-qa-week-4-21-july-2026)** W1 windows | **[G3](#g3--ml-outcome-labels-week-6-4-august-2026)** labels | **[G4](#g4--narrative--shadow-report-week-7-5-14-august-2026)** narrative | **[G5](#g5--production-launch-week-8-from-15-august-2026)** launch | **[G6](#g6--baselines--enrichment-windows-weeks-8-10--parallel)** 70/70 windows |
| **Product** | Score meanings | Staging review | — | Copy + UX QA | Launch comms | Prioritize waves |
| **Design** | — | Early layouts | — | Report polish | Production UI handoff | New input UX |
| **Leadership** | Scope approval | — | — | Go/no-go | Launch | Investment for Phase 5 |
| **Operations** | — | — | — | — | Support runbooks | New source monitoring |

---

## Risks stakeholders should know

| Risk | Impact | Our mitigation |
|------|--------|----------------|
| Users expect “full Part1” at Week 4 | Disappointment / trust | This document + clear “26% inputs” messaging |
| Sparse reassessment data | Weaker predictions early | Models improve as cohort matures; censoring rules prevent false confidence |
| Two scores confuse users | Support burden | Footnotes in app; readiness stays visible after launch |
| New data sources delayed | Slower Phase 5 | Launch unaffected; scores renormalize with available data |

---

## Glossary (minimal)

| Term | Plain meaning |
|------|----------------|
| **Readiness score** | 0–100 summary of mental readiness |
| **Pillar** | One of four “how you are now” dimensions |
| **Trend** | A direction arrow showing improvement or decline over ~7 days |
| **MCID** | Minimum meaningful change on validated assessments (CORE-OM, GAD-7) — [sign-off table](#clinical-sign-off--mcid--label-thresholds-g1--g3) |
| **Baseline / window** | How many past days are averaged or compared for scoring (e.g. mood **14d** avg, trend arrow **7d**) — [sign-off table](#clinical-sign-off--baselines-windows--trends-g1--g2--g6) |
| **Risk cap** | Safety rule that limits scores when clinical risk is high |
| **Staging** | Internal test environment — not visible to real users |
| **GA** | General availability — live for real users |

---
