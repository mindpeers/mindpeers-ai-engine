# Phase 03 TRD — CRS v2 Shadow & Narrative

**Document ID:** MP-ENGINE-TRD-P03  
**Version:** 1.0.0  
**Phase:** 3 — CRS v2 Shadow & Narrative  
**Timeline:** Weeks 9–10  
**Prerequisite:** Phase 02 exit criteria met

---

## 1. Phase objective

Integrate **CRS v2 ML composite** alongside rule-based readiness in **shadow mode**, and ship **narrative API** answering Engine Part1's five questions.

Users see both scores internally; product validates before Phase 4 cutover.

---

## 2. Functional requirements

### 2.1 CRS v2 composite

| ID | Requirement | Priority |
|----|-------------|----------|
| P03-FR-CRS-01 | `CRS = 0.40×P(recovery) + 0.20×(1−P(dropout)) + 0.20×(1−P(engagement_loss)) + 0.20×(1−P(relapse))` | P0 |
| P03-FR-CRS-02 | Scale to 0–100; persist as `crs_v2_score` | P0 |
| P03-FR-CRS-03 | Keep `crs_readiness_score` from Phase 1 | P0 |
| P03-FR-CRS-04 | `crs_primary = readiness` (shadow — not v2 yet) | P0 |
| P03-FR-CRS-05 | `cognitive_readiness_score` = readiness (unchanged for users) | P0 |
| P03-FR-CRS-06 | Expose both scores in internal/staging API | P0 |
| P03-FR-CRS-07 | `crs_breakdown` with four contribution terms | P0 |
| P03-FR-CRS-08 | Apply risk cap to both v2 and readiness | P0 |

### 2.2 Distribution comparison (shadow analytics)

| ID | Requirement | Priority |
|----|-------------|----------|
| P03-FR-SHD-01 | Daily report: mean/std CRS v2 vs readiness | P0 |
| P03-FR-SHD-02 | Correlation by cohort segment | P1 |
| P03-FR-SHD-03 | Flag users with |v2 − readiness| > 20 | P1 |
| P03-FR-SHD-04 | Dashboard for Product/Clinical review | P1 |

### 2.3 Narrative API (five questions)

| ID | Requirement | Priority |
|----|-------------|----------|
| P03-FR-NAR-01 | `narrative.where_now` from pillars + CRS band | P0 |
| P03-FR-NAR-02 | `narrative.why_summary` from SHAP → Part1 categories | P0 |
| P03-FR-NAR-03 | `narrative.awareness_flags` from declining trends | P0 |
| P03-FR-NAR-04 | `narrative.risk` from relapse_prob + core_om_risk | P0 |
| P03-FR-NAR-05 | `narrative.next_actions` from L1 pattern matches | P0 |
| P03-FR-NAR-06 | Risk-elevated override copy §10.4 | P0 |
| P03-FR-NAR-07 | `score_meanings` for all 5 scores | P0 |

### 2.4 L1 pattern engine (minimal)

| ID | Requirement | Priority |
|----|-------------|----------|
| P03-FR-PAT-01 | Evaluate patterns: motivation_decline_warning, risk_watch, engagement_drop | P0 |
| P03-FR-PAT-02 | Pattern cards in API response | P0 |

---

## 3. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| P03-NFR-01 | Narrative generation | < 50ms per user (template-based) |
| P03-NFR-02 | No LLM hallucination of scores | Templates only; read snapshot |
| P03-NFR-03 | A/B logging | Both scores logged for analysis |

---

## 4. API additions (staging)

```json
{
  "crs_primary": "readiness",
  "cognitive_readiness_score": 74.5,
  "crs_readiness_score": 74.5,
  "crs_v2_score": 81.2,
  "crs_breakdown": {
    "recovery_potential": 32.8,
    "retention_probability": 15.0,
    "engagement_stability": 16.4,
    "relapse_avoidance": 17.0
  },
  "narrative": { "...": "..." },
  "shadow_analytics": {
    "v2_minus_readiness": 6.7
  }
}
```

---

## 5. Acceptance criteria

- [ ] CRS v2 formula matches manual calculation for 20 test users
- [ ] Product reviews shadow distribution report — no blocking anomalies
- [ ] Clinical reviews risk narrative override
- [ ] Narrative QA: 50 snapshot copy reviews passed
- [ ] Patterns fire correctly on test archetypes (§3.3 CRS spec)
- [ ] Risk cap suppresses positive copy when risk ≥ 0.70

---

## 6. Out of scope

- `crs_primary = v2` switch (Phase 4)
- Public production API GA
- LLM-generated narrative (template only in Phase 3)

---

## 7. References

- [Phase 03 HLD](./Phase-03-HLD.md)
- [CRS Unified v3 §6.1, §10.4](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)
