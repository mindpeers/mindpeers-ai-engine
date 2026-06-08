#!/usr/bin/env python3
"""Merge POC markdown files into ENGINE-POC-COMPLETE-DOCUMENTATION.md"""

from pathlib import Path

ROOT = Path("/Users/apple/Downloads/mp_ai")
OUT = ROOT / "ENGINE-POC-COMPLETE-DOCUMENTATION.md"

HEADER = """# Mental Health Engine — Complete POC Documentation

**Version:** 3.0 (consolidated)  
**Date:** May 20, 2026  
**Status:** Single source of truth — specification complete, ready for implementation  
**Audience:** Product, engineering, data science, clinical/design reviewers

> **This document replaces** the split POC markdown files. Supporting assets:
> - Sample data: `Engine-POC-Sample-Dataset.xlsx` (sheet `All_Columns_Complete_Sample`)
> - L4 reference: `poc_extract.txt`
> - Validate columns: `python scripts/validate_dataset_columns.py <your-file.xlsx>`

---

## Table of contents

1. [How to use this document](#part-1--program-overview)
2. [Program context & architecture](#part-1--program-overview)
3. [Gap register & product decisions](#part-2--gaps-and-decisions)
4. [Gap deep dive (G1–G15)](#part-3--gap-deep-dive)
5. [L2 — Feature registry & computation](#part-4--l2--feature-registry--computation)
6. [L3 — Scoring service](#part-5--l3--scoring-service)
7. [L1 — Engine snapshot & batch API](#part-6--l1--engine-snapshot--batch-api)
8. [L1 — Patterns & actions](#part-7--l1--patterns--actions)
9. [Dataset columns & validation](#part-8--dataset-columns--validation)
10. [Implementation roadmap & appendices](#part-9--roadmap-and-appendices)

---

"""

PART_HEADERS = {
    "PRD-POC-Alignment-and-Gaps.md": ("part-1--program-overview", "Part 1 — Program overview"),
    "PRD-POC-Alignment-GAPS.md": None,  # skip duplicate
}

# Sections to extract from alignment doc by line markers
def strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    out = []
    skip_title = True
    for line in lines:
        if skip_title and (line.startswith("# ") or line.startswith("| Field") or line.startswith("**Changelog") or line.startswith("| Version") or line.startswith("| 1.0") or line.startswith("| 2.") or line.startswith("---") or line.startswith("## Table of contents")):
            if line.startswith("## 1. How to use"):
                skip_title = False
            else:
                continue
        if skip_title:
            continue
        if line.strip() == "*End of document — version 2.1*":
            break
        out.append(line)
    return "\n".join(out)


def strip_doc_header(text: str, start_section: str = "## 1.") -> str:
    idx = text.find(start_section)
    if idx == -1:
        return text
    body = text[idx:]
    for end in ("*End —", "*End of document"):
        e = body.find(end)
        if e != -1:
            body = body[:e]
    return body.strip()


