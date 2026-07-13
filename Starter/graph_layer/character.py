"""
SCF graph_layer — Stage 4: the Unified Spatial Character Profile.

Turns the numbers SCF already produces into a defensible, professional reading
of a room's CHARACTER, in TWO REGISTERS that can agree or disagree:

  PERCEPTUAL   — what the room feels like from within
                 · prospect     (mean openness)      Franz & Wiener 2004;
                                                      Dosen & Ostwald 2016
                 · variety       (internal range)     Appleton 1984
                 · legibility    (clarity/navigability) Wiener et al. 2007
  CONFIGURATIONAL — where the room sits in the building's logic
                 · integration  (publicness)         Hillier 1996
                 · depth         (privacy gradient)   Hillier & Hanson 1984;
                                                      Robinson via Mustafa 2010
                 · choice        (through-movement)   Hillier 1996

DESIGN PRINCIPLES (agreed with the author, before build):
1. RELATIVE-FIRST, ABSOLUTE-SECOND. The primary reading ranks a room among the
   others in THIS building (Hillier's genotype: the ordering is the signature).
   A fixed absolute band rides alongside as a second, cross-room-legible layer.
2. COMPOSABLE, NOT FIXED TYPOLOGY. Character is assembled from whichever axes
   are pronounced (Key & Gross 2021), so new axes slot in as list entries — the
   configurational register is deliberately an EXTENSIBLE axis list, not a
   hardcoded three (control value, visual integration, RRA can be added later).
3. TWO REGISTERS, DETERMINISTIC DIVERGENCE. No language model. Divergence is a
   COMPUTED FLAG: when a room's perceptual-openness rank and its configurational
   -publicness rank differ by >= DIVERGENCE_MARGIN (as a fraction of room count),
   a pre-written TEMPLATE sentence fires with the room's own terms slotted in.
   The Flur is the worked case: visually enclosed (low prospect rank) yet most
   public (top integration rank) -> divergence template fires.
4. CLAIMS DISCIPLINE. Evidence is not uniform (Dosen & Ostwald 2016, 34 studies):
   prospect is best-supported, complexity/legibility second, refuge weak — so
   variety is spoken as internal RANGE, never as a 'refuge' benefit claim.
"""

from lexicon import (PROSPECT_BANDS, VARIETY_BANDS, band, depth_phrase,
                     display_name)

CARRIER = "EXTERIOR"
DIVERGENCE_MARGIN = 0.5   # fraction of room count; rank gap beyond this = diverge

# PERCEPTUAL complexity axis (0..100). Built from Cv/Ov (see scp.py): how
# broken-up and hidden-behind-thresholds the boundary is. HIGH = complex.
# Wiener et al. 2007 (vertices/occlusion -> complexity); Dosen & Ostwald 2016
# (2nd best-supported interior factor). Note this is the PERCEPTUAL reading —
# 'what the eye meets' — NOT reachability (that is Legibility, configurational).
COMPLEXITY_BANDS = [
    (55.0, "highly intricate", "the boundary is broken up, much hidden behind thresholds"),
    (40.0, "intricate",        "a visually broken-up boundary"),
    (25.0, "moderate",         "moderately articulated"),
    (0.0,  "plain",            "a plain, unbroken boundary"),
]

# CONFIGURATIONAL legibility = accessibility-in-reach (author's definition,
# Lynch register): shallow depth + reached by DIRECT connections rather than
# through intervening rooms. Reported as TIERS (ties allowed — keeps complex
# plans simple and honest): most-legible / direct-reach / indirect.
LEGIBILITY_TIERS = ["most legible", "direct-reach", "indirect", "deep-indirect"]

