# Stage 2 — The Spatial Character Profile (plain-language report)

*What I built in Stage 2, why, and how it helps us — explained simply, with real numbers from our two test buildings. Still technical, just readable.*

---

## 1. What this stage was for

Before Stage 2 we had two separate things that didn't talk to each other:

- **Thousands of scored points** (from Stage 0) — every walkable spot in the building has an openness score from 0 to 100. Too fine-grained to reason about; nobody thinks "point #2043 is a 74."
- **A room map with connections** (from Stage 1) — we know each room's name, shape, and which rooms connect to which. But the rooms were empty labels; they had no idea how open or enclosed they felt.

Stage 2 joins these two. It takes the cloud of scored points, sorts them into their rooms, and turns each room into a small **profile** — a handful of numbers that describe that room's spatial character. That profile is called the **Spatial Character Profile (SCP)**, and it's the heart of the whole project.

## 2. The key step: sorting points into rooms

The first thing the code does (`assign_points`) is simple: for each scored point, find which room contains it, and tag the point with that room.

Real result on FZK Haus: **98.7% of points got sorted into a room.** The other 1.3% sit in doorway gaps — they don't belong to any room, they belong to thresholds, so we leave them unassigned on purpose rather than forcing them somewhere wrong.

**Why this step matters so much:** once each room owns its own pile of scores, we can ask questions about that pile. This is the step that makes everything else possible — especially the "how complex is this room" measure you asked about (see §4).

## 3. What each room's profile contains

For every room we now compute these values. Here are three real FZK rooms so you can see what they mean:

| Room | Prospect | Variety | Depth | Points |
|---|---|---|---|---|
| **Küche** (kitchen) | 99.9 | 0.6 | 2 | 437 |
| **Schlafzimmer** (bedroom) | 66.3 | 32.6 | 2 | 567 |
| **Büro** (office) | 10.5 | 19.4 | 2 | 342 |

**Prospect** = the *average* openness of the room's points. High = open and airy, low = enclosed. Küche is 99.9 (wide open); Büro is 10.5 (tight and enclosed). This is the best-supported idea in the research — openness/spaciousness is what isovist area measures, and it's what people most reliably respond to.

**Variety** = the *spread* of the room's points — how much they differ from each other. This is the "complexity relative to itself" number. Küche's variety is 0.6, meaning every spot in the kitchen feels almost identical — a simple, uniform room. Schlafzimmer's variety is 32.6, meaning the bedroom contains a real mix of open and sheltered spots — a richer, more varied room. Same idea as prospect-refuge: a room with high variety gives you both a view and a nook.