def relink(text: str) -> str:
    replacements = [
        ("./PRD-POC-Alignment-and-Gaps.md", "#part-2--gaps-and-decisions"),
        ("./L3-Scoring-Service-POC.md", "#part-5--l3--scoring-service"),
        ("./L2-Feature-Registry-POC.md", "#part-4--l2--feature-registry--computation"),
        ("./L1-Engine-Snapshot-POC.md", "#part-6--l1--engine-snapshot--batch-api"),
        ("./L1-Patterns-and-Actions-POC.md", "#part-7--l1--patterns--actions"),
        ("./POC-Documentation-Index.md", "#"),
        ("./Engine-POC-Sample-Dataset.xlsx", "`Engine-POC-Sample-Dataset.xlsx`"),
        ("[L3 §7](./L3-Scoring-Service-POC.md)", "[§7 Pillar scores](#75-pillar-scores-g1)"),
        ("[L3 §8](./L3-Scoring-Service-POC.md)", "[§8 Trend composites](#8-six-trend-composites-g2)"),
        ("[L2 §2](./L2-Feature-Registry-POC.md)", "[§4.2 Registry](#42-g3--canonical-registry-closed)"),
        ("[L2 §3](./L2-Feature-Registry-POC.md)", "[§4.3 Computation](#43-g4--computation-spec-closed)"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def main():
    alignment = (ROOT / "PRD-POC-Alignment-and-Gaps.md").read_text(encoding="utf-8")
    l2 = (ROOT / "L2-Feature-Registry-POC.md").read_text(encoding="utf-8")
    l3 = (ROOT / "L3-Scoring-Service-POC.md").read_text(encoding="utf-8")
    l1snap = (ROOT / "L1-Engine-Snapshot-POC.md").read_text(encoding="utf-8")
    l1pat = (ROOT / "L1-Patterns-and-Actions-POC.md").read_text(encoding="utf-8")
    dataset = (ROOT / "Dataset-Column-Validation-Checklist.md").read_text(encoding="utf-8")

    parts = [HEADER]

    # Part 1: alignment sections 1-7, 10, 6 (overview) - skip 8-9 we'll do part 2-3
    align_body = strip_doc_header(alignment, "## 1. How to use")
    # Split at gap register
    gap_idx = align_body.find("## 8. Gap register")
    part1 = align_body[:gap_idx].strip()
    part1 = relink(part1)
    parts.append("---\n\n# Part 1 — Program overview\n\n")
    parts.append(part1)
    parts.append("\n\n")

    # Part 2: gap register + decisions from alignment
    not_gap_idx = align_body.find("## 10. Items explicitly not gaps")
    part2 = align_body[gap_idx:not_gap_idx].strip()
    decisions = align_body[align_body.find("## 11. Product decisions"):align_body.find("## 12. Implementation")]
    part2 += "\n\n" + decisions.strip()
    part2 = relink(part2)
    parts.append("---\n\n# Part 2 — Gaps and decisions\n\n")
    parts.append(part2)
    parts.append("\n\n")

    # Part 3: gap deep dive
    gap_dive_idx = align_body.find("## 9. Gap deep dive")
    part3 = align_body[gap_dive_idx:not_gap_idx].strip()
    part3 = relink(part3)
    parts.append("---\n\n# Part 3 — Gap deep dive\n\n")
    parts.append(part3)
    parts.append("\n\n")

    # Part 4-7 layer docs
    for title, slug, content, start in [
        ("Part 4 — L2 — Feature registry & computation", "part-4--l2--feature-registry--computation", l2, "## 1. Purpose"),
        ("Part 5 — L3 — Scoring service", "part-5--l3--scoring-service", l3, "## 1. Purpose"),
        ("Part 6 — L1 — Engine snapshot & batch API", "part-6--l1--engine-snapshot--batch-api", l1snap, "## 1. Purpose"),
        ("Part 7 — L1 — Patterns & actions", "part-7--l1--patterns--actions", l1pat, "## 1. Purpose"),
    ]:
        body = strip_doc_header(content, start)
        body = relink(body)
        # Renumber ## 1. to ## 4.1. style under part
        parts.append(f"---\n\n# {title}\n\n")
        parts.append(body)
        parts.append("\n\n")

    # Part 8 dataset
    ds_body = strip_doc_header(dataset, "## Which file")
    ds_body = "# Part 8 — Dataset columns & validation\n\n" + ds_body.replace("# Dataset column validation checklist (v1 Engine)", "## 8.1 Overview")
    parts.append("---\n\n")
    parts.append(relink(ds_body))
    parts.append("\n\n")

    # Part 9 roadmap + appendices + index summary
    roadmap = align_body[align_body.find("## 12. Implementation"):].strip()
    roadmap = relink(roadmap)
    index = (ROOT / "POC-Documentation-Index.md").read_text(encoding="utf-8")
    impl_order = index[index.find("## Implementation order"):index.find("*End")]
    parts.append("---\n\n# Part 9 — Roadmap and appendices\n\n")
    parts.append(roadmap)
    parts.append("\n\n## 9.1 Implementation order (quick reference)\n\n")
    parts.append(strip_doc_header(impl_order, "## Implementation"))
    parts.append("\n\n## 9.2 Related files (repository)\n\n")
    parts.append("```\nmp_ai/\n├── ENGINE-POC-COMPLETE-DOCUMENTATION.md  ← this file\n├── Engine-POC-Sample-Dataset.xlsx\n├── poc_extract.txt\n├── scripts/validate_dataset_columns.py\n├── scripts/generate_sample_dataset.py\n└── (legacy split .md files — deprecated, see top of each)\n```\n")
    parts.append("\n---\n\n*End of consolidated documentation — version 3.0*\n")

    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {OUT} ({len(''.join(parts)):,} chars)")


if __name__ == "__main__":
    main()
