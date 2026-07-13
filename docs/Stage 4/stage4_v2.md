# Stage 4 Addendum v2 — Privacy, Reachability & Full-Building Perception
*Prompted by architect review of the first character demo. All Stage 4 tests rewritten and passing; full regression Stages 0–3 green with the rescored field.*

## Issue 1 — The privacy gradient was flat (all FZK rooms "semi-private")
Depth-from-carrier alone cannot differentiate rooms that share a depth. **New
formula (author-approved on both buildings' full orderings): PRIVACY = 0.5·segregation + 0.5·closability**, each normalised 0–100 within the building:
- *Segregation* = **RRA** — Hillier's size-normalised mean depth (relative
  asymmetry over the diamond value): "how deep does the plan hold this room
  from everywhere," comparable across plans of any size by construction.
- *Closability* = how much of the entrance path can be **shut behind you**:
  door 1.0 · stair 0.8 · opening 0.35 (an archway is a permanent leak).
Gradient words (Robinson register via Mustafa et al. 2010) are assigned by
within-building quantile. Result: FZK now reads public Flur → semi-public
open-plan south (Wohnen 29.5 < Küche 36.7 — the kitchen IS deeper, as the
author observed) → private door-rooms 79.2 → innermost Galerie 100. The
door-room triple ties **because they are configurationally identical** — an
honest tie; their differences live in the perceptual register. On the Duplex
the two components prove their joint necessity: Kitchen vs Living (identical
RRA, split by closability) and downstairs vs upstairs Bathroom (downstairs
MORE segregated, upstairs wins on barriers — one storey up genuinely reads
more withdrawn).

## Issue 2 — Upper storeys were never scored perceptually
Author correction accepted: the stair IS the upper level's entrance, and the
graph already treated it so (one topological step; upper rooms already deeper).
What was missing was the isovist field. Both upper storeys are now scored
(FZK Dachgeschoss 437 pts; Duplex Level 2 449 pts) and every room in both
buildings carries the full two-register profile. Lifts extend the same way
via IfcTransportElement (named future work). Bonus insight: the scored
Galerie immediately fired the second divergence template — *"plain and clear
yet held deepest by the plan — a withdrawn retreat"* — architecturally exact
for a gallery loft.

## Issue 3 — Reachability was three flat tiers ("all direct-reach")
**New formula: REACHABILITY = 0.5·topological + 0.5·metric** (Hillier & Iida
2005 — the two distance concepts are genuinely different and both felt):
- *Topological* = threshold-weighted cost of the easiest way in (door 1.0 ·
  opening 0.55 · stair 1.6) + a small route-redundancy bonus.
- *Metric* = actual walking distance from the chosen entrance, chained
  threshold-to-threshold to the room centre (thresh_xy now stored on every
  edge; room centroids on every node).
This vindicated the author's instinct with evidence: **Büro 74.6 > Küche
66.9** — the office is two doors but 4.0 m; the kitchen one archway but 6.7 m
down the corridor. Every room now carries a distinct, decomposable value the
tool can explain ("easy to enter, far to reach"). The tiered measure remains
as a coarse label; the continuous score is primary. Blend weights (50/50
defaults) are explicitly Stage-5 slider material. A premise correction is
recorded: the FZK kitchen is reached DIRECTLY from the corridor via a 1.14 m
opening (evidence figure archived) — not through the living room — but the
author's conclusion held via the metric component.

## Issue 4 — "Two senses of depth" (the kitchen question, answered)
The kitchen is NOT the ground floor's deepest room by segregation (the
door-rooms are) but IS among its deepest by metric journey (6.7 m). The
profile now expresses both senses instead of collapsing them: RRA answers
"how deep does the plan hold it," walk answers "how far in must I travel."
Topologically shallow + metrically far = the signature of an open-plan room
at the end of a circulation run.

## Divergence recalibrated (deterministic as ever)
Templates now watch the continuous measures: *complex-yet-reachable* =
above-median complexity AND reach ≥ 80 (Flur, both Foyers — the control
role); *plain-yet-secluded* = bottom-third complexity AND privacy ≥ 80
(Galerie — the retreat). Above-median (not top-third) because a control hall
in a building full of small complex rooms must still register; verified on
both buildings, still template-fill, still no language model.

## Housekeeping closed
The queued Duplex L1 rescore (post stair-aggregate-opacity fix) is DONE
(395 pts): Foyer prospect settles at 45/51 (stair now blocks vision), the
Foyer–Kitchen opening reads jump 0 locally. All archived fields are now
post-fix. Generalisation guards shipped: max==min normalisation, unreachable
rooms → None throughout, multi-entrance via weighted shortest path, loops
native to the graph measures. Honest caveats carried in-code: the closability
and threshold-cost coefficients are reasoned conventions, tunable in Stage 5.

## Files changed
`graph_layer/scp.py` — node centroids + edge thresh_xy (incl. entrance edges).
`graph_layer/structure.py` — stair-edge coordinates; `_privacy_and_reach`
(RRA, barrier, walk, blended scores, gradient words). `graph_layer/character.py`
— configurational register speaks privacy + reachability with components;
divergence on continuous measures. `tests/test_stage4.py` — rewritten
(approved orderings asserted on both buildings). New archived fields:
`fzk_OG.csv`, `duplex_L2.csv`, `duplex_L1.csv` (rescored, post-fix).
