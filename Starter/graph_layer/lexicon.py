"""
SCF graph_layer — Stage 3: the interpretive lexicon.

THE ACADEMIC/PROFESSIONAL SKELETON for SCP data: every number the framework
produces is bound here to (a) a banded professional term, (b) the source that
licenses the term, and (c) the sentence grammar the instrument uses to speak
to designers. Later stages (change loop, principle flags, Pset write-back)
consume THIS module — language and code cannot drift apart.

DESIGN PRINCIPLES
1. No invented jargon: every term traces to a citable tradition —
   Hillier & Hanson 1984 (depth, shallow/deep, carrier);
   Alexander et al. 1977, Pattern 127 'Intimacy Gradient' (depth-as-privacy);
   Cullen 1961, serial vision (transition vocabulary) with Appleton 1984;
   Ching 1979/2014 degrees of enclosure (openness adjectives);
   Franz & Wiener 2004 / Dosen & Ostwald 2016 (spaciousness, complexity,
   prospect, refuge — the empirical register) — or to the model's own
   internal class structure (below).
2. Derived thresholds, not arbitrary ones: the capstone's five typologies
   sit on a 25-point Quality ladder (0/25/50/75/100). Prospect bands are the
   MIDPOINT BOUNDARIES of that ladder (12.5/37.5/62.5/87.5): a band change
   means the room's central tendency crossed into another of the model's own
   classes. Jump bands are expressed in LADDER UNITS: a 'marked' transition
   is on the order of one class; a 'dramatic' one approaches two classes.
   Variety bands are corpus-calibrated conventions and are FLAGGED as such
   (provisional, designer-tunable) — claims discipline, not false precision.
3. Two voices: informative (default, descriptive) and bold (only when a
   designer-declared principle is broken — Stage 5). This module renders the
   informative voice and exposes the hooks the bold voice will use.
4. Hedged uncertainty: rooms below sampling support (reliable=False) receive
   'indicatively …' phrasing automatically. The instrument never sounds more
   certain than its data.
"""

# ---------------------------------------------------------------------------
# PROSPECT — degrees of enclosure/openness (Ching; Franz & Wiener spaciousness)
# Bands derived from the model's own class ladder midpoints.
# ---------------------------------------------------------------------------
PROSPECT_BANDS = [
    (87.5, "expansive",  "reads as expansive — strong outlook throughout"),
    (62.5, "open",       "reads as open"),
    (37.5, "semi-open",  "reads as semi-open"),
    (12.5, "intimate",   "reads as intimate and enclosed"),
    (0.0,  "confined",   "reads as confined — tightly enclosed"),
]

# ---------------------------------------------------------------------------
# VARIETY — within-room experiential range (complexity/visual variety:
# Dosen & Ostwald 2016; prospect–refuge mix as interpretive frame: Appleton).
# Thresholds are corpus-calibrated CONVENTIONS (provisional, tunable).
# ---------------------------------------------------------------------------
VARIETY_BANDS = [
    (25.0, "contrasting", "with strongly contrasting zones — prospect beside refuge"),
    (15.0, "varied",      "with distinctly varied zones"),
    (6.0,  "graded",      "with a gentle internal gradient"),
    (0.0,  "uniform",     "uniform in character throughout"),
]
VARIETY_PROVISIONAL = True   # thresholds are conventions, not perceptual constants

# ---------------------------------------------------------------------------
# CHARACTER QUADRANTS — the two axes jointly (professional shorthand).
# Echoes: Turner et al. 2001 (uniform open spaces read 'hall-like');
# Appleton (refuge pockets); the project's own two-axis construct.
# ---------------------------------------------------------------------------
def character(prospect_term, variety_term):
    open_side = prospect_term in ("expansive", "open")
    plural = variety_term in ("varied", "contrasting")
    if open_side and not plural:
        return "open and legible — a hall-like clarity"
    if open_side and plural:
        return "a room of zones — outlook with pockets of shelter"
    if not open_side and not plural:
        return "a calm retreat"
    return "intricate seclusion — sheltered, with inner variety"

# ---------------------------------------------------------------------------
# DEPTH — Hillier & Hanson justified depth from the carrier;
# Alexander Pattern 127 'Intimacy Gradient' as the practitioner register.
# ---------------------------------------------------------------------------
def depth_phrase(d, d_max):
    if d is None:
        return None   # handled by the sentence: unreachable clause
    if d == 0:
        return "the carrier itself"
    ordinal = {1: "one threshold", 2: "two thresholds", 3: "three thresholds"}.get(
        d, f"{d} thresholds")
    base = f"{ordinal} deep from the entrance"
    if d == 1:
        return base + " — directly off the entry (shallow, public end of the intimacy gradient)"
    if d_max and d == d_max and d >= 3:
        return base + " — among the deepest, most private rooms of the plan"
    return base

# ---------------------------------------------------------------------------
# JUMP — transition sharpness at thresholds (Cullen 1961 serial vision;
# Appleton 1984). Bands in ladder units: ~one class = 'marked'.
# ---------------------------------------------------------------------------
JUMP_BANDS = [
    (45.0, "dramatic",  "a dramatic reveal — the character changes by nearly two classes as you cross"),
    (20.0, "marked",    "a marked transition — about one character class"),
    (8.0,  "eased",     "an eased transition"),
    (0.0,  "seamless",  "a seamless continuation — the spaces flow as one"),
]

def band(value, bands):
    if value is None:
        return None, None
    for lo, term, gloss in bands:
        if value >= lo:
            return term, gloss
    return bands[-1][1], bands[-1][2]

# ---------------------------------------------------------------------------
# SENTENCE GRAMMAR — the informative voice.
# ---------------------------------------------------------------------------
def display_name(node):
    """Disambiguate repeated long names (mirrored units) with the space code."""
    ln, nm = node.get("long_name", "?"), node.get("name")
    return f"{ln} ({nm})" if nm and str(nm) != ln else ln


