# Stage 4 Report — The Unified Spatial Character Profile
*SCF · Stage 4 complete. All acceptance criteria met; full regression (Stages 0–4) passing.*
*This stage delivers the academic backbone the author asked for: it turns the numbers SCF already produces into a defensible, professional reading of a room's spatial character — in two registers, composed from individually-validated axes, with no language model anywhere in the pipeline.*

---

## 1. Objective and acceptance criteria (fixed before build)

Define **character** as a structured composition of validated axes in two registers (perceptual and configurational) that can agree or disagree, read relative-first with an absolute layer beneath, and surface the disagreement deterministically. Acceptance: (1) three perceptual axes, each ranked within the building and banded absolutely; (2) the new complexity axis computed from data already stored, with no rescore; (3) configurational legibility as accessibility-in-reach, tiered with ties allowed; (4) divergence fully deterministic — a computed flag firing a template sentence, no LM; (5) the two registers demonstrably independent; (6) the profile stable across mirror units. **All six met** (§6).

## 2. The construct

Character is reported in **two registers**, each composed from axes that are individually grounded in the literature and read **relative-first** (this room's rank among the others in the building — Hillier's genotype method) **with an absolute band as a second layer** (fixed thresholds, for cross-room legibility).

**Perceptual register — what the room feels like from within.**
- *Prospect* — mean openness; isovist area → spaciousness (Franz & Wiener 2004; Dosen & Ostwald 2016, the best-supported factor). Already computed.
- *Variety* — internal experiential range; prospect–refuge in sequence within the room (Appleton 1984). Spoken as *range*, never as a "refuge" benefit, per the evidence (Dosen & Ostwald 2016: refuge weak in interiors). Already computed.
- *Complexity* **(new this stage)** — how broken-up and hidden-behind-thresholds the boundary is. Vertices/occlusion → perceived complexity (Wiener et al. 2007, r≈.78–.81; Dosen & Ostwald 2016, 2nd-best interior factor). **Computed with no new geometry** (§3).

**Configurational register — where the room sits in the building's reach-structure.**
- *Integration* — closeness; publicness (Hillier 1996). Already computed.
- *Depth* — justified depth from the carrier; privacy, named on Robinson's territorial gradient via Mustafa et al. 2010. Already computed.
- *Choice* — betweenness; through-movement (Hillier 1996). Already computed.
- *Legibility* **(new this stage, and reframed by author review)** — accessibility-in-reach: how directly a room is reached from the carrier (§4). A **tiered** measure (Lynch register).

The configurational register is implemented as an **extensible axis list**, not a hardcoded set: control value, RRA, or a future visibility-integration measure slot in as one entry, not a rewrite — the structural expression of the author's instruction to leave room for deeper graph analysis later.

## 3. The complexity axis: a new qualitative parameter from existing numbers

The reading round (Wiener et al. 2007) identified a quality neither register captured: perceptual complexity — the broken-up, partly-hidden character of what surrounds the observer. Crucially, this required **no new computation**: the capstone's five Benedikt features already encode it. **Cv** (circularity = 4π·Area/Perimeter²) is the inverse of jaggedness — a low Cv means a broken-up outline; **Ov** (occlusivity) is the fraction of the view-boundary that is hidden edges. Complexity is composed as `(1 − Cv̄)·(0.5 + 0.5·Ōv)` × 100, aggregated per room from points already stored. This keeps the tool lean (the author's explicit constraint) and means the axis is recomputable from any saved field without re-scoring. On FZK it is immediately discriminating: Flur is the most intricate room (61 — its boundary is mostly doorways to unseen spaces), Büro the plainest reliable room (33 — a simple enclosed cell).

## 4. Legibility as accessibility-in-reach (the author's reframing)

Architect review corrected an early error worth recording, because it sharpened the whole construct. The first implementation computed "legibility" from isovist geometry (Cv/Ov) and scored the Flur *lowest* — which the author correctly rejected: the Flur is the entrance hall, attached to the carrier, and should read as **highly legible**. The diagnosis: the isovist measure was conflating *elongation* with *illegibility* (a long straight hall is thin but easy to grasp), and — more fundamentally — it was measuring a **perceptual** property and mislabelling it. The author's definition resolved it: **legibility is accessibility-in-reach** — a room is legible when it is easy to reach and reached directly rather than through intervening spaces (Lynch's sense: how readily one grasps and moves through the structure). This is **configurational, not perceptual**, so it moved registers, and the perceptual Cv/Ov measure took its honest name, *complexity*.

Legibility is computed on the building graph as **tiers** (ties allowed, to stay simple and honest on complex plans): tier 0 = on the carrier / opens to everything (Flur, both Foyers); tier 1 = one direct door off a shallow hub (Büro, Bad, Schlafzimmer, Wohnen, Küche — a genuine tie, as the author directed); tier 2+ = reached only through other rooms or up a stair (Galerie, tier 3). The split into complexity (perceptual) and legibility (configurational) is not cosmetic: it is the two-register separation doing real work — a room can be complex to *see* through yet easy to *move* through, which is precisely the Flur.

