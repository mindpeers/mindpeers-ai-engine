# MindPeers Engine — Architecture Index

**Version:** 1.0.0  
**Last updated:** 2026-06-05

Single entry point for all production specifications, implementation artifacts, and layer dependencies.

---

## Layer map

```
┌─────────────────────────────────────────────────────────────────────────┐
│ L1 — Product Engine          Dashboard, patterns, recommendations, API  │
│ Doc: ENGINE-POC Part 6–7                                                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↑ user_engine_snapshot
┌───────────────────────────────▼─────────────────────────────────────────┐
│ L3 — Scoring Service         CRS, pillars, trends, drivers, confidence  │
│ Doc: CRS-Calculation-and-Trends-Production-Spec.md                      │
│      ENGINE-POC Part 5 (rule-based v1)                                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↑ feature row / day
┌───────────────────────────────▼─────────────────────────────────────────┐
│ L2 — Feature Store           7d/14d/30d windows, slopes, flags, labels    │
│ Doc: ENGINE-POC Part 4                                                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↑ staging.user_daily_activity
┌───────────────────────────────▼─────────────────────────────────────────┐
│ L0 — Data Ingestion          Connectors, validate, raw, staging          │
│ Doc: Data-Ingestion-Layer-Production-Spec.md                            │
│ Code: ingestion/  schemas/ingestion/                                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↑
                         Source systems (app, wearable, therapy, assessments)

┌─────────────────────────────────────────────────────────────────────────┐
│ L4 — Intelligence Router     Intent → ML? → LLM (uses L1 snapshot)      │
│ Doc: ENGINE-POC Part 1–2, poc_extract.txt                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Document registry

| Layer | Primary spec | Status | Key outputs |
|-------|-------------|--------|-------------|
| **Roadmap (4-month all phases)** | [final/Development-Roadmap-4Month-Accelerated.md](./final/Development-Roadmap-4Month-Accelerated.md) | **8–9 engineers**, 17 weeks, 70/70 Part1 |
| **Roadmap (stakeholder)** | [final/Development-Roadmap-Stakeholder.md](./final/Development-Roadmap-Stakeholder.md) | **Non-technical** — user outcomes, milestones, FAQ |
| **Roadmap (technical)** | [final/Development-Roadmap.md](./final/Development-Roadmap.md) | **Development schedule** — phases, gates, team matrix |
| **Program** | [final/MindPeers-Engine-Master-Production-Spec.md](./final/MindPeers-Engine-Master-Production-Spec.md) | **Single combined master spec (PDF export)** |
| **Program** | [final/README.md](./final/README.md) | **TRD + HLD per phase** | Phase 01–05 TRD/HLD, master program docs |
| **Part1 binding** | [final/Engine-Part1-Full-Attribute-Binding-Spec.md](./final/Engine-Part1-Full-Attribute-Binding-Spec.md) | **Mandatory 100%** | 70 attributes → state + trajectory |
| **L0** | [Data-Ingestion-Layer-Production-Spec.md](./Data-Ingestion-Layer-Production-Spec.md) | Production spec | Raw events, staging rollups |
| **L2** | [L2-Feature-Store-Production-Spec.md](./L2-Feature-Store-Production-Spec.md) | Production spec | 34-column feature row, flags, meta |
| **L2 (POC)** | [ENGINE-POC-COMPLETE-DOCUMENTATION.md](./ENGINE-POC-COMPLETE-DOCUMENTATION.md) Part 4 | POC closed | Registry reference |
| **L3** | [CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md](./CRS-Calculation-and-Trends-Production-Spec-Unified-v3.md) | **Unified production spec (v3)** — CRS v2 + Engine Part1 + labels + trends | CRS, pillars, narrative, risk cap |
| **L3 (v2 ref)** | [CRS-Calculation-and-Trends-Production-Spec.md](./CRS-Calculation-and-Trends-Production-Spec.md) | Reference (v2 only) | ML labels, trends without Part1 integration |
| **L3 v1** | ENGINE-POC Part 5 | POC closed | Rule-based CRS (25% pillars) |
| **L1** | ENGINE-POC Part 6–7 | POC closed | Snapshot API, patterns |
| **Program** | ENGINE-POC (full) | Consolidated | Gaps G1–G15, roadmap |
| **Alignment** | PRD-POC-Alignment (merged into ENGINE-POC) | Reference | PRD ↔ data mapping |

---

## Implementation artifacts

| Path | Purpose |
|------|---------|
| [schemas/ingestion/](./schemas/ingestion/) | JSON Schema for L0 events (envelope + payloads) |
| [schemas/ingestion/registry.json](./schemas/ingestion/registry.json) | event_type → schema mapping |
| [ingestion/](./ingestion/) | Python connector stubs, validator, staging builder |
| [features/](./features/) | L2 window computations (optional reference implementation) |
| [scripts/run_ingestion_demo.py](./scripts/run_ingestion_demo.py) | End-to-end L0 demo (optional) |
| [scripts/run_feature_pipeline_demo.py](./scripts/run_feature_pipeline_demo.py) | L2 feature demo (optional) |
| [scripts/validate_ingestion_event.py](./scripts/validate_ingestion_event.py) | Validate event JSON against schemas |
| [scripts/validate_dataset_columns.py](./scripts/validate_dataset_columns.py) | Validate L2 export columns |
| [scripts/generate_sample_dataset.py](./scripts/generate_sample_dataset.py) | Generate Engine-POC-Sample-Dataset.xlsx |
| [Engine-POC-Sample-Dataset.xlsx](./Engine-POC-Sample-Dataset.xlsx) | Sample L2 + snapshot columns |

---

## Daily batch schedule (UTC)

| Time | Layer | Job |
|------|-------|-----|
| Continuous | L0 | App event stream → raw |
| Every 6h | L0 | Wearable sync |
| **01:30** | **L0** | Staging finalize (`user_daily_activity`) |
| **02:00** | **L2** | Feature computation |
| **02:30** | **L4 ML** | Outcome model inference (CRS v2) |
| **02:45** | **L3** | CRS, pillars, trends |
| **03:00** | **L1** | Pattern evaluation |
| **03:05** | **L1** | Persist `user_engine_snapshot` |

---

## Data contracts by layer

### L0 → L2 handoff

**Table:** `staging.user_daily_activity`  
**Grain:** `(user_id, local_date)`  
**Spec:** [Data Ingestion §11](./Data-Ingestion-Layer-Production-Spec.md#11-staging--l2-handoff)

### L2 feature row

**Grain:** `(user_id, as_of_date)`  
**Columns:** 34 required v1 — see [ENGINE-POC Part 8](./ENGINE-POC-COMPLETE-DOCUMENTATION.md)

### L3 engine snapshot

**Table:** `user_engine_snapshot`  
**Spec:** ENGINE-POC Part 6 + [CRS spec §10](./CRS-Calculation-and-Trends-Production-Spec.md#10-api-contracts-and-response-examples)

---

## CRS versions

| Version | Formula | Doc |
|---------|---------|-----|
| **v1** | `0.25 × (Clarity + Balance + Resilience + Capacity)` | ENGINE-POC L3 §7.6 |
| **v2** | `0.4×P(recovery) + 0.2×(1−P(dropout)) + …` | CRS spec §6 |

Migration: shadow v2 alongside v1, then switch primary (CRS spec §15).

---

## Quick start (developers)

```bash
# L0 — run ingestion demo
python scripts/run_ingestion_demo.py

