# Stage 5 Report — The Visual Instrument
*SCF · Stage 5 complete. All acceptance criteria met; full regression (Stages 0–4) passing.*
*This stage gives the framework its visual voice: the profiles of Stage 4 are no longer text — they are drawings a designer reads the way designers read everything else: in the plan, in the graph, in the sequence.*

---

## 1. Objective and acceptance criteria (fixed before build)

Deliver a deterministic library of literature-anchored views composed into a per-building **Character Sheet**, plus one interactive isovist explorer. Acceptance: (1) every SCP axis and both registers visible somewhere — nothing lives only as text; (2) visual conventions inherited from the field where they exist; (3) the two registers use two distinct colour families, enforced in code and tested; (4) reliability hedging visible; (5) deterministic rendering; (6) both buildings validated. **All six met** (§5). Structural decision, author-approved: visualization is its **own stage, built before templates**, because Stage 6's sliders must control living pictures — every view is a pure function (graph in, axes drawn) precisely so sliders can re-call them.

## 2. The visual vocabulary and its inheritance

Where the field already has a visual convention, SCF inherits rather than invents — the same discipline as the lexicon: the **quality lens** and **choropleth gradient plans** follow the Depthmap warm–cold field tradition (Turner 2001; Hillier); the **justified graph** is Hillier & Hanson's (1984) own iconic drawing — rooms in rows by carrier depth; the **genotype chart** draws Hillier's (1996) inequality sequence directly (rooms ranked by integration — the sequence IS the signature, now literally a picture); the **serial-vision strip** renders the walk from entrance to the deepest room as an experiential curve — Cullen's (1961) concept, Appleton's (1984) prospect–refuge sequencing, and Ganis's (1998) doctoral evidence that the *sequence* of spatial information drives affective response; the **isovist polygons** in the explorer are Benedikt's (1979) figures, computed live from our Stage-0 engine; and the **room cards** are semantic-differential profiles in the register validated by Alfirević et al. (2026).

## 3. The colour law (the two-register rule, in pixels)

Perceptual axes render exclusively in the **RdYlBu** family (blue = open/plain/calm; red = enclosed/intricate); configurational axes exclusively in **viridis** (light = public/reachable/integrated; dark = private/segregated/withdrawn). A designer can tell *which register they are looking at from colour alone* — the Flur lesson enforced visually, and asserted in the test suite (T1). Reliability hedging is visible, not textual: unreliable rooms hatch and desaturate — the graphic "indicatively". Every relative view states "relative to this building" in its title, so the genotype method's building-relative normalisation can never be misread as cross-building comparison.

## 4. What was built

`viz_layer/views.py` — pure view functions: quality_lens, choropleth (five axes), justified_graph, genotype_chart, serial_strip, room_card, colour-law constants. `viz_layer/sheet.py` — the Character Sheet composer: **Board A (spatial)** = quality lens · privacy plan · reachability plan · justified graph · genotype chart · serial strip · upper-storey privacy; **Board B (rooms)** = the semantic-differential card grid, divergences flagged in the title, mirror pairs adjacent. `viz_layer/explorer.py` — the offline HTML isovist explorer: probe points (room centres + door thresholds) precomputed through the Stage-0 engine itself, dropdown-selectable, each showing the true visibility polygon with its five Benedikt features and local quality (FZK 11 probes; Duplex L1 14 probes; plotly, no server, no language model). Precomputation is the honest middle: static HTML cannot compute isovists, and computing them everywhere is waste.

## 5. Validation

Seven criteria, all passing: colour-law binding and full axis coverage (every SCP axis appears in at least one view); every view renders on both buildings; justified-graph rows equal carrier depths; the genotype chart's order equals the integration order exactly; the serial strip's walked distance is monotone; room cards keep pole labels inside the frame and carry the "indicative" flag for low-support rooms; explorers exist as self-contained plotly documents with their probe dropdowns. Full regression Stages 0–4 re-passes. One execution finding (F1): the first card render clipped its pole labels outside the axes — caught by eye, fixed by widening the card frame, and the fix is now a tested invariant (T6). A second (F2): the explorer initially assumed shapely polygons from `scoring.isovist`, which actually returns vertex lists — our own Stage-0 contract, misremembered; corrected, and a reminder that contracts bind their authors too.

## 6. Reading the sheets (what the visuals immediately show)

On FZK, the serial strip alone justifies the stage: the walk from the front door rises through the corridor into the bright southern zone — peaking at the archway (Δ7, seamless) — then falls off a cliff through the stair into the Galerie's deep quiet (quality 13, privacy 100). That is the building's experiential plot, drawn. The genotype chart reads *Flur > Wohnen > Küche > (Büro = Bad = Schlafzimmer) > Galerie* — the inequality signature as a picture. And the Flur's card makes the divergence visible at a glance: intricate, fully integrated, public and reachable, yet only moderately open — the control-hall, in six dots.

## 7. Critical appraisal — why good, where incomplete

**Strengths.** (1) Nothing is text-only anymore; the instrument's primary artifact is now the Character Sheet, and every panel inherits a citable convention. (2) The colour law makes the two-register epistemology *perceptible* — a reviewer can audit the register of any figure without reading a caption. (3) Pure-function views mean Stage 6 costs no rework: sliders re-render, the change loop diffs two sheets. (4) The explorer closes the pedagogical gap — a designer can finally *see where the numbers come from*, one isovist at a time.

**Incomplete, plainly.** (1) Aesthetic calibration is v1: the author's invitation to supply exemplar figures stands, and typography/layout will be tuned to taste. (2) The explorer probes centroids and door thresholds only; opening thresholds and serial-path waypoints are a scoped extension. (3) The serial strip follows one path (entrance → deepest room); multiple paths and user-chosen destinations belong to Stage 6's interactivity. (4) Board layouts are tuned for 7–20-room dwellings; very large plans will need pagination rules. (5) Static sheets do not yet embed the divergence *sentences* — the text and visual layers meet fully in the pyRevit panel (Stage 7 delivery).

## 8. What this stage feeds

Stage 6 (templates/gradients/sliders) draws its controls directly onto these views: a privacy-threshold slider re-colours the privacy plan live; a declared genotype overlays the genotype chart as a target sequence; violations flag on the choropleths in the bold voice. Stage 7's change loop renders two sheets and draws the deltas. The instrument now has eyes; next we give the designer the controls.

## 9. Deliverables

`viz_layer/views.py` · `viz_layer/sheet.py` · `viz_layer/explorer.py` · `tests/test_stage5.py` (7 criteria, passing) · Character Sheets: `FZK_sheet_A_spatial.png`, `FZK_sheet_B_rooms.png`, `Duplex_sheet_A_spatial.png`, `Duplex_sheet_B_rooms.png` · Explorers: `FZK_isovist_explorer.html`, `Duplex_isovist_explorer.html` · this report.
