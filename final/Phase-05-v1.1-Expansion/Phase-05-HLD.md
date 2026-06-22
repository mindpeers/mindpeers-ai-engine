# Phase 05 HLD — v1.1 Input Expansion

**Document ID:** MP-ENGINE-HLD-P05  
**Version:** 1.0.0  
**Phase:** 5

---

## 1. Expansion architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NEW SOURCE SYSTEMS (v1.1)                            │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│ Games API   │ Forms Svc   │ Lifestyle   │ Biomarker   │ NLP Worker      │
│             │             │ Tracker     │ Partner     │ (journal)       │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴────────┬────────┘
       │             │             │             │               │
       ▼             ▼             ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  NEW CONNECTORS (extend ingestion/connectors/)                           │
│  game_connector | forms_connector | lifestyle_connector | biomarker_*   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ▼
                         raw.events (existing)
                                ▼
                    staging.user_daily_activity
                     (+ new rollup fields)
                                ▼
              features.user_features_daily (v1.1 columns added)
                                ▼
              RuleScoringService (expanded category blocks)
                                ▼
              Optional: model retrain with feature_v1.1.0
```

---

## 2. New connector specifications

### 2.1 Game connector

```json
{
  "event_type": "game_session_completed",
  "payload": {
    "game_id": "memory_game",
    "session_id": "gs_123",
    "score": 85,
    "max_score": 100,
    "duration_seconds": 120,
    "accuracy": 0.92
  }
}
```

**L2:** `game_memory_score_7d` = mean normalized score over 7d

### 2.2 Forms connector

```json
{
  "event_type": "intake_form_submitted",
  "payload": {
    "form_id": "therapy_intent_v1",
    "therapy_intent": "anxiety_management",
    "primary_concern": "work_stress",
    "burnout_self_report": 7,
    "routine_disruption": true
  }
}
```

**L2:** `form_burnout_flag`, `form_work_stress_score`

### 2.3 Lifestyle connector

```json
{
  "event_type": "lifestyle_checkin",
  "payload": {
    "fatigue_level": 6,
    "exercise_minutes": 30,
    "hydration_glasses": 8,
    "nutrition_quality": 4,
    "hunger_level": 3,
    "libido_level": 5,
    "sun_exposure_minutes": 20
  }
}
```

### 2.4 Biomarker connector

```json
{
  "event_type": "biomarker_result",
  "payload": {
    "marker_type": "cortisol",
    "value": 12.5,
    "unit": "ug/dL",
    "reference_range": { "low": 5, "high": 25 },
    "collected_at": "2026-06-01T08:00:00Z"
  }
}
```

**Privacy:** Requires `biomarker_consent = true` on user profile.

---

## 3. L2 schema evolution

```sql
-- Additive columns only (feature_v1.1.0)
ALTER TABLE features.user_features_daily
  ADD COLUMN fatigue_score_7d REAL,
  ADD COLUMN exercise_days_7d INT,
  ADD COLUMN game_memory_score_7d REAL,
  ADD COLUMN form_burnout_flag INT,
  ADD COLUMN phq9_normalized_latest REAL,
  ADD COLUMN journal_sentiment_7d REAL,
  ADD COLUMN biomarker_cortisol_latest REAL;
```

**Versioning:** `feature_version = feature_v1.1.0`; scoring reads both v1 and v1.1 columns with fallback.

---

## 4. Pillar block expansion

Example — **Clarity** Tools block after Wave A:

```
Tools block (30%):
  v1:  (none)
  v1.1: game_memory_score_7d, game_connect4_score_7d, engagement patterns
  block_score = mean(available normalized params)
```

Renormalization when block partially available — same as Phase 1.

---

## 5. Lineage documentation

Maintain [Appendix G](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md) as each wave ships:

| Wave | Update Appendix G rows |
|------|------------------------|
| A | Games, lifestyle |
| B | Forms |
| C | PHQ-9, trauma |
| D | Biomarkers, therapist |
| E | Journal NLP |

---

## 6. Model retrain trigger

When `feature_v1.1.0` deployed AND ≥30 days data:

```
1. Backfill features for cohort
2. Retrain 4 outcome models
3. Compare holdout AUC vs v1 feature set
4. Promote if AUC improvement ≥ 1% or parity
5. Register outcome_models_v1.1.0
```

---

## 7. Testing strategy

| Test | Scope |
|------|-------|
| Schema validation | Each new event type |
| Connector integration | Staging against mock APIs |
| L2 column | Unit tests per new feature |
| Scoring regression | Phase 1 users unchanged when v1.1 null |
| Coverage report | Automated Part1 parameter % |

---

## 8. References

- [Phase 05 TRD](./Phase-05-TRD.md)
- [Engine Part1.docx](../../Engine%20Part1.docx)
