# Phase 04 TRD — Production Cutover & L1 API GA

**Document ID:** MP-ENGINE-TRD-P04  
**Version:** 1.0.0  
**Phase:** 4 — Production Cutover  
**Timeline:** Week 11+  
**Prerequisite:** Phase 03 exit + clinical/product sign-off

---

## 1. Phase objective

Promote **CRS v2 as primary headline score**, launch **production L1 API**, and operationalize **monitoring, rollback, and governance**.

---

## 2. Cutover requirements

### 2.1 CRS primary switch

| ID | Requirement | Priority |
|----|-------------|----------|
| P04-FR-CRS-01 | Set `crs_primary = v2` when `data_maturity_stage = full` AND models loaded | P0 |
| P04-FR-CRS-02 | `cognitive_readiness_score` = `crs_v2_score` after cutover | P0 |
| P04-FR-CRS-03 | Continue exposing `crs_readiness_score` as secondary | P0 |
| P04-FR-CRS-04 | Footnote in API: `score_interpretation` field explaining v2 vs readiness | P1 |
| P04-FR-CRS-05 | Rollback flag: `FORCE_CRS_PRIMARY=readiness` env override | P0 |

**Maturity rules (§13):**

| Tier | CRS primary |
|------|-------------|
| Limited (≤7 days or completeness < 0.4) | readiness |
| Moderate (≤30 days or completeness < 0.7) | readiness |
| High (>30 days AND completeness ≥ 0.7) | v2 |

### 2.2 L1 API — production

| ID | Requirement | Priority |
|----|-------------|----------|
| P04-FR-API-01 | `GET /users/{id}/engine/report` — production SLA | P0 |
| P04-FR-API-02 | `GET /users/{id}/engine/trends/{trend_id}/series` | P0 |
| P04-FR-API-03 | Auth: OAuth2 / JWT; user scoped | P0 |
| P04-FR-API-04 | Response matches CRS Unified v3 §10 | P0 |
| P04-FR-API-05 | Cache snapshot read (Redis) TTL 1h | P1 |
| P04-FR-API-06 | Rate limit: 100 req/min per user | P0 |

### 2.3 Snapshot persistence

| ID | Requirement | Priority |
|----|-------------|----------|
| P04-FR-SNAP-01 | `user_engine_snapshot` table at 03:05 UTC | P0 |
| P04-FR-SNAP-02 | API reads snapshot only — never computes on request path | P0 |
| P04-FR-SNAP-03 | `computed_at`, all version fields on every row | P0 |

### 2.4 Monitoring & governance

| ID | Requirement | Priority |
|----|-------------|----------|
| P04-FR-MON-01 | KL divergence alert on CRS distribution | P0 |
| P04-FR-MON-02 | Model AUC weekly eval job | P0 |
| P04-FR-MON-03 | Label rate drift alert ±5% | P0 |
| P04-FR-MON-04 | Runbook: model rollback, score_version hotfix | P0 |
| P04-FR-MON-05 | Quarterly clinical review of thresholds | P0 |

---

## 3. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| P04-NFR-01 | API availability | 99.9% |
| P04-NFR-02 | API p99 latency | < 200ms |
| P04-NFR-03 | Batch SLA | Complete by 03:30 UTC |
| P04-NFR-03 | Rollback time | < 15 min to previous model_bundle |

---

## 4. Cutover checklist

- [ ] Shadow analytics signed off (Phase 3)
- [ ] Clinical sign-off on CRS v2 as headline
- [ ] Product sign-off on narrative copy
- [ ] Load test 10K RPM passed
- [ ] On-call runbook published
- [ ] `score_version = crs_v3.0.0` deployed
- [ ] Feature flags: `crs_primary` per maturity tier
- [ ] Rollback drill completed

---

## 5. Rollback procedure

```
1. Set FORCE_CRS_PRIMARY=readiness in scoring service
2. OR rollback model_bundle_version pointer in registry
3. Rerun L3 scoring job for affected date
4. Invalidate Redis snapshot cache
5. Verify API returns readiness as headline
```

---

## 6. Out of scope

- v1.1 input expansion (Phase 5)
- LLM chat integration
- Real-time score updates

---

## 7. References

- [Phase 04 HLD](./Phase-04-HLD.md)
- [CRS Unified v3 §13, §14, §15](../../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md)