## 5. Divergence: the signature insight, fully deterministic (no language model)

The stage's sharpest output is the moment the two registers **disagree**. The author raised the right concern — generating such prose would need a local language model, adding fragility, non-determinism, and indefensibility. The resolution: divergence is **not generated, it is detected**. It is arithmetic. For each room the tool compares its **perceptual-complexity rank** against its **configurational-reach tier**; when a room is among the most complex yet the most reachable (tier 0), a **pre-written template sentence** fires with the room's own name slotted in. No model, fully inspectable, reproducible byte-for-byte. Two templates exist: *complex-yet-reachable* (the control-hall) and *plain-yet-secluded* (the withdrawn simple room). The mechanism reuses the deterministic band-and-fill grammar built in Stage 3A.

The worked case is the one that started this whole line of review. FZK's **Flur** now reads: *perceptually* open, varied, highly intricate; *configurationally* most integrated, most legible, most through-moved; and the divergence fires — *"visually complex yet the most reachable space — hard to read through, easy to move through: a control/threshold role."* That sentence is the intellectual payload of Stage 4, and it is the author's original correction, finally captured by the machinery.

## 6. Validation results

**FZK.** Three perceptual axes rank and band correctly; complexity present from the saved field with no rescore; legibility tiers are Flur=0, the direct-reach group=1 (the author-directed tie), Galerie=3; the Flur divergence fires as *complex_yet_reachable* while Büro (a plain direct room) correctly does not; and the two registers are provably separate — Büro and Küche share legibility tier 1 yet carry different prospect bands (confined vs expansive). **Duplex.** The mirror units are the strongest available validation: the two units yield matching character (complexity within 1 point, identical tiers, identical prospect bands), and **both** Foyers diverge as control-halls — the construct generalises beyond the single worked example. **Regression.** Stages 0–3 suites all re-pass alongside the six Stage 4 tests. The full two-building narration is archived as `SCF_character_demo.txt` and reads as professional architectural description.

## 7. Critical appraisal — why good, where incomplete

**Strengths.** (1) The academic backbone is real: every axis is grounded in a named source, and confidence is disciplined by the evidence hierarchy (Dosen & Ostwald 2016) — prospect and complexity spoken plainly, variety framed honestly as range, refuge never claimed. (2) The two-register design, forced by the Flur, is validated: it lets a room be one thing perceptually and another configurationally, which single-score tools cannot express. (3) The signature insight is deterministic — no language model, so it is fast, reproducible, and examinable, exactly as required. (4) A new qualitative parameter (complexity) was extracted from numbers already in hand, at zero compute cost. (5) The configurational register is extensible by design, honouring the instruction to leave room for deeper graph analysis.

**Incomplete, plainly.** (1) Complexity's band thresholds are corpus-calibrated conventions, not perceptual constants — flagged as tunable, like Variety's. (2) Legibility tiers are deliberately coarse (ties allowed); a finer reach-directness measure is possible but was set aside to keep the tool simple on complex plans, per the author's steer. (3) The divergence margin (top-third complexity vs tier-0 reach) is a defensible but adjustable threshold. (4) The visibility-graph layer (seen-but-not-reached — the fuller answer to visibility ≠ permeability, Beck & Turkienicz 2009) remains **named future work**, not built. (5) Perception varies with lived background even where it doesn't with expertise (Dosen & Ostwald 2016; Alfirević et al. 2026) — the tool computes a proxy, and says so. (6) The Duplex field still predates the Stage-2 stair-opacity fix; rescore remains queued.

## 8. What this stage feeds

Stage 5 (templates / gradients / sliders) consumes these axes directly: the designer declares intent as target ranges or a target inequality-sequence (Hillier's genotype-as-template) over exactly the perceptual and configurational axes defined here, and the tool flags deviation. Stage 6 (the change loop) diffs two of these character profiles and speaks the differences in the same validated language. The academic skeleton the author asked for is now the literal skeleton of the code.

## 9. Deliverables

`graph_layer/character.py` (new — the two-register profile, divergence) · `graph_layer/scp.py` (complexity aggregation from Cv/Ov) · `graph_layer/structure.py` (legibility-tier graph measure) · `tests/test_stage4.py` (6 criteria, passing) · `SCF_character_demo.txt` (both buildings, full narration) · this report. Sources: Hillier 1996; Key & Gross 2021; Beck & Turkienicz 2009; Wiener et al. 2007; Franz & Wiener 2004; Dosen & Ostwald 2016/2017; Mustafa et al. 2010; Alfirević et al. 2026; Appleton 1984; Lynch 1960.
