# Engine Part1 — Full Attribute Binding Specification

**Version:** 1.0.0  
**Status:** Mandatory — 100% Part1 attribute coverage for state + trajectory  
**Source:** `Engine Part1.docx`  
**Parent specs:** [CRS Unified v3](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md), [L2 Feature Store](../L2-Feature-Store-Production-Spec.md), [Data Ingestion](../Data-Ingestion-Layer-Production-Spec.md)

---

## 1. Policy — use ALL Part1 attributes

| Rule | Requirement |
|------|-------------|
| **P1** | Every attribute listed in Engine Part1 **must** be ingested, featureized, and bound to **at least one state score** (CRS readiness and/or pillar). |
| **P2** | Every attribute marked **trajectory-relevant** below **must** contribute to **at least one trend metric** (§8) via level, slope, or volatility feature. |
| **P3** | Missing data → **renormalize weights within category block** — never drop the attribute from the spec. |
| **P4** | `core_om_risk` applies **risk cap** to all state and trajectory display scores (§7.7). |
| **P5** | Implementation waves (Phase 1 → 5) deliver attributes incrementally; **spec coverage is 100% from day one**. |

**State layer** = CRS readiness + 4 pillars (Clarity, Emotional Balance, Resilience, Capacity).  
**Trajectory layer** = 7 trend metrics + direction arrows.

---

## 2. Canonical attribute registry (complete)