def room_sentence(node, d_max=None, dname=None):
    """One professional sentence for a room node (SCP dict from scp.py)."""
    name = dname or display_name(node)
    if node.get("is_stair"):
        return (f"{name} is a stair volume — carried as a connective node "
                f"(no in-room character is scored, by design).")
    if node.get("prospect") is None:
        d = node.get("depth")
        if d is not None:
            return (f"{name}: character not yet scored (storey field pending); "
                    f"it sits {depth_phrase(d, d_max)}.")
        return f"{name}: no evaluated points."
    p_term, _ = band(node["prospect"], PROSPECT_BANDS)
    v_term, _ = band(node["variety"], VARIETY_BANDS)
    quad = character(p_term, v_term)
    hedge = "" if node.get("reliable", True) else "indicatively "
    support = "" if node.get("reliable", True) else \
        " (small room — low sampling support)"
    d = node.get("depth")
    if d is None:
        dep = ("it is not reachable from the chosen entrance(s) — "
               "confirm entrance selection, or a vertical link is pending")
    else:
        dep = f"it sits {depth_phrase(d, d_max)}"
    return (f"{name} {hedge}reads {p_term} and {v_term} — {quad}; "
            f"{dep}.{support}")

def threshold_sentence(name_a, name_b, edge, stair_side=False):
    """One professional sentence for a threshold (edge dict from scp.py)."""
    j = edge.get("jump")
    k = edge.get("kind", "door")
    w = edge.get("width")
    kindtxt = "doorway" if k == "door" else "open passage"
    wtxt = f" ({w:.2f} m clear)" if w else ""
    if stair_side:
        return (f"The {kindtxt} between {name_a} and {name_b}{wtxt} "
                f"leads to the stair volume (transitions to stairs are not "
                f"characterised — the stair carries movement, not room character).")
    if j is None:
        return f"The {kindtxt} between {name_a} and {name_b}{wtxt}: transition unmeasured."
    _, j_gloss = band(j, JUMP_BANDS)
    src = "" if edge.get("jump_source", "local") == "local" else \
        " [room-average estimate — sparse threshold sampling]"
    return (f"Crossing the {kindtxt} between {name_a} and {name_b}{wtxt} is "
            f"{j_gloss} (Δ {j:.0f}).{src}")


def describe_graph(G):
    """Full informative-voice narration of one storey's SCP graph."""
    rooms = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "room"]
    depths = [d.get("depth") for _, d in rooms if d.get("depth") is not None]
    d_max = max(depths) if depths else None
    lines = [building_summary(G), ""]
    for n, d in sorted(rooms, key=lambda x: (x[1].get("depth") is None,
                                             x[1].get("depth") or 0,
                                             x[1].get("long_name", ""))):
        lines.append("• " + room_sentence(d, d_max))
    lines.append("")
    lines.append("Thresholds:")
    for a, b, e in G.edges(data=True):
        da, db = G.nodes[a], G.nodes[b]
        if da.get("kind") == "carrier" or db.get("kind") == "carrier":
            continue
        stair_side = da.get("is_stair") or db.get("is_stair")
        lines.append("  – " + threshold_sentence(display_name(da),
                                                 display_name(db), e,
                                                 stair_side=stair_side))
    return "\n".join(lines)

def building_summary(G):
    """Short structural summary in Hillier/Alexander register."""
    rooms = [d for _, d in G.nodes(data=True) if d.get("kind") == "room"]
    depths = [d.get("depth") for d in rooms if d.get("depth") is not None]
    if not depths:
        return "No entrance chosen yet — the intimacy gradient is undefined."
    d_max = max(depths)
    shallow = [d["long_name"] for d in rooms if d.get("depth") == 1]
    deep = [d["long_name"] for d in rooms if d.get("depth") == d_max]
    guess = " (entrance auto-selected — please confirm)" if \
        G.graph.get("entrance_is_guess") else ""
    return (f"The plan is {d_max} threshold(s) deep{guess}. "
            f"Shallow, public end: {', '.join(shallow)}. "
            f"Deepest: {', '.join(deep)}.")

# ---------------------------------------------------------------------------
# SKELETON TABLE (machine-readable: report + Pset write-back share this)
# ---------------------------------------------------------------------------
SKELETON = {
    "prospect": dict(construct="perceived openness / spaciousness",
                     bands=PROSPECT_BANDS,
                     derived_from="model class ladder midpoints (12.5/37.5/62.5/87.5)",
                     sources=["Benedikt 1979", "Franz & Wiener 2004",
                              "Wiener et al. 2007", "Dosen & Ostwald 2016",
                              "Ching 1979 (enclosure register)"]),
    "variety": dict(construct="within-room experiential range (complexity/variety)",
                    bands=VARIETY_BANDS, provisional=VARIETY_PROVISIONAL,
                    derived_from="corpus-calibrated convention (tunable)",
                    sources=["Dosen & Ostwald 2016", "Appleton 1975 (frame)"]),
    "depth": dict(construct="justified-graph depth from carrier (privacy as position)",
                  derived_from="topological step count",
                  sources=["Hillier & Hanson 1984",
                           "Alexander et al. 1977, Pattern 127"]),
    "jump": dict(construct="serial-vision transition sharpness at thresholds",
                 bands=JUMP_BANDS,
                 derived_from="ladder units (~25 pts per character class)",
                 sources=["Cullen 1961", "Appleton 1984"]),
    "exterior_touch": dict(construct="carrier exposure (recorded; deferred axis)",
                           derived_from="metres of outer-boundary frontage",
                           sources=["Hillier & Hanson 1984 (carrier)"]),
}
