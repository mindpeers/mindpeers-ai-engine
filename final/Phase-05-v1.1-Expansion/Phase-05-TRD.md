# Phase 05 TRD — v1.1 Input Expansion (Engine Part1 Full)

**Document ID:** MP-ENGINE-TRD-P05  
**Version:** 1.0.0  
**Phase:** 5 — v1.1 Expansion  
**Timeline:** Ongoing (starts after Phase 01 L0 stable)  
**Prerequisite:** Phase 01 exit; parallel with Phases 2–4

---

## 1. Phase objective

Ingest and featureize **100% of Engine Part1 attributes** (70 canonical IDs) and bind each to **state scores** (CRS readiness + 4 pillars) and **trajectory trends** (7 metrics). See [Engine-Part1-Full-Attribute-Binding-Spec.md](../Engine-Part1-Full-Attribute-Binding-Spec.md).

**Reference:** [CRS Unified v3 Appendix F](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md#appendix-f--engine-part1-input-registry)

---

## 2. v1.1 ingestion requirements

### 2.1 New event types

| ID | Event type | Source | Priority |
|----|------------|--------|----------|
| P05-FR-L0-01 | `game_session_completed` | Games (Memory, Connect Four, Whack A Mole) | P0 |
| P05-FR-L0-02 | `intake_form_submitted` | Forms / onboarding | P0 |
| P05-FR-L0-03 | `biomarker_result` | Lab / partner API | P1 |
| P05-FR-L0-04 | `lifestyle_checkin` | Lifestyle tracker (fatigue, exercise, nutrition, hydration, hunger, libido, sun) | P0 |
| P05-FR-L0-05 | `journal_features_computed` | NLP worker (tone, themes) | P1 |
| P05-FR-L0-06 | `assessment_completed` PHQ-9, trauma instruments | Assessment service | P1 |
| P05-FR-L0-07 | Therapist sheet sync | Google Sheet / therapy platform | P1 |

### 2.2 JSON schemas

| ID | Requirement | Priority |
|----|-------------|----------|
| P05-FR-SCH-01 | Publish schemas for all v1.1 events in `schemas/ingestion/` | P0 |
| P05-FR-SCH-02 | Update `registry.json` | P0 |

### 2.3 L2 feature extensions

| ID | New L2 columns (examples) | Priority |
|----|---------------------------|----------|
| P05-FR-L2-01 | `fatigue_score_7d`, `exercise_days_7d` | P0 |
| P05-FR-L2-02 | `game_memory_score_7d`, `game_connect4_score_7d` | P0 |
| P05-FR-L2-03 | `phq9_normalized_latest`, `trauma_score_latest` | P1 |
| P05-FR-L2-04 | `journal_sentiment_7d`, `journal_stress_theme_flag` | P1 |
| P05-FR-L2-05 | `form_burnout_flag`, `form_work_stress_score` | P0 |
| P05-FR-L2-06 | `biomarker_cortisol_latest`, `biomarker_tsh_latest` | P1 |
| P05-FR-L2-07 | Bump `feature_version` to `feature_v1.1.0` | P0 |

### 2.4 L3 scoring updates

| ID | Requirement | Priority |
|----|-------------|----------|
| P05-FR-L3-01 | Include v1.1 features in Part1 category blocks §7.6 | P0 |
| P05-FR-L3-02 | Retrain outcome models with expanded feature set | P1 |
| P05-FR-L3-03 | Update availability matrix §7.8 | P0 |

---

## 3. Category coverage targets

| Milestone | Attributes live | State scores | Trajectories |
|-----------|-----------------|--------------|--------------|
| Phase 1 (W1) | 18 / 70 | Rule-based with renormalization | Minimal v1 trends |
| Phase 5 complete (W1–W7) | **70 / 70** | **Full Part1 category blocks** | **Full §8.9 bindings** |
| `feature_version` | `feature_v2.0.0` | All pillars + CRS readiness | All 7 trends upgraded |

---

## 4. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| P05-NFR-01 | Backward compatible L2 export | Old 34 cols unchanged |
| P05-NFR-02 | New columns nullable | No break for partial rollout |
| P05-NFR-03 | Biomarker consent | Per-user consent flag in L0 |

---

## 5. Rollout strategy

| Wave | Scope | Duration |
|------|-------|----------|
| Wave A | Games + lifestyle check-ins | 4 weeks |
| Wave B | Forms / intake | 4 weeks |
| Wave C | PHQ-9, trauma assessments | 4 weeks |
| Wave D | Biomarkers + therapist sheet | 8 weeks |
| Wave E | Journal NLP features | 8 weeks |

Each wave: schema → connector → L2 column → L3 block → model retrain (optional).

---

## 6. Acceptance criteria

- [ ] Registry §2: **70/70** attributes have L0 + L2 + state + trajectory binding
- [ ] `feature_version = feature_v2.0.0` deployed
- [ ] Trend formulas upgraded per CRS Unified §8.9

---

## 7. Out of scope

- CogniArt full production
- Real-time biomarker streaming
- Custom lab integrations beyond first partner

---

## 8. References

- [Phase 05 HLD](./Phase-05-HLD.md)
- [Appendix F & G](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)
- [Data Ingestion Appendix F (v1.1 events)](../../Data-Ingestion-Layer-Production-Spec.md#appendix-f--v11-event-specifications-engine-part1-complete)
- [L2 §11 full lineage](../../L2-Feature-Store-Production-Spec.md#11-l0--l2-column-lineage-full-matrix)
