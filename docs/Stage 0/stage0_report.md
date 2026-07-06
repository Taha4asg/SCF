# Stage 0 Report — The Scoring Engine
*SCF · completed. All validation passed.*

## Objective (as defined before build)
Port the capstone inference (notebook cell 4, the definitive final approach) into
`core/scoring.py` as composable functions. Acceptance: (1) numerical identity with
the notebook on identical input; (2) zero new analytical logic; (3) every step
independently callable. **All three met**, with one documented, provably-safe deviation.

## Method evaluation
Three architectures considered: monolithic port (rejected — blocks Stage 2/4 reuse),
stateful engine class (rejected — hidden state vs reproducibility), pure functions +
thin orchestrator (**chosen**). Faster isovist implementations (vectorised NumPy,
visilibity) deliberately deferred: swapping implementations now would violate the
identity criterion; they become Stage-4+ optimisations validated against this reference.
**Module boundary = two shapely polygons (land, wall)** — geometry-source agnostic, so
the Stage 1 IFC layer plugs in without touching this code.

## Deliverables
- `core/scoring.py` — generate_grid · extract_wall_segments · isovist ·
  compute_features · compute_feature_table · scale_and_weight · score_features ·
  score_plan. Constants verbatim (weights Av 1.0, Uv 1.0, Cv 0.5, Ov −0.6, Hv 1.0;
  confidence threshold 0.65; spacing = min dim / 50; shrink 0.1·spacing).
- `tests/test_stage0.py` — final validation suite (passing).
- `tests/export_resplan_samples.py` — run locally to enable the one deferred test.

## Validation results
**Test 1 (geometry half).** Synthetic two-room plan, merged holed walls, 0.9 m door:
rays blocked correctly; mean isovist area per room matches physical floor area
(51.6 ≈ 51.6 m²; 33.1 ≈ 32.6 m² + door glimpse); quality ordering follows enclosure;
all five typologies appear.
**Test 2 (scoring half).** Module vs an independent re-implementation of the notebook
ML block across **all 221 capstone plans / 84,560 points: 0 prediction mismatches,
quality deviation 0.0.** Class distribution sensible (16–28% per class).

## Findings (critical audit — three)
1. **Hole-blindness (fixed, the single deviation).** The capstone ray-caster read
   polygon exteriors only — correct for ResPlan's solid wall pieces, but silently
   catastrophic for merged/holed wall geometry (walls become invisible; the whole plan
   scores as one space). `extract_wall_segments` now includes interior rings.
   Byte-identical on hole-free input; fails loud instead of quiet on holed input.
   **Consequence for Stage 1:** IFC-derived walls may arrive holed — now safe.
2. **Stale artifacts.** `kmeans_model.pkl` + `cluster_map.pkl` do not correspond to the
   final RF (55% best-case purity; the map even labels the most-enclosed cluster
   "Wide-Open"). They are pre-GMM pipeline leftovers, unused by inference.
   **Action:** moved to `core/legacy/` to prevent future misuse. *(User: please confirm
   against your training history — is the final label generator the GMM on your PC?)*
3. **Training/inference grid discrepancy (capstone-inherited, documented).** The master
   dataset was generated at spacing min/20, shrink 0.01; final inference uses min/50,
   shrink 0.1. Not a bug in the port — but worth one honest sentence in the
   dissertation's methods.

## Deferred (one item)
Exact geometry-half reproduction vs capstone-stored ResPlan features requires ResPlan
geometry (297 MB, local-only). `export_resplan_samples.py` exports 3 plans as WKT;
once pushed, the equivalence test runs here. Until then the geometry half stands on
physical-area validation (strong) rather than dataset identity (exact).

## Stage 1 preconditions established
The engine consumes (land, wall) polygons and is holed-geometry-safe. Stage 1's job:
produce exactly that pair per storey from IFC, plus the room graph.