| ID | Part1 name | L0 event | L2 feature (target) | Phase |
|----|------------|----------|---------------------|-------|
| A01 | CORE-OM Overall Score | `assessment_completed` | `core_om_total_norm` | 1 |
| A02 | CORE-OM Life Functioning | `assessment_completed` | `core_om_functioning` | 1 |
| A03 | CORE-OM Problems | `assessment_completed` | `core_om_problems` | 1 |
| A04 | CORE-OM Wellbeing | `assessment_completed` | `core_om_wellbeing` | 1 |
| A05 | CORE-OM Risk | `assessment_completed` | `core_om_risk` | 1 |
| A06 | CORE-OM Delta / Previous | `assessment_completed` | `core_om_delta_30d` | 1 |
| A07 | Anxiety Score | `assessment_completed` GAD-7 | `gad7_normalized_latest` | 1 |
| A08 | Depression Score | `assessment_completed` PHQ-9 | `phq9_normalized_latest` | 5 |
| A09 | Trauma Score | `assessment_completed` PTSD | `trauma_score_latest` | 5 |
| A10 | ADHD Assessment | `assessment_completed` ASRS | `adhd_score_latest` | 5 |
| A11 | Sleep | `sleep_session` | `sleep_avg_7d`, `sleep_slope_7d` | 1 |
| A12 | Fatigue | `lifestyle_checkin` | `fatigue_score_7d` | 5 |
| A13 | HRV | `heart_rate_daily` / wearable | `hrv_avg`, `hrv_trend` | 1 |
| A14 | Pulse Rate | `heart_rate_daily` | `resting_hr_avg`, `resting_hr_trend` | 5 |
| A15 | Exercise | `lifestyle_checkin` | `exercise_days_7d`, `exercise_minutes_7d` | 5 |
| A16 | Nutrition | `lifestyle_checkin` | `nutrition_score_7d` | 5 |
| A17 | Hydration | `lifestyle_checkin` | `hydration_score_7d` | 5 |
| A18 | Hunger | `lifestyle_checkin` | `hunger_level_7d` | 5 |
| A19 | Sun Exposure | `lifestyle_checkin` | `sun_exposure_minutes_7d` | 5 |
| A20 | Libido | `lifestyle_checkin` | `libido_level_14d` | 5 |
| A21 | Cortisol | `biomarker_result` | `biomarker_cortisol_latest` | 5 |
| A22 | Thyroid / TSH | `biomarker_result` | `biomarker_tsh_latest` | 5 |
| A23 | Blood Sugar | `biomarker_result` | `biomarker_glucose_latest` | 5 |
| A24 | Vitamin D | `biomarker_result` | `biomarker_vitd_latest` | 5 |
| A25 | HbA1c | `biomarker_result` | `biomarker_hba1c_latest` | 5 |
| A26 | Weight Change | `biomarker_result` | `weight_delta_90d` | 5 |
| A27 | Mood Check-In | `mood_checkin` | `mood_avg_14d`, `mood_volatility_14d`, `mood_slope_7d` | 1 |
| A28 | Motivation Check-In | `motivation_checkin` | `motivation_avg_14d`, `motivation_slope_7d` | 1 |
| A29 | Confidence Check-In | `confidence_checkin` | `confidence_avg_14d`, `confidence_slope_7d` | 1 |
| A30 | Memory Game | `game_session_completed` | `game_memory_score_7d`, `game_memory_slope_7d` | 5 |
| A31 | Connect Four | `game_session_completed` | `game_connect4_score_7d` | 5 |
| A32 | Whack A Mole | `game_session_completed` | `game_whack_score_7d`, `game_frustration_proxy` | 5 |
| A33 | Journaling tone/themes | `journal_features_computed` | `journal_sentiment_7d`, `journal_stress_theme_flag` | 5 |
| A34 | Blank Slate Journal | `journal_entry` | `journal_blank_slate_sentiment_7d` | 5 |
| A35 | Letter to Self | `journal_entry` | `journal_letter_self_sentiment_7d` | 5 |
| A36 | Gratitude Journal | `journal_entry` | `journal_gratitude_sentiment_7d` | 5 |
| A37 | App engagement | `app_session` | `engagement_rate_7d`, `engagement_slope_7d` | 1 |
| A38 | Support-seeking frequency | `app_session`, therapy events | `support_seeking_rate_30d` | 5 |
| A39 | Guides / content usage | `content_viewed` | `guide_usage_rate_30d` | 5 |
| A40 | Focus app behaviour | `app_session` | `focus_session_rate_7d` | 5 |
| A41 | Completion / drop-off | `app_session` | `task_completion_rate_7d`, `dropoff_rate_7d` | 5 |
| A42 | Check-in drop-off | check-in events | `checkin_completion_rate_7d` | 5 |
| A43 | Session booking / attendance | `session_attended`, `session_missed` | `therapy_attendance_rate` | 1 |
| A44 | Therapy intent | `intake_form_submitted` | `form_therapy_intent_score` | 5 |
| A45 | Primary concern | `intake_form_submitted` | `form_primary_concern_severity` | 5 |
| A46 | Free-text concern | `intake_form_submitted` | `form_concern_nlp_severity` | 5 |
| A47 | Work-stress pattern | `intake_form_submitted` | `form_work_stress_score` | 5 |
| A48 | Routine disruption | `intake_form_submitted` | `form_routine_disruption_flag` | 5 |
| A49 | Check-in completion (forms) | `intake_form_submitted` | `form_checkin_burden_score` | 5 |
| A50 | Overthinking themes | `intake_form_submitted` | `form_overthinking_score` | 5 |
| A51 | Decision fatigue | `intake_form_submitted` | `form_decision_fatigue_score` | 5 |
| A52 | Brain fog | `intake_form_submitted` | `form_brain_fog_score` | 5 |
| A53 | Work-pressure patterns | `intake_form_submitted` | `form_work_pressure_score` | 5 |
| A54 | Emotional triggers | `intake_form_submitted` | `form_emotional_triggers_score` | 5 |
| A55 | Relationship patterns | `intake_form_submitted` | `form_relationship_stress_score` | 5 |
| A56 | Self-talk themes | journal + forms NLP | `form_self_talk_score` | 5 |
| A57 | Crisis / risk markers (forms) | `intake_form_submitted` | `form_crisis_marker_flag` | 5 |
| A58 | Pattern improvement | `intake_form_submitted` | `form_coping_improvement_score` | 5 |
| A59 | Coping behaviour | `intake_form_submitted` | `form_coping_score` | 5 |
| A60 | Trigger reduction | `intake_form_submitted` | `form_trigger_reduction_score` | 5 |
| A61 | Burnout patterns | `intake_form_submitted` | `form_burnout_score` | 5 |
| A62 | Work functioning concerns | `intake_form_submitted` | `form_work_functioning_score` | 5 |
| A63 | Daily routine difficulty | `intake_form_submitted` | `form_routine_difficulty_score` | 5 |
| A64 | Self-reported overwhelm | `intake_form_submitted` | `form_overwhelm_score` | 5 |
| A65 | Missed check-ins (forms) | staging rollup | `missed_checkin_days_7d` | 5 |
| A66 | Session missed/cancelled | `session_missed` | `therapy_missed_rate_30d` | 5 |
| A67 | Time since last session | therapy events | `days_since_last_session` | 5 |
| A68 | Therapist availability | therapist sheet sync | `therapist_availability_score` | 5 |
| A69 | Affordability / fee continuity | therapist sheet sync | `therapy_affordability_score` | 5 |
| A70 | Mode / language match | therapist sheet sync | `therapist_match_score` | 5 |

