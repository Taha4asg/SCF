# Stage 1 Addendum v1.2 — Second Architect Review Integrated
*Three issues raised on the v1.1 render; each diagnosed to root cause before fixing.
Both test suites re-passed.*

## R5 — White dots (root cause: duplicated grid points)
Two hypotheses were tested and eliminated (geometry micro-holes: none; quality>100
float overflow: max is exactly 100.0). The arithmetic cornered it: FZK's walkable
should yield ~2,575 points at 0.2 m; the grid produced 2,701 — ~126 DUPLICATES. Cause:
an L-shaped walkable face fails topologic's direct face build, falls back to
triangulation, and the grid is generated per-triangle, duplicating points on shared
internal edges; scipy.griddata emits NaN patches at duplicate coordinates — the white
dots, aligned along invisible triangulation edges. Fix: grid deduplication at source in
`generate_grid` (a strict no-op when faces build whole — all of ResPlan — so Stage 0
identity is preserved; suites re-passed). Duplicates now: 0. Bonus: ~5% fewer wasted
isovists.

## R6 — Stairs are OPAQUE (D7 revised; the architect's rule, quantified)
Review argument accepted in full: a stair device in mid-space works as a (mostly)
sight-blocking obstacle — the zone behind it IS more enclosed in real space. Revised
policy: stair ELEMENTS join the vision walls (as their convex hull — a spiral reads as
its cylinder; also keeps ray-cast segments sane at 245 vs 328); stair-named SPACES
remain transparent point-free rooms whose enclosure comes from their own walls.
**The prediction, tested:** the 1.4 m zone east of FZK's Wendeltreppe scored Q=89.7
with a transparent stair and **Q=39.5 with the opaque stair (Δ −50.2)**; Wohnen's room
mean moved 95.8 → 83.4. One modelling decision, one visible experiential consequence —
the tool's core thesis, demonstrated on itself before the change loop even exists.

## R7 — Stair rendering
The stair now draws as a dark hatched hull at wall z-order with a crisp vector edge;
the field is masked beneath it and interpolation artefacts at its boundary are gone
(the duplicates fix removed most; resolution raised to 480 for the rest).

## Deliverables (v1.2)
`core/scoring.py` (dedupe) · `ifc_layer/ifc_reader.py` (D7 revised + scoring_inputs +
vision hull) · `core/render.py` (dedupe/clip, styling, 480 px) · `FZK_v12.png`.

---
## v1.3 — R8: the white dots, actually solved (with credit where due)
The v1.2 dedupe fix was real but was NOT the dot cause. The architect's own hunch —
"aren't they contours or something related?" — was correct: 43,834 grid cells sat at
exactly 100.0 and interpolation arithmetic overshot to 100.00000000000003; anything
above the top contourf level renders BLANK. Three-part fix in `render.py`: clip AFTER
interpolation (not before), `extend='both'` as belt-and-braces, iso-lines drawn at
interior levels only (lines at exact data extremes speckle across flat plateaus).
A final residue (403 px) was the 0.05 m mask halo around the stair reading as a white
ring — fill and mask now share one outline. Verified: **0 white pixels** in the test
window; the stair draws as one authoritative hull (`stair_vision_hull`) used
identically for vision and rendering — no double outlines.
