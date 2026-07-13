"""
SCF graph_layer — Stage 3B: the building as ONE structure.

Per-storey SCP graphs become a single building-wide graph:

1. VERTICAL EDGES (kind='stair'): a stair connects the space that hosts it
   on storey i to the space its footprint lands in on storey i+1. Endpoint
   on the lower storey = the stair SPACE node if one exists (this is why
   stair nodes were kept as depth-only connectors all along), else the room
   containing the stair element. Endpoint above = the space overlapping the
   stair footprint. Doors, openings and stairs are all one topological step
   (consistent with the agreed Hillier-faithful depth convention).

2. ONE CARRIER: every storey graph shares the 'EXTERIOR' node, so composing
   them yields a single carrier and depths recompute building-wide — a
   first-floor bedroom is now honestly N thresholds deep THROUGH the stair.

3. STRUCTURAL MEASURES (Hillier & Hanson; departmental vocabulary S03-07):
   integration  = closeness centrality on the room graph — how few steps the
                  room is from everywhere else; the 'social hub' measure.
   choice       = betweenness centrality — how much through-movement the
                  room carries; the 'corridor' measure.
   Both are reported RELATIVELY (ranks within the building), which is the
   defensible register for small graphs: 'the most integrated room of the
   plan', not a pseudo-absolute score.
"""

import networkx as nx
from shapely.geometry import Point

CARRIER = "EXTERIOR"


def _stair_anchors(storey, G):
    """[(anchor_node_guid, footprint)] for every stair presence on a storey:
    stair SPACE nodes where they exist, else the room hosting the element."""
    anchors = []
    stair_spaces = [r for r in storey["spaces"] if r.get("is_stair")]
    for r in stair_spaces:
        anchors.append((r["guid"], r["poly"]))
    if not stair_spaces and not storey["stair_obstacle"].is_empty:
        c = storey["stair_obstacle"].centroid
        host = next((r for r in storey["spaces"] if r["poly"].contains(c)), None)
        if host:
            anchors.append((host["guid"], storey["stair_obstacle"]))
    return anchors


def _space_at(storey, geom):
    """The space on a storey that best receives a footprint from below.
    Three tiers: (1) contains the centroid; (2) largest area overlap;
    (3) longest SHARED BOUNDARY — stairwells are often open voids on the
    upper storey, so the stair arrives BESIDE its landing space (Duplex:
    the L2 Hallway adjoins the void with zero overlap)."""
    c = geom.centroid
    direct = next((r for r in storey["spaces"] if r["poly"].contains(c)), None)
    if direct:
        return direct["guid"]
    best, best_ov = None, 0.0
    for r in storey["spaces"]:
        ov = r["poly"].intersection(geom).area
        if ov > best_ov:
            best, best_ov = r["guid"], ov
    if best_ov > 0.2:
        return best
    rim = geom.buffer(0.15).boundary
    best, best_len = None, 0.0
    for r in storey["spaces"]:
        shared = r["poly"].buffer(0.05).intersection(geom.buffer(0.15))
        if shared.area > 0 and shared.length > best_len:
            best, best_len = r["guid"], shared.length
    return best if best_len > 0.5 else None


def build_building_graph(storeys, storey_graphs):
    """Compose per-storey SCP graphs into one building graph with vertical
    stair edges, then recompute carrier depth and structural measures.

    storeys:       list of Stage 1 extraction dicts (ordered by elevation)
    storey_graphs: matching list of Stage 2 SCP graphs
    Returns the composed nx.Graph.
    """
    B = nx.Graph()
    for G in storey_graphs:
        B = nx.compose(B, G)          # shared CARRIER label merges to one

    # vertical edges between consecutive storeys
    for i in range(len(storeys) - 1):
        lower, upper = storeys[i], storeys[i + 1]
        for anchor, footprint in _stair_anchors(lower, storey_graphs[i]):
            landing = _space_at(upper, footprint)
            if landing and B.has_node(anchor) and B.has_node(landing):
                fc = footprint.centroid
                B.add_edge(anchor, landing, kind="stair", width=None,
                           jump=None, jump_local=None, jump_avg=None,
                           jump_source=None,
                           thresh_xy=(round(fc.x, 3), round(fc.y, 3)),
                           door_guid=None)

    # building-wide depth from the single carrier
    entrances_exist = any(B.has_edge(n, CARRIER) for n in B.neighbors(CARRIER)) \
        if B.has_node(CARRIER) else False
    lengths = nx.single_source_shortest_path_length(B, CARRIER) \
        if B.has_node(CARRIER) else {}
    for n in B.nodes:
        if B.nodes[n].get("kind") == "room":
            B.nodes[n]["depth"] = lengths.get(n)

    # structural measures on the room graph (carrier excluded from ranking)
    rooms = [n for n in B.nodes if B.nodes[n].get("kind") == "room"]
    sub = B.subgraph(rooms + ([CARRIER] if B.has_node(CARRIER) else []))
    integ = nx.closeness_centrality(sub)
    choice = nx.betweenness_centrality(sub, normalized=True)
    ranked_i = sorted(rooms, key=lambda n: -integ.get(n, 0))
    ranked_c = sorted(rooms, key=lambda n: -choice.get(n, 0))
    for n in rooms:
        B.nodes[n]["integration"] = round(integ.get(n, 0), 4)
        B.nodes[n]["choice"] = round(choice.get(n, 0), 4)
        B.nodes[n]["integration_rank"] = ranked_i.index(n) + 1
        B.nodes[n]["choice_rank"] = ranked_c.index(n) + 1
    B.graph["n_rooms"] = len(rooms)
    B.graph["entrances"] = sorted({e for G in storey_graphs
                                   for e in G.graph.get("entrances", [])})
    B.graph["entrance_is_guess"] = any(G.graph.get("entrance_is_guess")
                                       for G in storey_graphs)
    _assign_legibility_tiers(B, rooms)
    _privacy_and_reach(B, rooms)
    return B