**Total: 70 canonical attributes** (39 Part1 table rows + 31 forms/therapist/behavioural expansions from weight tables).

---

## 3. State binding — which attributes feed which scores

Legend: **●** = Part1 Table explicitly lists this attribute for that score.

### 3.1 CRS readiness (Table 1 + Table 6 categories)

| Category | Weight | Attributes (all must be used) |
|----------|--------|------------------------------|
| Assessment 30% | A01–A10 | |
| Lifestyle + Biomarker 30% | A11–A18, A21–A23 | |
| Tools / Behavioural 15% | A27–A29, A30–A31, A37 | |
| Forms 15% | A44–A49 | |
| Therapist 10% | A43, A66–A70 | |

### 3.2 Clarity (Table 2 + Table 7)

| Category | Weight | Attributes |
|----------|--------|------------|
| Tools 30% | A30–A31, A40–A41 | |
| Lifestyle 25% | A11–A14, A16–A18, A22–A24 | |
| Assessment 20% | A02, A03, A07, A10 | |
| Forms 15% | A50–A53 | |
| Therapist 10% | A66–A70 | |

### 3.3 Emotional Balance (Table 3 + Table 8)

| Category | Weight | Attributes |
|----------|--------|------------|
| Assessment 35% | A04, A03, A05, A07–A09 | |
| Forms 20% | A54–A57 | |
| Tools 20% | A27–A29, A33–A36, A32, A42 | |
| Lifestyle 20% | A11–A12, A20–A23 | |
| Therapist 5% | A66–A70 | |

### 3.4 Resilience (Table 4 + Table 9)

| Category | Weight | Attributes |
|----------|--------|------------|
| Lifestyle 30% | A13, A11, A15–A19, A21–A24 | |
| Assessment 25% | A06, A02, A05 | |
| Forms 20% | A58–A60 | |
| Tools 15% | A36, A37–A39 | |
| Therapist 10% | A66–A70 | |

### 3.5 Capacity (Table 5 + Table 10)

| Category | Weight | Attributes |
|----------|--------|------------|
| Assessment 30% | A02, A01, A03, A05 | |
| Lifestyle 30% | A11–A18, A13–A14, A22–A26 | |
| Forms 20% | A61–A65 | |
| Therapist 10% | A43, A66–A70 | |
| Tools 10% | A28–A29, A37, A40 (per therapist sheet cross-ref) | |

---

## 4. Trajectory binding — all attributes → trends

Every trajectory-relevant attribute contributes via **level (L)**, **slope (S)**, or **volatility (V)**.

| Trend | Primary attributes | Feature form |
|-------|-------------------|--------------|
| **Recovery Readiness** | A11, A13, A12, A15, A19, A21, A24, A06 | L: sleep, HRV, fatigue⁻; S: sleep_slope, hrv_trend, core_om_delta |
| **Stress Load** | A07–A09, A13–A14, A21–A23, A27 volatility | L: gad7, cortisol, pulse; S: hrv_trend⁻, mood_volatility |
| **Sleep Consistency** | A11, A12 | V: sleep_duration_variance, bedtime_variance |
| **Energy Rhythm** | A12, A15–A18, A23, A28, A37 | L + S: fatigue, exercise, nutrition, motivation_slope, engagement_slope |
| **Emotional Stability** | A27–A29, A07–A09, A33–A36, A54 | V: mood_volatility; S: mood_slope, confidence_slope, journal_sentiment_slope |
| **Motivation Momentum** | A28, A37–A39, A42, A61 | S: motivation_slope, engagement_slope, checkin_completion_slope |
| **Cognitive Momentum** | A30–A31, A02, A12, A50–A52, A10 | S: game_memory_slope, functioning_trend, brain_fog_trend |

