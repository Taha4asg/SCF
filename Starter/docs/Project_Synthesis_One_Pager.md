# Spatial Character in BIM — Project Synthesis (v1.0)

**Working title:** *Making the Invisible Visible: An ML-Driven Instrument for Spatial Character Feedback in BIM Design Workflows*
**Author:** Taha Asghari · **Timeframe:** ~10–12 working weeks · **Status:** Concept locked, pre-build

---

## 1. Objective

Develop a BIM-integrated design instrument that computes the **spatial character** of every room in an IFC model — using a previously trained ML pipeline as a computational proxy for perceived openness — and feeds it back to the architect **at the moment of a design decision**: the designer edits geometry, re-runs on demand, and sees how the character of the affected spaces shifted, checked against designer-defined project principles. Results are written back into the model as structured information, making design-alternative comparison a documented, defensible record.

**Intellectual spine (one principle, three scales):** every layer measures *traversed, perceived space rather than abstract geometry* — the isovist at the point level, the openness distribution at the room level, and the **access graph** (doors, not shared walls) at the structural level.

## 2. Terminology & claims discipline (agreed wording strategy)

No perception study is possible in this timeframe, so the writing never claims validated experience. Replacements, used consistently:

| Avoid | Use instead |
|---|---|
| experiential quality (as a claim) | **spatial character**; *computational proxy for perceived openness* (defined once) |
| "measures how a space feels" | "profiles / indicates the spatial character of" |
| the fingerprint | **Spatial Character Profile (SCP)** — mean openness + internal spread + access depth per room |
| validation | **illustrative evaluation** through worked case studies and reflective practitioner review; perceptual validation explicitly framed as future work |

This is honest, standard research-through-design language — it states exactly what was done and defers what wasn't.

## 3. Stages, predicted results, and stage risks

| # | Stage | Predicted result | Principal risk |
|---|---|---|---|
| 0 | **Asset consolidation** — refactor capstone inference into a callable module (`score_points(geometry) → df`) preserving per-point probabilities | Reusable scoring engine; the tool's heart, verified against capstone outputs | Hidden coupling between scoring and plotting code |
| 1 | **IFC ingestion & room graph** — `Graph.ByIFCPath` / `Graph.ByTopology(directApertures=True)`; extract IfcSpace boundaries, labels, access edges | Room-node graph with semantics; adjacency vs access distinction operational | Messy real-world IFCs; *fallback:* geometric opening detection |
| 2 | **Point→room aggregation (SCP core)** — point-in-polygon grouping; per-room mean openness (plan-relative) + internal spread (self-relative) + typology mix | Two-axis SCP per room; the project's central novel construct working on test files | Boundary/grid mismatches at thin rooms; grid resolution tuning |
| 3 | **Graph measures** — depth/privacy via ShortestPath on access graph (core); choice & centrality computed at *room* level (supporting) | Structural layer near-instant; privacy depth drives templates | None significant — pre-built in professor's topologicpy stack |
| 4 | **Change loop** — baseline vs edited state; re-run; per-room, per-edge, per-graph deltas; both reference frames reported (self-change + plan rebalance) | The before/after core interaction functioning end-to-end on demand | Isovist compute time per run (minutes, not seconds — accepted); legibility of three-layer deltas |
| 5 | **Principles & flagging** — template library (privacy gradient, etc.) set per project; violations reported per axis and per level | Designer-defined rule checking; "informative by default, bold on violation" | Template expressiveness vs simplicity balance |
| 6 | **Delivery** — pyRevit panel (thin trigger, local Python companion); evolved capstone heatmaps; animated before/after (**static side-by-side fallback**); IFC `Pset_SpatialCharacter` write-back **with option/iteration tag** | Demoable in-Revit workflow; enriched IFC readable in any viewer | pyRevit↔CPython bridge; animation polish under time pressure |
| 7 | **Alternatives comparison + write-up** — option A/B/C SCP comparison as demo climax; worked case studies (3–5 IFC models); dissertation | Complete narrative demo (hook: before/after → payoff: options compared); evaluated, written, defended | **Scope creep — the chief project risk throughout** |

**Tiering:** Stages 0–4 = guaranteed core (~6 weeks). Stage 5–6 = committed deliverable. Animated transition, choice/centrality prominence, comparison polish = stretch. Real-time local recompute, perceptual validation, generative redesign = named future work.

## 4. Probable tools & skills

**Already held:** Python, scikit-learn (trained RF + scalers, no retraining), shapely/geopandas, topologicpy (isovist, Grid, Graph), matplotlib. **To learn/shallow-learn:** ifcopenshell (IfcSpace/Pset read-write), pyRevit basics (panel, export trigger, view refresh), Plotly or lightweight HTML for the panel visuals, buildingSMART Pset conventions. **Execution assistants:** Claude Code / Antigravity for API boilerplate — architecture decisions stay ours.

## 5. Standing risk register (watch constantly)

1. **Scope creep** — enough good ideas for 9 months, time for 3; tier discipline is the defense.
2. **Compute time** — pure-Python ray casting; keep grid modest, parallelize (cell-5 pattern), never promise real-time.
3. **IFC quality variance** — test files early (Stage 1), keep the geometric fallback alive.
4. **Overclaiming** — terminology table above is the contract; every claim sits where evidence is strongest.
5. **Demo fragility** — static fallback for every animated element; rehearse on fixed test files.

## 6. Academic data & context needed from you before build

1. Capstone reference list (BibTeX/PDFs) — esp. **Benedikt (1979)** isovists; **Turner et al. (2001)** VGA.
2. **Hillier & Hanson** — justified graphs / depth (grounds privacy-depth academically).
3. **Appleton** prospect-refuge + **Dosen & Ostwald** review (grounds the internal-spread axis).
4. **Zhu et al.** IFC-Graph paper + **Jabi** topologicpy paper (grounds the graph layer in your department's stack).
5. **ResPlan dataset** citation and license note.
6. **ISO 19650 / UK BIM Framework** documents (grounds the information-deliverable framing).
7. buildingSMART documentation on **custom property sets** (naming conventions for `Pset_SpatialCharacter`).
8. 3–5 **test IFC files** with labeled IfcSpaces (varied quality deliberately — one clean, one messy).
9. Any precedent you can find on **design-tool evaluation via case study / research-through-design** (methodology cover for the illustrative evaluation).
10. Your professor's preferred **proposal template/format** for ART049.