# ---------------------------------------------------------------------------
# PRIVACY and REACHABILITY — the two-component formulas (author-approved).
#
# PRIVACY = 0.5·segregation + 0.5·closability, each normalised 0–100 within
# the building (the gradient is building-relative, per the genotype method):
#   segregation  = RRA — Hillier's size-normalised mean depth (relative
#                  asymmetry over the diamond value), the literature-standard
#                  'how deep does the plan hold this room from everywhere'.
#   closability  = how much of the entrance path can be SHUT behind you:
#                  door 1.0 (closable leaf) · stair 0.8 (level change, no
#                  leaf) · opening 0.35 (a permanent leak — cannot close).
# Words on the Robinson territorial register (via Mustafa et al. 2010),
# assigned by within-building quantile.
#
# REACHABILITY = 0.5·topological + 0.5·metric (Hillier & Iida 2005: the two
# distance concepts are genuinely different and both felt):
#   topological  = threshold-weighted cost of the easiest way in
#                  (door 1.0 · opening 0.55 · stair 1.6), plus a small bonus
#                  for route redundancy (more ways in = easier to reach).
#   metric       = actual walking distance from the chosen entrance, chained
#                  threshold-to-threshold to the room centre.
# Coefficients are reasoned conventions, tunable (Stage-5 sliders).
# ---------------------------------------------------------------------------
import math
from itertools import islice

CLOS = {"door": 1.0, "stair": 0.8, "opening": 0.35}
REACH_W = {"door": 1.0, "opening": 0.55, "stair": 1.6}
PRIVACY_WORDS = [(80, "innermost/intimate"), (60, "private"),
                 (40, "semi-private"), (20, "semi-public"), (0, "public")]


def _diamond(k):
    if k <= 2:
        return 1.0
    return 2 * (k * (math.log2((k + 2) / 3) - 1) + 1) / ((k - 1) * (k - 2))


def _norm(vals):
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return [50.0] * len(vals)
    return [100.0 * (v - lo) / (hi - lo) for v in vals]