# The configurational register is an EXTENSIBLE list (principle 2). Each entry:
# (attribute, direction, relative-noun). direction +1 = high value ranks 1st.
CONFIG_AXES = [
    ("integration", +1, "publicness"),
    ("privacy",     +1, "privacy"),        # RRA + closability (structure.py)
    ("reach",       +1, "reachability"),   # threshold-cost + metric walk
    ("choice",      +1, "through-movement"),
]
PERCEPT_AXES = [
    ("prospect",   +1, "openness"),
    ("variety",    +1, "internal variety"),
    ("complexity", +1, "complexity"),
]


# ---------------------------------------------------------------------------
# ranking (relative-first)
# ---------------------------------------------------------------------------
def _rank_map(rooms, attr, direction):
    """rank 1 = most, among rooms with a non-None value for attr."""
    have = [(n, d[attr]) for n, d in rooms if d.get(attr) is not None]
    have.sort(key=lambda kv: -direction * kv[1])
    return {n: i + 1 for i, (n, _) in enumerate(have)}, len(have)


def annotate_character(B):
    """Attach the unified character profile to every room node of graph B.

    Adds per room:
      char_perceptual   dict(term, gloss, ranks{axis:rank}, absolute{axis:band})
      char_config       dict(term, gloss, ranks{axis:rank}, absolute{axis:band})
      char_divergence   None, or a dict(fires=True, sentence, gap, ...)
    Returns B (mutated).
    """
    rooms = [(n, d) for n, d in B.nodes(data=True) if d.get("kind") == "room"]
    n_rooms = len(rooms)

    # precompute rank maps for every axis in both registers
    ranks = {}
    for attr, direction, _ in PERCEPT_AXES + CONFIG_AXES:
        ranks[attr], _ = _rank_map(rooms, attr, direction)

    for n, d in rooms:
        # ---- perceptual register ----
        p_ranks = {a: ranks[a].get(n) for a, _, _ in PERCEPT_AXES}
        p_abs = {}
        if d.get("prospect") is not None:
            p_abs["prospect"] = band(d["prospect"], PROSPECT_BANDS)[0]
        if d.get("variety") is not None:
            p_abs["variety"] = band(d["variety"], VARIETY_BANDS)[0]
        if d.get("complexity") is not None:
            p_abs["complexity"] = band(d["complexity"], COMPLEXITY_BANDS)[0]
        d["char_perceptual"] = dict(ranks=p_ranks, absolute=p_abs,
                                    summary=_percept_summary(d, p_abs, p_ranks, n_rooms))

        # ---- configurational register ----
        c_ranks = {a: ranks[a].get(n) for a, _, _ in CONFIG_AXES}
        d["char_config"] = dict(ranks=c_ranks,
                                summary=_config_summary(d, c_ranks, n_rooms))

        # ---- divergence: perceptual complexity vs configurational reach ----
        d["char_divergence"] = _divergence(d, n_rooms)

    return B