**Depth** = how many doorways you cross to reach this room from the front door. The entrance hall (Flur) is depth 1; every other room is depth 2 (one more door in). This is the privacy measure — deeper = more private — and it comes straight from the room connections, not from the room's shape. It's a 50-year-old method from architectural theory (Hillier's "justified graph"), so it's solid ground.

*(We also store the typology mix — what percentage of the room is each of the five categories — and the room's area and number of connections, but Prospect / Variety / Depth are the three you'll mostly reason with.)*

## 4. Your question answered: how we measure "complexity relative to itself"

This is worth its own section because you asked directly.

**Complexity of a room relative to itself = the Variety number = the spread of that room's own points.** Nothing else. We are *not* comparing the room to other rooms or to other floorplans for this measure. We look only at the room's own pile of scores and ask: do they all agree, or do they disagree?

- All points similar → low variety → simple, uniform room (Küche, 0.6)
- Points disagree a lot → high variety → complex room with mixed zones (Schlafzimmer, 32.6)

And this is *only possible because of §2* — the point-sorting step. If we never tagged points with their rooms, we'd have one big pile of scores for the whole building and no way to isolate "just the kitchen's points." So the assignment step isn't a side-detail; it's the thing that unlocks the whole self-relative complexity idea.

(There's also a second, cross-check version of complexity called `mix_entropy` — it measures complexity by counting how many different *categories* the room mixes. Küche = 0.0 entropy, one category only. Schlafzimmer = 1.85, genuinely mixed. It agrees with Variety, which is reassuring — two different methods pointing the same way.)

## 5. The connections between rooms (edges) carry information too

We don't just profile rooms — we profile the *doorways and openings* between them. Each connection stores:

- **kind** — is it a real door, or an open archway?
- **width** — how wide the passage is (measured from the geometry)
- **jump** — how big the openness *change* is when you cross it

Real FZK examples:
- **Büro → Flur**: jump of **70** — you step from a tight office straight into a bright hall. A dramatic transition.
- **Wohnen → Flur** (an archway, no door): jump of **2** — the living room and hall basically flow into each other. Barely a transition at all.

That jump number is how the tool will eventually spot "this design has a jarring transition here" or "this one flows gently." It's measured at the doorway because that's where you actually *experience* the change.

## 6. Proof it works — the nice results

**The kitchen/bedroom contrast is architecturally true.** The tool independently found that FZK's kitchen is uniform and its bedroom is varied — which matches what any architect would say looking at the plan. We didn't tell it that; it computed it.

**The mirrored apartment is the best proof.** Duplex has two identical mirror-image units. If our profiles are trustworthy, the two units should score nearly the same. They do: the two living rooms scored 96.6 and 97.0; the two kitchens 98.0 and 97.9 — within one point. That's a natural consistency check we got for free from the test file, and it passed.

**The depths match theory exactly.** The privacy depths we computed match what you'd get drawing the justified graph by hand.

## 7. Two real problems I hit and fixed (so you understand what changed in the files)

**Problem 1 — a stair room named "Room."** Duplex's second unit has a staircase whose space is mislabeled "Room" instead of "Stair." My first version only checked *names*, so it missed it and tried to score the space under the stairs (which is meaningless). **Fix:** now I check *geometry too* — if a staircase physically sits inside a space, it's a stair space regardless of its name. Names lie; geometry doesn't.

**Problem 2 — invisible staircases.** In IFC files, a staircase is often an empty "container" whose actual steps are stored as separate child pieces. My code looked at the container, found no geometry, and saw nothing. **Fix:** now I open the container and read its child pieces. *(Honest note: the Duplex scores we have were computed before this fix, so when we rescore in Stage 3 the Duplex entrance numbers will shift a little. The room structure and depths don't change — only some openness values near the stair.)*

## 8. How this helps us going forward

Every later stage stands on this profile:

- **Stage 3 (structure)** adds the vertical stair connections and computes which room is the "hub" of the building — using the same graph we just built.
- **Stage 4 (the change loop)** compares two profiles — before an edit and after — to show what a design change did. That only works because a room is now a set of numbers we can compare.
- **Stage 5 (principles)** lets you say "bedrooms should be depth 2+ and low-prospect" and checks each room's profile against your rule.
- **Write-back** saves each room's profile back into the BIM model as real data.

In short: Stage 2 turned the building from "a picture with scores" into "a set of rooms that each know their own character and how they connect." That's the thing the whole tool reasons with from here on.

## 9. What's still rough (honest list)

1. **Prospect is relative to each plan**, so you can't compare a kitchen in one building to a kitchen in another — only rooms *within the same design*. Fine for our purpose (comparing design options), but a real limit to remember.
2. **Variety needs enough points to be trustworthy.** Tiny rooms (a 3 m² bathroom with 12 points) get a variety number that's basically noise — we flag these as "not reliable" so you know not to trust them.
3. **Stairs still aren't connections yet** — that's Stage 3's job. Right now Duplex's upstairs is correctly shown as "unreachable" rather than wrongly connected.
4. **The Duplex scores predate Problem-2's fix** — a known, written-down thing to rescore, not a hidden bug.

## 10. Files in this delivery

- `graph_layer/scp.py` — the new profile-building code (§2–5)
- `tests/test_stage2.py` — checks all of the above automatically (passing)
- `ifc_layer/ifc_reader.py` — updated with the two stair fixes (§7)
- `core/scoring.py` — re-delivered (an earlier fix hadn't reached the repo)
- `tests/test_stage1.py` — restored (had gone missing from the repo)
- `FZK_SCP_graph.png` — the picture of the room profiles on the connection map
- the two score fields as CSVs — so we can experiment without re-running the slow scoring




# Stage 2 Addendum v2 — Depth, Entrance & Jump refinements
*Prompted by architect review of the SCP values. All Stage 2 tests + full regression pass.*

## Issue 1 — Depth was wrong because an exterior door was mis-wired (root cause found)
The architect flagged Küche's depth as suspect. Investigation revealed the true fault:
FZK's **Terrassentür** (terrace door, Wohnen→garden) was being recorded as an INTERNAL
Wohnen↔Küche door. Cause: the door's 0.30 m association buffer grazed Küche's corner
with a numerically-zero (0.000 m²) overlap, so `len(touching)==2` fired and it became an
internal edge instead of an exterior entrance. This corrupted the entire depth graph.
**Fix:** door↔space association now requires a MEANINGFUL overlap (>0.02 m²), ignoring
float-hairline grazes. Both exterior doors are now correctly detected.

## Issue 2 — Which door is the entrance? (designer choice + honest auto-default)
Per architect decision: **the designer designates entrance(s) per project** (one or
several — front + back doors, complex plans); if unspecified, the tool auto-picks the
PRIMARY entrance and flags it as a guess (`entrance_is_guess=True`) so the UI can prompt
confirmation. Auto-heuristic order: (1) door NAME hint (haust/front/entrance/eingang…),
(2) the sole exterior door, (3) widest — width LAST, because a terrace door is often
wider than a front door (FZK: terrace 2.01 m vs front 1.01 m; naive width picked wrong).
With the front door chosen, depths are architecturally correct and confirmed by the
architect: Flur=1, all other rooms=2. Designer selecting BOTH doors gives the pure-
Hillier reading (Wohnen & Flur=1; all others=2) — both supported, designer decides.

## Issue 3 — Jump upgraded from room-average to local-at-threshold (Appleton 1984)
Jump measured character change using whole-room averages, which misrepresents the
transition you actually feel at a doorway. New **primary jump = local**: mean Quality of
scored points within 0.9 m of the threshold on each side; **fallback = average** where a
threshold lacks ≥3 near points per side. Both are stored (`jump_local`, `jump_avg`,
`jump_source`). The upgrade proved its worth on FZK: Wohnen↔Küche reads **0.0 local vs
16.5 average** — the wide opening IS a seamless transition, which room-averages hid; and
Bad↔Flur reads **49.7 local vs 36.6 average** — a sharper doorway than averages suggest.
Architect confirmed local-primary.

## Issue 4 — Carrier exposure recorded (D10), deferred as a factor
Per architect decision (defer-but-record): each room now stores `exterior_touch` —
metres of its frontage on the building's outer boundary (Wohnen 12.0 m, Bad 4.0 m,
internal-only rooms ~0). This is the raw material for a future second privacy axis
(circulation-depth vs environmental-exposure) without rework; not yet used in scoring.
Data before judgment — same discipline as edge widths.

## Files changed
`ifc_layer/ifc_reader.py` — meaningful-overlap door association (Issue 1) +
exterior_touch recording (D10). `graph_layer/scp.py` — designer/auto entrances with
guess flag + name-hint heuristic (Issue 2), local/average jump (Issue 3), exterior_touch
on nodes. `tests/test_stage2.py` — entrance, jump-source, exterior-touch assertions added.
