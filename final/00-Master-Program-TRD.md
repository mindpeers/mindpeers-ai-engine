# Master Program TRD — MindPeers Cognitive Readiness Engine

**Document ID:** MP-ENGINE-TRD-000  
**Version:** 1.0.0  
**Status:** For review  
**Date:** 2026-06-05

---

## 1. Purpose

Define the **end-to-end technical requirements** for the MindPeers Cognitive Readiness Engine across all implementation phases, from raw event ingestion through user-facing report API.

This master TRD governs phase-specific TRDs (Phase 01–05). Phase TRDs inherit requirements listed here unless explicitly deferred.

---

## 2. Business objectives

| Objective | Success metric |
|-----------|----------------|
| Deliver unified mental health report | CRS + 4 pillars + 7 trends on dashboard |
| Ground scores in real data | ≥95% snapshots have auditable L0 lineage |
| Predict trajectory (CRS v2) | Recovery model AUC-PR ≥ 0.65 on holdout |
| Clinical safety | Risk cap fires when `core_om_risk ≥ 0.70`; escalation workflow documented |
| Deterministic scoring | Same inputs + versions → identical outputs (batch = API) |
| Cold start support | Scores available from day 1 with confidence tier |

---

## 3. Scope

### 3.1 In scope

| Layer | Capability |
|-------|------------|
| **L0** | Event ingestion, validation, staging rollups |
| **L2** | 34-column feature row, windows, flags, meta |
| **L4** | Label generation, 4 outcome models, inference |
| **L3** | CRS v2, CRS readiness, pillars (Part1), trends, risk cap |
| **L1** | Snapshot API, patterns, narrative (five questions) |

### 3.2 Out of scope (program level)

- Mobile UI implementation (consumes L1 API only)
- Real-time streaming scores (batch-first; API reads snapshot)
- LLM intent router productionization (L4 LLM — separate program)
- CogniArt full NLP pipeline (Phase 5 partial)

---

## 4. Stakeholders

| Role | Responsibility |
|------|----------------|
| Product | Score meanings, five questions, band copy |
| Clinical lead | MCID thresholds, risk cap, escalation |
| Engineering | L0–L3 services, API |
| Data Platform | Warehouse, batch orchestration |
| ML | Labels, models, monitoring |
| Security / Legal | PHI, consent, retention |

---

## 5. System requirements (cross-phase)

### 5.1 Functional

| ID | Requirement | Phase |
|----|-------------|-------|
| FR-001 | Ingest all v1 event types per Data Ingestion spec Appendix A | 1 |
| FR-002 | Produce `staging.user_daily_activity` at grain `(user_id, local_date)` | 1 |
| FR-003 | Compute 34 L2 features deterministically per L2 spec | 1 |
| FR-004 | Compute 4 pillar scores using Part1 category weights §7.6 | 1 |
| FR-005 | Compute CRS readiness using Part1 5-category weights §6.6 | 1 |
| FR-006 | Compute 7 trend metrics with direction arrows | 1 |
| FR-007 | Apply CORE-OM risk cap (≥0.70 → cap 40) on all display scores | 1 |
| FR-008 | Generate clinical labels per §4.3 (R1–R4, L1–L5) offline | 2 |
| FR-009 | Train 4 outcome models; register in model registry | 2 |
| FR-010 | Run inference: P(recovery), P(relapse), P(dropout), P(engagement_loss) | 2–3 |
| FR-011 | Compute CRS v2 composite §6.1 | 3 |
| FR-012 | Shadow CRS v2 alongside readiness; expose both in API | 3 |
| FR-013 | Generate narrative blocks (Where/Why/Aware/Risk/Next) §10.4 | 3 |
| FR-014 | Set `crs_primary = v2` when maturity rules met §13 | 4 |
| FR-015 | Persist `user_engine_snapshot` for L1 API | 4 |
| FR-016 | Ingest v1.1 events: games, forms, biomarkers (Appendix F) | 5 |

### 5.2 Non-functional

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | Batch pipeline completion | By 03:30 UTC daily |
| NFR-002 | API p99 latency (snapshot read) | < 200ms |
| NFR-003 | Ingestion availability | 99.9% |
| NFR-004 | Determinism | Bit-identical batch vs API path |
| NFR-005 | Auditability | `score_version`, `label_version`, `model_bundle_version` on every snapshot |
| NFR-006 | Data retention | Per privacy policy; raw events ≥ 24 months |
| NFR-007 | Throughput design | 10,000 requests/min API; 500K users batch |
| NFR-008 | Idempotent ingestion | Duplicate events do not double-count |
| NFR-009 | Censoring transparency | `label_censored_reason` stored for ML rows |
| NFR-010 | No diagnosis copy | Narrative uses probabilistic language only |

---

## 6. Data requirements

### 6.1 Canonical tables

| Table | Grain | Owner |
|-------|-------|-------|
| `raw.events` | event | L0 |
| `staging.user_daily_activity` | user-day | L0 |
| `features.user_features_daily` | user-day | L2 |
| `ml.training_labels` | user-snapshot | L4 |
| `ml.model_registry` | model version | L4 |
| `scoring.user_scores_daily` | user-day | L3 |
| `user_engine_snapshot` | user-day | L1 |

### 6.2 Version fields (mandatory)

Every scoring output must include:

```
score_version, feature_version, label_version (training only),
model_bundle_version, trend_version, computed_at
```

---

## 7. Phase breakdown

| Phase | Weeks | Deliverable | Entry criteria | Exit criteria |
|-------|-------|-------------|----------------|---------------|
| **1** | 1–4 | L0 + L2 + L3 rule-based | PRD signed, schemas approved | Pillars + readiness + trends in staging DB |
| **2** | 5–8 | Labels + trained models | Phase 1 exit; 90d history | 4 models in registry; AUC targets met |
| **3** | 9–10 | CRS v2 shadow + narrative | Phase 2 exit | Dual scores in API; narrative QA passed |
| **4** | 11+ | Production cutover | Phase 3 exit; clinical sign-off | `crs_primary=v2`; L1 API GA |
| **5** | Ongoing | v1.1 inputs | Phase 1 L0 patterns stable | Part1 parameters ≥80% v1.1 available |

---

## 8. Acceptance criteria (program)

- [ ] End-to-end demo: event → snapshot → API response for test user
- [ ] Clinical sign-off on label thresholds and risk cap
- [ ] Product sign-off on five questions narrative copy
- [ ] Load test: 10K RPM API read path
- [ ] Batch SLA: 03:30 UTC completion 30 consecutive days
- [ ] Model monitoring dashboards live
- [ ] Runbook for ingestion failure, batch retry, model rollback

---

## 9. Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sparse CORE-OM reassessment | Biased ML training | Censoring + GAD-7 secondary path §4.3 |
| Wearable gaps | Null biological features | Web-only renormalization §13.3 |
| Score confusion (v2 vs readiness) | UX trust | Dual display + footnotes Phase 3–4 |
| Clinical risk false negative | Safety | Risk cap + escalation independent of CRS |
| Label drift | Model degradation | Monthly censoring rate + AUC monitoring §14.2 |

---

## 10. References

- [CRS Unified v3](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)
- [Data Ingestion](../Data-Ingestion-Layer-Production-Spec.md)
- [L2 Feature Store](../L2-Feature-Store-Production-Spec.md)
- [Engine Architecture Index](../Engine-Architecture-Index.md)
- `Engine Part1.docx`