# ---------------------------------------------------------------------------
# register summaries (deterministic template fill — no LM)
# ---------------------------------------------------------------------------
def _ordinal_word(rank, total):
    if rank is None:
        return None
    if rank == 1:
        return "most"
    if rank == total:
        return "least"
    if rank <= max(1, total // 3):
        return "among the more"
    if rank > total - max(1, total // 3):
        return "among the less"
    return "mid-range in"


def _percept_summary(d, p_abs, p_ranks, total):
    if d.get("prospect") is None:
        return None
    hedge = "" if d.get("reliable", True) else "indicatively "
    op = p_abs.get("prospect", "?")            # absolute openness term
    var = p_abs.get("variety", "?")            # absolute variety term
    cx = p_abs.get("complexity")               # absolute complexity term
    cx_txt = f", {cx}" if cx else ""
    rel = _ordinal_word(p_ranks.get("prospect"), total)
    rel_txt = f" ({rel} open of the plan's rooms)" if rel else ""
    return f"{hedge}reads {op}, {var}{cx_txt}{rel_txt}"


def _config_summary(d, c_ranks, total):
    parts = []
    ir = c_ranks.get("integration")
    if ir is not None:
        parts.append(f"{_ordinal_word(ir, total)} integrated (publicness)")
    if d.get("privacy") is not None:
        parts.append(f"privacy {d['privacy']:.0f} — {d['privacy_word']} "
                     f"(segregation RRA {d['rra']:.2f} · "
                     f"{d['barrier']:.1f} closable behind you)")
    if d.get("reach") is not None:
        parts.append(f"reachability {d['reach']:.0f} "
                     f"(barriers {d['reach_cost']:.2f} · walk {d['walk_m']:.1f} m)")
    cr = c_ranks.get("choice")
    if cr == 1:
        parts.append("carries the most through-movement")
    return "; ".join(parts) if parts else None


def _legibility_word(tier):
    return {0: "most legible — opens to everything",
            1: "directly reachable off the hub",
            2: "reached through another space"}.get(
        tier, f"deeply indirect ({tier} steps in)")


def _hillier_depth_word(depth, d):
    # Robinson territorial register (via Mustafa et al. 2010), mapped to depth
    return {0: "the carrier", 1: "shallow/public", 2: "semi-private",
            3: "private", 4: "deep/private", 5: "innermost"}.get(
        depth, f"{depth} steps deep")


# ---------------------------------------------------------------------------
# divergence — the stage's signature insight, fully deterministic (no LM).
# Watches PERCEPTUAL complexity vs CONFIGURATIONAL reachability: a room can be
# visually complex (hard to SEE through) yet highly reachable (easy to move
# through) — the Flur. Rank-gap method (author's choice).
# ---------------------------------------------------------------------------
def _divergence(d, total):
    """Deterministic rank-gap flags on the CONTINUOUS measures:
    · complex_yet_reachable — among the most visually complex AND highly
      reachable (reach >= 80): the control/threshold role (the Flur case).
    · plain_yet_secluded — among the visually plainest AND deeply private
      (privacy >= 80): the withdrawn retreat."""
    if d.get("complexity") is None:
        return None
    cx_rank = d["char_perceptual"]["ranks"].get("complexity")
    if cx_rank is None or total < 3:
        return None
    name = display_name(d)
    cx_high = cx_rank <= max(1, total // 2)   # above-median complexity
    cx_low = cx_rank > total - max(1, total // 3)
    if cx_high and (d.get("reach") or 0) >= 80:
        return dict(fires=True, kind="complex_yet_reachable",
                    sentence=(f"{name} is visually complex yet among the most "
                              f"reachable spaces — hard to read through, easy "
                              f"to move through: a control/threshold role."))
    if cx_low and (d.get("privacy") or 0) >= 80:
        return dict(fires=True, kind="plain_yet_secluded",
                    sentence=(f"{name} reads plain and clear yet is held "
                              f"deepest by the plan — a simple room behind "
                              f"many barriers: a withdrawn retreat."))
    return None


# ---------------------------------------------------------------------------
# narration
# ---------------------------------------------------------------------------
def character_sentences(B):
    """Full two-register narration for a building graph (already annotated)."""
    rooms = [(n, d) for n, d in B.nodes(data=True) if d.get("kind") == "room"]
    rooms.sort(key=lambda x: (x[1].get("depth") is None, x[1].get("depth") or 0,
                              x[1].get("name") or ""))
    lines = []
    for _, d in rooms:
        if d.get("prospect") is None and not d.get("is_stair"):
            continue
        nm = display_name(d)
        if d.get("is_stair"):
            lines.append(f"• {nm}: stair volume (connective node; character not scored).")
            continue
        p = d["char_perceptual"]["summary"]
        c = d["char_config"]["summary"]
        lines.append(f"• {nm}")
        if p:
            lines.append(f"    perceptual:      {p}")
        if c:
            lines.append(f"    configurational: {c}")
        dv = d.get("char_divergence")
        if dv:
            lines.append(f"    ⚡ divergence:    {dv['sentence']}")
    return "\n".join(lines)