### 4.1 Trajectory inclusion matrix (attribute → trends)

| ID | Trends fed |
|----|------------|
| A01–A06 | Recovery Readiness (A06), Cognitive Momentum (A02), Stress Load |
| A07–A09 | Stress Load, Emotional Stability |
| A10 | Cognitive Momentum |
| A11 | Recovery Readiness, Sleep Consistency, Energy Rhythm, all pillars |
| A12 | Recovery Readiness⁻, Energy Rhythm, Stress Load, Cognitive Momentum⁻ |
| A13–A14 | Recovery Readiness, Stress Load |
| A15–A19 | Recovery Readiness, Energy Rhythm, Resilience |
| A20 | Emotional Stability |
| A21–A26 | Stress Load, Energy Rhythm, Emotional Stability |
| A27–A29 | Emotional Stability, Motivation Momentum, Energy Rhythm |
| A30–A32 | Cognitive Momentum, Emotional Stability (A32) |
| A33–A36 | Emotional Stability, Resilience (A36) |
| A37–A42 | Motivation Momentum, Energy Rhythm |
| A43–A70 | Motivation Momentum, Capacity context; therapist attrs → Engagement trends |

---

## 5. Computation rules

### 5.1 State score (per pillar / CRS)

```
FOR each category block B in score S:
  params = all attributes assigned to B (section 3)
  FOR each param p in params:
    value_p = normalize(L2_feature_p)  // 0-100
  block_score_B = mean(value_p where p is non-null)
  renormalize category weights over blocks with data
score_S = Σ weight_B × block_score_B
score_S = apply_risk_cap(score_S, A05)
```

### 5.2 Trend score (per trend T)

```
FOR each trend T:
  attrs = trajectory bindings (section 4.1)
  contributions = []
  FOR each attr a in attrs:
    f = level and/or slope and/or volatility feature for a
    contributions.append(weight_a × normalize(f))
trend_T = weighted_sum(contributions)
direction_7d = compute_direction(trend_T, trend_T_7d_ago)
```

### 5.3 Expanded trend weights (Part1-complete v3.1)

When all attributes available, trend formulas **upgrade** from minimal v1 (sleep/HRV only) to full Part1 bindings. See [CRS Unified v3 §8.9](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md).

---

## 6. Implementation waves (100% coverage path)

| Wave | Attributes | Phases |
|------|------------|--------|
| W1 Core clinical + check-ins | A01–A07, A11, A13, A27–A29, A37, A43 | Phase 1 |
| W2 Lifestyle + games | A12, A14–A20, A30–A32 | Phase 5A |
| W3 Forms (all) | A44–A65 | Phase 5B |
| W4 Biomarkers | A21–A26 | Phase 5C |
| W5 Journal NLP | A33–A36, A56 | Phase 5D |
| W6 Therapist sheet | A66–A70 | Phase 5E |
| W7 Behavioural app | A38–A42 | Phase 5A |

**Gate:** Program complete when all 70 attributes have L0 + L2 + state binding + trajectory binding (where applicable).

---

## 7. Acceptance criteria

- [ ] Registry §2: 70/70 attributes have L0 event type defined
- [ ] Registry §2: 70/70 attributes have target L2 column in spec
- [ ] Section 3: every attribute appears in ≥1 state score category
- [ ] Section 4: every trajectory-relevant attribute feeds ≥1 trend
- [ ] Risk cap tested with A05 ≥ 0.70
- [ ] Missing-attribute renormalization tested per block
- [ ] `feature_version = feature_v2.0.0` when W1–W7 complete

---

## 8. References

- [CRS Unified v3 §7.6, §7.9, §8.9](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)
- [Phase 05 TRD](./Phase-05-v1.1-Expansion/Phase-05-TRD.md) (updated for 100% coverage)
- [Engine Part1.docx](../Engine%20Part1.docx)
