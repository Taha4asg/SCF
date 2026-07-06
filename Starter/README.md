# SCF — Spatial Character Framework

An ML-driven instrument for spatial character feedback in BIM design workflows.

The tool reads an IFC model, computes the **Spatial Character Profile (SCP)** of every
room — mean openness, internal spread, and access depth — using a trained isovist-based
ML pipeline, and feeds the consequences of geometric design changes back to the
architect inside Revit, at the moment of decision.

**One principle, three scales:** every layer measures traversed, perceived space rather
than abstract geometry — the isovist at the point level, the openness distribution at
the room level, and the access graph at the structural level.

## Repository structure

- `core/` — Stage 0: the callable scoring engine (refactored capstone inference)
- `ifc_layer/` — Stage 1-2: IFC ingestion, room graph, point-to-room aggregation
- `graph_layer/` — Stage 3: access-graph measures (depth, choice, centrality)
- `tool/` — Stage 4-6: change loop, principles/flagging, pyRevit panel, Pset write-back
- `tests/` — verification against capstone outputs and test files
- `test_files/ifc/` — verified sample models (FZK Haus IFC4, Duplex IFC2x3)
- `references/` — papers and standards (see docs/Project_Synthesis_One_Pager.md, section 6)
- `docs/` — project synthesis, proposal, dissertation drafts
- `notebooks/` — exploratory work

## Test files

| File | Schema | Spaces | Doors | Notes |
|---|---|---|---|---|
| FZK_Haus.ifc | IFC4 | 7 (German labels) | 5 | KIT/IAI sample; single-family house; cite KIT-IAI |
| Duplex.ifc | IFC2x3 | 21 (English) | 14 | buildingSMART community sample; two storeys |

## Status

Concept locked. Build stage 0 in progress.
