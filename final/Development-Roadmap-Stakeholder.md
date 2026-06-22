# MindPeers Cognitive Readiness Engine — Stakeholder Roadmap

**Audience:** Product, Clinical, Leadership, Design, Operations  
**Version:** 1.0.0  
**Date:** 2026-06-05  
**Technical companion:** [Development-Roadmap.md](./Development-Roadmap.md) (for Engineering & Data teams)

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

## Timeline overview

**About 11 weeks** from kickoff to public launch, plus an **ongoing expansion** to connect all data sources from the product spec.

```mermaid
gantt
    title Stakeholder view — when capabilities land
    dateFormat YYYY-MM-DD
    axisFormat %b %d

    section Prepare
    Approvals & clinical sign-off       :prep, 2026-06-09, 10d

    section Build core report
    First working scores (internal)       :core, 2026-06-16, 28d

    section Add intelligence
    Prediction models trained           :ml, after core, 28d

    section Validate
    Dual scores + personalized text     :val, after ml, 14d

    section Launch
    Public release                      :launch, after val, 21d

    section Enrich data (parallel)
    More inputs: games, forms, labs     :expand, 2026-07-14, 120d
```

---

## Phase-by-phase — what changes for users and the business

### Phase 0 — Prepare (1–2 weeks before build)

**What happens:** Specs, clinical thresholds, and data agreements are approved.

| You’ll see | You won’t see yet |
|------------|-------------------|
| Signed-off score meanings and risk rules | Any live user scores |

**We need from you:**

- Clinical: approve risk cap and assessment change rules  
- Product: approve score labels and band copy (Low / Moderate / High)  
- Leadership: confirm launch scope (core report first; full data inputs later)

---

### Phase 1 — Foundation (Weeks 1–4)

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

**Business milestone (Week 4):** First scores visible for test users in staging.

---

### Phase 2 — Prediction models (Weeks 5–8)

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

**Business milestone (Week 8):** Models pass quality checks and are approved for shadow testing.

---

### Phase 3 — Validate before launch (Weeks 9–10)

**What happens:** We combine prediction models into the **trajectory readiness score** and add **personalized report text** (the five questions).

**What users get (staging / internal QA):**

- Both scores side by side for comparison  
- “Where / Why / Aware / Risk / Next” narrative blocks  
- Early-warning flags (e.g. declining motivation)  

**We need from you:**

- Product: review all user-facing copy  
- Clinical: review risk and escalation messaging  
- Design: review report layout with real sample data  

**Business milestone (Week 10):** Go / no-go decision for public launch.

---

### Phase 4 — Public launch (Week 11+)

**What happens:** Trajectory readiness becomes the **main headline score** for users with enough history. The report API goes live in production with monitoring and rollback plans.

**What users get:**

- Full daily report in the app  
- Trajectory readiness as primary score (when data maturity is sufficient)  
- Same-day readiness still visible for context  
- Personalized guidance and risk-aware messaging  

**Launch does not wait** for every data source (games, forms, labs) — those enrich scores in Phase 5.

**We need from you:**

- Product & Clinical: final launch sign-off  
- Operations: support runbooks for “why did my score change?”  
- Leadership: communicate two-score story clearly in release notes  

**Business milestone:** Production launch with 99.9% API availability target.

---

### Phase 5 — Richer data (parallel from Week 5, ~4–7 months)

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

## Milestones executives can track

| # | When | What success looks like | Data richness |
|---|------|-------------------------|---------------|
| **M1** | Week 4 | First real scores for test users | ~26% of inputs |
| **M2** | Week 8 | Prediction models approved | ~26% |
| **M3** | Week 10 | Personalized report ready for review | ~26% + narrative |
| **M4** | Week 11–13 | **Public launch** | ~26% at launch |
| **M5** | Month 4–5 | Half of all inputs connected | ~50% |
| **M6** | Month 6–8 | All inputs connected | **100%** |

---

## What we are *not* building in this program

| Out of scope | Why |
|--------------|-----|
| Mobile UI implementation | Separate product track — consumes our report API |
| Real-time score on every tap | Daily batch is simpler, auditable, and sufficient for v1 |
| AI chat / open-ended coaching | Separate LLM program |
| Full CogniArt cognitive testing | Future phase |

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
**A:** Clinical lead approves risk thresholds, label definitions, and escalation copy. Engineering implements — Clinical governs.

---

## Your involvement — quick reference

| Role | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|------|---------|---------|---------|---------|---------|---------|
| **Clinical** | Approve risk & labels | Risk cap QA | Label definitions | Narrative + risk copy | Launch sign-off | New input validation |
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
| **Risk cap** | Safety rule that limits scores when clinical risk is high |
| **Staging** | Internal test environment — not visible to real users |
| **GA** | General availability — live for real users |

---

## Related documents

| Document | Who should read it |
|----------|-------------------|
| [Development-Roadmap.md](./Development-Roadmap.md) | Engineering, Data, ML — technical schedule |
| [MindPeers-Engine-Master-Production-Spec.md](./MindPeers-Engine-Master-Production-Spec.md) | Deep dive for technical leads |
| [Engine Part1.docx](../Engine%20Part1.docx) | Product source — pillar inputs and weights |
| [00-Master-Program-TRD.md](./00-Master-Program-TRD.md) | Formal requirements |

### Export to PDF

```bash
pandoc final/Development-Roadmap-Stakeholder.md \
  -o final/Development-Roadmap-Stakeholder.pdf \
  --toc -V geometry:margin=1in \
  --metadata title="MindPeers Engine — Stakeholder Roadmap"
```

---

## Revision history

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-05 | Initial non-technical stakeholder roadmap |

---

*Questions? Contact the program lead. For technical implementation detail, see [Development-Roadmap.md](./Development-Roadmap.md).*