# L0 — validate an event file
python scripts/validate_ingestion_event.py --sample mood_checkin

# L2 — feature pipeline demo (optional)
python scripts/run_feature_pipeline_demo.py

# L2 — validate feature export
python scripts/validate_dataset_columns.py Engine-POC-Sample-Dataset.xlsx
```

---

## Source product artifacts (reference)

| File | Role |
|------|------|
| `Engine Document.docx` | PRD |
| `Contextuliazation.xlsx` | Pillar / trend input map |
| `Data contexualization Datasets.xlsx` | Dataset column definitions |
| `Engine Part1.docx` | Pillar input catalog, category weights, product screens |
| `CRS Calculation with trends.docx` | CRS v2 + trend framework |

---

## Revision history

| Date | Change |
|------|--------|
| 2026-06-05 | Added [Development-Roadmap-4Month-Accelerated.md](./final/Development-Roadmap-4Month-Accelerated.md) — all phases in 17 weeks |
| 2026-06-05 | Added [Development-Roadmap.md](./final/Development-Roadmap.md) — program development schedule |
| 2026-06-05 | Added [MindPeers-Engine-Master-Production-Spec.md](./final/MindPeers-Engine-Master-Production-Spec.md) — single combined PDF-style master doc |
| 2026-06-05 | Data Ingestion v1.1.0 — Part1-complete event catalog (Appendix F); L2 §11 full lineage |
| 2026-06-05 | Added `final/` TRD + HLD package (Phases 01–05 + master program) |
| 2026-06-05 | Added CRS Unified v3 spec (Engine Part1 + CRS v2 + labels) |
| 2026-06-05 | Added L0 + L2 production specs, schemas, ingestion/features stubs |
| 2026-05-20 | ENGINE-POC consolidated doc (L1–L3 POC) |