def _privacy_and_reach(B, rooms):
    reach_rooms = [n for n in rooms
                   if B.has_node(CARRIER) and nx.has_path(B, CARRIER, n)]
    for n in rooms:                      # graceful default for the stranded
        for f in ("rra", "mean_depth", "barrier", "privacy", "privacy_word",
                  "reach_cost", "walk_m", "reach"):
            B.nodes[n][f] = None
    if len(reach_rooms) < 3:
        return
    Bw = B.copy()
    for a, b, d in Bw.edges(data=True):
        Bw.edges[a, b]["w"] = REACH_W.get(d.get("kind"), 1.0)
    R = B.subgraph(reach_rooms)
    k = len(reach_rooms)
    seg, bar, cost, walk = [], [], [], []
    for n in reach_rooms:
        sp = nx.single_source_shortest_path_length(R, n)
        md = sum(sp.values()) / max(1, len(sp) - 1)
        ra = 2 * (md - 1) / (k - 2) if k > 2 else 0.0
        rra = ra / _diamond(k)
        path = nx.shortest_path(Bw, CARRIER, n, weight="w")
        c = sum(REACH_W.get(B.edges[path[i], path[i + 1]].get("kind"), 1.0)
                for i in range(len(path) - 1))
        b_ = sum(CLOS.get(B.edges[path[i], path[i + 1]].get("kind"), 1.0)
                 for i in range(len(path) - 1))
        pts = []
        for i in range(len(path) - 1):
            t = B.edges[path[i], path[i + 1]].get("thresh_xy")
            if t:
                pts.append(t)
        cen = B.nodes[n].get("centroid")
        if cen:
            pts.append(cen)
        w = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))             if len(pts) > 1 else 0.0
        alt = len(list(islice(nx.all_simple_paths(B, CARRIER, n, cutoff=5), 25)))
        B.nodes[n]["mean_depth"] = round(md, 2)
        B.nodes[n]["rra"] = round(rra, 3)
        B.nodes[n]["barrier"] = round(b_, 2)
        B.nodes[n]["reach_cost"] = round(c, 2)
        B.nodes[n]["walk_m"] = round(w, 1)
        B.nodes[n]["_alt"] = alt
        seg.append(rra); bar.append(b_); cost.append(c); walk.append(w)
    segN, barN = _norm(seg), _norm(bar)
    costN, walkN = _norm(cost), _norm(walk)
    for i, n in enumerate(reach_rooms):
        privacy = 0.5 * segN[i] + 0.5 * barN[i]
        topo = min(100.0, (100.0 - costN[i]) + 4 * (B.nodes[n].pop("_alt") - 1))
        metric = 100.0 - walkN[i]
        B.nodes[n]["privacy"] = round(privacy, 1)
        B.nodes[n]["privacy_word"] = next(w for lo, w in PRIVACY_WORDS
                                          if privacy >= lo)
        B.nodes[n]["reach"] = round(0.5 * topo + 0.5 * metric, 1)


def _assign_legibility_tiers(B, rooms):
    """Legibility = accessibility-in-reach (author's definition, Lynch register).
    A room is legible when it is easy to reach and reached DIRECTLY rather than
    through intervening rooms. Reported as integer TIERS (ties allowed — keeps
    complex plans honest and simple):
      tier 0  on the carrier / opens to everything  (most legible)
      tier 1  one direct step off a shallow hub      (direct-reach)
      tier 2+ reached only through other rooms / stairs (indirect, by depth)
    Directness = the shallowest room on its carrier-path (its 'parent') is a
    hub (depth 1). Indirect = parent is itself deep, or the last leg is a stair.
    """
    if not B.has_node(CARRIER):
        for n in rooms:
            B.nodes[n]["legibility_tier"] = None
        return
    depth = nx.single_source_shortest_path_length(B, CARRIER)
    paths = nx.single_source_shortest_path(B, CARRIER)
    for n in rooms:
        d = depth.get(n)
        if d is None:
            B.nodes[n]["legibility_tier"] = None
            continue
        if d <= 1:
            tier = 0
        else:
            path = paths[n]
            last_edge = B.edges[path[-2], path[-1]]
            parent_depth = depth.get(path[-2], 99)
            # direct-reach: one clear step off a shallow hub, not via a stair
            if parent_depth == 1 and last_edge.get("kind") != "stair":
                tier = 1
            else:
                tier = d  # indirect: deepens with each intervening space
        B.nodes[n]["legibility_tier"] = tier


# ---------------------------------------------------------------------------
# structural language (extends the Stage 3A lexicon register)
# ---------------------------------------------------------------------------
def structural_sentences(B):
    """Hillier-register sentences for the building's structure."""
    rooms = {n: B.nodes[n] for n in B.nodes if B.nodes[n].get("kind") == "room"}
    if not rooms:
        return []
    from lexicon import display_name
    hub = min(rooms, key=lambda n: rooms[n]["integration_rank"])
    seg = max(rooms, key=lambda n: rooms[n]["integration_rank"])
    thru = min(rooms, key=lambda n: rooms[n]["choice_rank"])
    out = []
    out.append(f"The most integrated space of the plan is "
               f"{display_name(rooms[hub])} — its natural hub: on average the "
               f"fewest thresholds from everywhere else (Hillier: integration).")
    if seg != hub:
        out.append(f"The most segregated is {display_name(rooms[seg])} — "
                   f"structurally the furthest-withdrawn room.")
    if rooms[thru]["choice"] > 0:
        out.append(f"{display_name(rooms[thru])} carries the most "
                   f"through-movement (choice): journeys between other rooms "
                   f"tend to pass through it.")
    stairs = [(a, b) for a, b, d in B.edges(data=True) if d.get("kind") == "stair"]
    for a, b in stairs:
        out.append(f"A stair links {display_name(B.nodes[a])} to "
                   f"{display_name(B.nodes[b])} — one threshold, carried "
                   f"vertically.")
    return out
