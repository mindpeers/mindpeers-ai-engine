# MindPeers Engine — Final TRD & HLD Package

**Version:** 1.0.0  
**Date:** 2026-06-05  
**Program:** Cognitive Readiness Engine (CRS v3 Unified)

---

## Single master document (PDF export)

**[MindPeers-Engine-Master-Production-Spec.md](./MindPeers-Engine-Master-Production-Spec.md)** — combined program spec for stakeholder review and PDF export. Consolidates architecture, requirements, all five layers, phases, and the full 70-attribute binding in one document.

## Development roadmap

| Audience | Document |
|----------|----------|
| **Product, Clinical, Leadership** | [Development-Roadmap-Stakeholder.md](./Development-Roadmap-Stakeholder.md) — plain-language timeline, user outcomes, milestones |
| **Engineering, Data, ML** | [Development-Roadmap.md](./Development-Roadmap.md) — standard schedule (11-week GA + ongoing Phase 5) |
| **4-month all-phases** | [Development-Roadmap-4Month-Accelerated.md](./Development-Roadmap-4Month-Accelerated.md) — compressed 17-week plan, **8–9 engineers** |

```bash
pandoc final/MindPeers-Engine-Master-Production-Spec.md \
  -o final/MindPeers-Engine-Master-Production-Spec.pdf \
  --toc --toc-depth=3 -V geometry:margin=1in
```

---

## Purpose

This folder contains **complete Technical Requirements Documents (TRD)** and **High-Level Design documents (HLD)** for each implementation phase of the MindPeers scoring engine.

Each phase is independently reviewable by Engineering, Data Platform, ML, Product, and Clinical stakeholders.

---

## Document index

| Phase | Timeline | TRD | HLD | Layers | Part1 |
|-------|----------|-----|-----|--------|-------|
| **0 — Master** | — | [00-Master-Program-TRD.md](./00-Master-Program-TRD.md) | [00-Master-Program-HLD.md](./00-Master-Program-HLD.md) | All | Spec: 70/70 defined |
| **1 — Foundation** | Weeks 1–4 | [Phase-01-TRD.md](./Phase-01-Foundation/Phase-01-TRD.md) | [Phase-01-HLD.md](./Phase-01-Foundation/Phase-01-HLD.md) | L0, L2, L3 (rule-based) | **Framework + 18/70 attrs** |
| **2 — ML Labels & Training** | Weeks 5–8 | [Phase-02-TRD.md](./Phase-02-ML-Labels-Training/Phase-02-TRD.md) | [Phase-02-HLD.md](./Phase-02-ML-Labels-Training/Phase-02-HLD.md) | L4 labels, model training | 18/70 |
| **3 — CRS v2 Shadow & Narrative** | Weeks 9–10 | [Phase-03-TRD.md](./Phase-03-CRS-v2-Shadow-Narrative/Phase-03-TRD.md) | [Phase-03-HLD.md](./Phase-03-CRS-v2-Shadow-Narrative/Phase-03-HLD.md) | L3 v2 shadow, L1 narrative | 18/70 + narrative |
| **4 — Production Cutover** | Week 11+ | [Phase-04-TRD.md](./Phase-04-Production-Cutover/Phase-04-TRD.md) | [Phase-04-HLD.md](./Phase-04-Production-Cutover/Phase-04-HLD.md) | L3 primary v2, L1 API GA | 18/70 at GA |
| **5 — v1.1 Expansion** | Ongoing | [Phase-05-TRD.md](./Phase-05-v1.1-Expansion/Phase-05-TRD.md) | [Phase-05-HLD.md](./Phase-05-v1.1-Expansion/Phase-05-HLD.md) | **100% Part1 attributes** | **70/70 complete** |

| **Binding (all phases)** | — | [Engine-Part1-Full-Attribute-Binding-Spec.md](./Engine-Part1-Full-Attribute-Binding-Spec.md) | 70 attrs → pillars + CRS + 7 trends |

---

## Authoritative specifications (reference)

| Document | Role |
|----------|------|
| [CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md](../CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md) | CRS, pillars, labels, trends, API |
| [Data-Ingestion-Layer-Production-Spec.md](../Data-Ingestion-Layer-Production-Spec.md) | L0 (v1.1.0 — Part1-complete events) |
| [L2-Feature-Store-Production-Spec.md](../L2-Feature-Store-Production-Spec.md) | L2 |
| [Engine-Architecture-Index.md](../Engine-Architecture-Index.md) | Layer map, schedule |
| `Engine Part1.docx` | Pillar inputs, category weights |

---

## Phase dependency graph

```
Phase 1 (L0 + L2 + L3 rule-based)
    ↓
Phase 2 (labels + ML training)
    ↓
Phase 3 (CRS v2 shadow + narrative)
    ↓
Phase 4 (production cutover)
    ↓
Phase 5 (v1.1 inputs — parallel after Phase 1)
```

Phase 5 can begin connector work in parallel with Phase 2 once L0 patterns are stable.

---

## Glossary

| Term | Definition |
|------|------------|
| **TRD** | Technical Requirements Document — what must be built, acceptance criteria |
| **HLD** | High-Level Design — how it is built, components, flows |
| **CRS v2** | ML composite: 0.4×P(recovery) + 0.2×(1−P(dropout)) + … |
| **CRS readiness** | Engine Part1 rule-based same-day score |
| **L0–L4** | Ingestion → Features → Scoring → ML → Product Engine |
