# Phase 01 TRD — Foundation (L0 + L2 + L3 Rule-Based)

**Document ID:** MP-ENGINE-TRD-P01  
**Version:** 1.0.0  
**Phase:** 1 — Foundation  
**Timeline:** Weeks 1–4  
**Status:** For review

---

## 1. Phase objective

Establish the **data foundation and rule-based scoring layer** so the product can ship:

- Validated event ingestion (L0)
- Deterministic feature computation (L2)
- Four pillar scores + CRS readiness + seven trends (L3 rule-based)
- CORE-OM risk cap on all display scores

**No ML required in this phase.** CRS headline = `crs_readiness_score` (Engine Part1).

---

## 2. Dependencies

| Dependency | Owner | Required by |
|------------|-------|-------------|
| JSON schemas approved | Engineering | Week 1 |
| Source system API access | Platform | Week 1 |
| Clinical sign-off on risk cap threshold | Clinical | Week 2 |
| L2 column registry frozen (34 cols) | Data | Week 1 |

---

## 3. Functional requirements

### 3.1 L0 — Data Ingestion

| ID | Requirement | Priority |
|----|-------------|----------|
| P01-FR-L0-01 | Implement connectors: `app_mobile`, `app_web`, `wearable_apple`, `therapy_platform`, `assessments`, `auth_crm` | P0 |
| P01-FR-L0-02 | Validate events against `schemas/ingestion/` JSON Schema | P0 |
| P01-FR-L0-03 | Enforce `idempotency_key` deduplication | P0 |
| P01-FR-L0-04 | Persist to `raw.events` with envelope fields | P0 |
| P01-FR-L0-05 | Roll up to `staging.user_daily_activity` grain `(user_id, local_date)` | P0 |
| P01-FR-L0-06 | Ingest v1 events: mood, motivation, confidence, app_session, sleep, HR, session_attended, assessment_completed, user_churned | P0 |
| P01-FR-L0-07 | Normalize mood 0–10 → canonical 0–5 at L0 boundary | P0 |
| P01-FR-L0-08 | Quarantine invalid events; do not block pipeline | P1 |
| P01-FR-L0-09 | Staging finalize job at 01:30 UTC | P0 |

**Reference:** [Data-Ingestion-Layer-Production-Spec.md](../../Data-Ingestion-Layer-Production-Spec.md)

### 3.2 L2 — Feature Store

| ID | Requirement | Priority |
|----|-------------|----------|
| P01-FR-L2-01 | Compute all 34 v1 features per [L2 spec §7](../../L2-Feature-Store-Production-Spec.md) | P0 |
| P01-FR-L2-02 | Windows: 7d, 14d, 30d for means, std, slopes | P0 |
| P01-FR-L2-03 | Derived flags: `withdrawal_flag`, `sleep_mood_coupled_decline`, `cortisol_flag` (v1 proxy) | P0 |
| P01-FR-L2-04 | Meta: `days_active`, `data_completeness_score`, `system_type` | P0 |
| P01-FR-L2-05 | CORE-OM subscales: wellbeing, problems, functioning, risk | P0 |
| P01-FR-L2-06 | Feature job at 02:00 UTC; idempotent upsert | P0 |
| P01-FR-L2-07 | Export validation via `validate_dataset_columns.py` | P1 |

### 3.3 L3 — Rule-Based Scoring

| ID | Requirement | Priority |
|----|-------------|----------|
| P01-FR-L3-01 | Compute 4 pillars using Part1 category weights §7.6 | P0 |
| P01-FR-L3-02 | Compute `crs_readiness_score` using 5-category weights §6.6 | P0 |
| P01-FR-L3-03 | Compute 7 trend metrics §8 with `direction_7d` | P0 |
| P01-FR-L3-04 | Apply risk cap: `core_om_risk ≥ 0.70` → cap all scores at 40 | P0 |
| P01-FR-L3-05 | Assign bands: Low 0–33, Moderate 34–66, High 67–100 | P0 |
| P01-FR-L3-06 | Web-only renormalization when `system_type = 0` | P0 |
| P01-FR-L3-07 | Cold start: cohort prior 50 for missing blocks; confidence tier Limited | P0 |
| P01-FR-L3-08 | Persist to `scoring.user_scores_daily` | P0 |
| P01-FR-L3-09 | `crs_primary = readiness`; `crs_v2_score = null` | P0 |

**Reference:** [CRS Unified v3 §6.6, §7, §8](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)

---

## 4. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| P01-NFR-01 | Staging job completes | < 45 min for 500K users |
| P01-NFR-02 | Feature job completes | < 60 min |
| P01-NFR-03 | Scoring job completes | < 30 min |
| P01-NFR-04 | Determinism | Replay produces identical scores |
| P01-NFR-05 | Ingestion idempotency | 100% duplicate rejection |

---

## 5. Data contracts

### 5.1 L0 → L2

**Table:** `staging.user_daily_activity`  
**Spec:** Data Ingestion §11

### 5.2 L2 → L3

**Table:** `features.user_features_daily`  
**Grain:** `(user_id, as_of_date)`  
**Columns:** 34 required + meta

### 5.3 L3 output

```json
{
  "user_id": "string",
  "as_of_date": "date",
  "score_version": "crs_v3.0.0_p1",
  "crs_primary": "readiness",
  "cognitive_readiness_score": 74.5,
  "crs_readiness_score": 74.5,
  "crs_v2_score": null,
  "risk_elevated": false,
  "pillars": { "clarity_score": 73, "emotional_balance_score": 69, "resilience_score": 68, "capacity_score": 59 },
  "trends": [ "... 7 metrics ..." ],
  "confidence_tier": "Moderate"
}
```

---

## 6. Acceptance criteria

- [ ] `run_ingestion_demo.py` passes against staging schema
- [ ] `run_feature_pipeline_demo.py` produces valid 34-column row
- [ ] 10 test users: manual score verification against spreadsheet
- [ ] Risk cap test: user with `core_om_risk=0.72` → all scores ≤ 40
- [ ] Web-only user: no HRV features; scores still computed
- [ ] Batch completes by 03:00 UTC in staging environment
- [ ] Clinical sign-off on risk cap behaviour

---

## 7. Out of scope (Phase 1)

- ML outcome models and CRS v2
- Narrative API blocks (Phase 3)
- v1.1 events: games, forms, biomarkers (Phase 5)
- L1 public API GA (Phase 4)

---

## 8. Risks

| Risk | Mitigation |
|------|------------|
| Mood scale 0–10 vs 0–5 | L0 normalization §6 L2 spec |
| Missing wearable data | Null + completeness score |
| Part1 parameters not in L2 | Renormalize block weights; document gaps in §7.8 |

---

## 9. References

- [Phase 01 HLD](./Phase-01-HLD.md)
- [Data Ingestion Spec](../../Data-Ingestion-Layer-Production-Spec.md)
- [L2 Feature Store Spec](../../L2-Feature-Store-Production-Spec.md)
- [CRS Unified v3](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)
