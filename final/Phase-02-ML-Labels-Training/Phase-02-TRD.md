# Phase 02 TRD — ML Labels & Model Training

**Document ID:** MP-ENGINE-TRD-P02  
**Version:** 1.0.0  
**Phase:** 2 — ML Labels & Training  
**Timeline:** Weeks 5–8  
**Prerequisite:** Phase 01 exit criteria met

---

## 1. Phase objective

Build the **offline ML foundation** for CRS v2:

- Clinical and behavioral **label generation** (§4.3)
- **Training datasets** from historical snapshots
- **Four outcome models** trained, evaluated, registered
- Batch **inference pipeline** (not yet primary CRS)

---

## 2. Functional requirements

### 2.1 Label generation service

| ID | Requirement | Priority |
|----|-------------|----------|
| P02-FR-LBL-01 | Implement `ml.label_generation_daily` batch job | P0 |
| P02-FR-LBL-02 | Recovery/relapse: CORE-OM pairing T vs [T+21,T+45] | P0 |
| P02-FR-LBL-03 | Apply R1–R4, L1–L5 rules with `label_v2.0.0` | P0 |
| P02-FR-LBL-04 | Censoring: null labels when no follow-up | P0 |
| P02-FR-LBL-05 | Dropout: `user_churned`, inactivity, terminated | P0 |
| P02-FR-LBL-06 | Engagement loss: 50% relative drop at T+14 | P0 |
| P02-FR-LBL-07 | Store in `ml.training_labels` with audit columns | P0 |
| P02-FR-LBL-08 | GAD-7 secondary recovery path when CORE-OM missing | P1 |

**Reference:** [CRS Unified v3 §4.3](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)

### 2.2 Training data assembly

| ID | Requirement | Priority |
|----|-------------|----------|
| P02-FR-TRN-01 | Join `features.user_features_daily` + `ml.training_labels` on `(user_id, snapshot_date)` | P0 |
| P02-FR-TRN-02 | Exclude censored rows from recovery/relapse training | P0 |
| P02-FR-TRN-03 | Minimum 90 days history; target ≥ 10K non-censored clinical rows | P0 |
| P02-FR-TRN-04 | Stratified split: 70/15/15 train/val/holdout by user_id | P0 |
| P02-FR-TRN-05 | Class weights for imbalanced labels | P0 |

### 2.3 Outcome models

| ID | Model | Target | Algorithm | Priority |
|----|-------|--------|-----------|----------|
| P02-FR-MDL-01 | `recovery_model_v1` | `recovery_label` | LightGBM/XGBoost | P0 |
| P02-FR-MDL-02 | `relapse_model_v1` | `relapse_label` | LightGBM/XGBoost | P0 |
| P02-FR-MDL-03 | `dropout_model_v1` | `dropout_label` | LightGBM/XGBoost | P0 |
| P02-FR-MDL-04 | `engagement_loss_model_v1` | `engagement_loss_label` | LightGBM/XGBoost | P0 |

### 2.4 Model quality gates

| Model | Metric | Minimum |
|-------|--------|---------|
| recovery | AUC-ROC | 0.70 |
| recovery | AUC-PR | 0.35 |
| relapse | AUC-PR | 0.25 |
| dropout | AUC-ROC | 0.72 |
| engagement_loss | AUC-ROC | 0.68 |

### 2.5 Inference pipeline (batch)

| ID | Requirement | Priority |
|----|-------------|----------|
| P02-FR-INF-01 | Daily inference at 02:30 UTC on active users | P0 |
| P02-FR-INF-02 | Output: 4 probabilities per user-day | P0 |
| P02-FR-INF-03 | Store SHAP top-5 features per model | P1 |
| P02-FR-INF-04 | Register `model_bundle_version` in MLflow/registry | P0 |
| P02-FR-INF-05 | Do NOT set `crs_primary=v2` yet (Phase 3) | P0 |

---

## 3. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| P02-NFR-01 | Label job idempotent | Upsert on `(user_id, snapshot_date, label_version)` |
| P02-NFR-02 | Training reproducible | Fixed seed + pinned feature_version |
| P02-NFR-03 | Inference latency | < 2h for 500K users |
| P02-NFR-04 | Censoring rate report | Monthly; alert if > 40% |

---

## 4. Data schema — `ml.training_labels`

| Column | Type | Description |
|--------|------|-------------|
| user_id | TEXT | |
| snapshot_date | DATE | Anchor T |
| recovery_label | INT NULL | 0/1/null |
| relapse_label | INT NULL | 0/1/null |
| dropout_label | INT | 0/1 |
| engagement_loss_label | INT | 0/1 |
| label_version | TEXT | `label_v2.0.0` |
| label_confidence | TEXT | primary/secondary |
| label_censored_reason | TEXT | nullable |
| recovery_criteria_met | TEXT[] | R1–R4 |
| relapse_criteria_met | TEXT[] | L1–L5 |
| computed_at | TIMESTAMPTZ | |

---

## 5. Acceptance criteria

- [ ] Label job produces expected labels for §2.2.6 worked examples (users 1001–1005)
- [ ] Clinical sign-off on MCID thresholds
- [ ] All 4 models pass quality gates on holdout
- [ ] Model registry has full lineage: data version, label version, hyperparams
- [ ] Inference job writes probabilities; CRS v2 computable but not primary
- [ ] Censoring rate documented for cohort

---

## 6. Out of scope

- CRS v2 as primary headline (Phase 4)
- Narrative generation (Phase 3)
- Real-time inference API
- Auto-retrain loop (Phase 4 monitoring only)

---

## 7. References

- [Phase 02 HLD](./Phase-02-HLD.md)
- [CRS Unified v3 §4.3, §5](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)
- [Data Ingestion §12](../../Data-Ingestion-Layer-Production-Spec.md)
