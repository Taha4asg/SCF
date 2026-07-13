"""
SCF graph_layer — Stage 2: the Spatial Character Profile (SCP).

Fuses the perceptual point field (Stage 0 engine) with the semantic room
graph (Stage 1 reader) into the project's central construct: a per-room,
theory-grounded character profile attached to the access graph.

THE SCP, v1 (deliberately extensible — fields, not rebuilds):

Node (room) attributes
  prospect      mean Quality Score of the room's points. The best-evidenced
                perceptual axis: isovist area / max radial correlate with
                rated spaciousness and outlook (Benedikt 1979; Franz et al.
                2004; Wiener et al. 2007; Dosen & Ostwald 2016 meta-analysis).
                Plan-relative BY CONSTRUCTION (the engine's per-plan scaling).
  variety       spread of Quality Scores within the room (population std).
                The second-best-evidenced interior factor — complexity /
                visual variety; prospect-refuge cited as interpretive frame
                with its mixed interior evidence acknowledged (Dosen &
                Ostwald 2016; Appleton 1975/1984).
  mix           fraction of the room's points in each of the five capstone
                typologies (sums to 1) — the room's typological fingerprint.
  mix_entropy   Shannon entropy of `mix` in bits (0 = monotype room,
                log2(5) ≈ 2.32 = perfectly mixed): a scale-free, categorical
                companion to `variety`.
  depth         justified-graph depth from the CARRIER (Hillier & Hanson
                1984): shortest path length from the EXTERIOR node on the
                access graph. Doors and door-less openings both count one
                topological step (Hillier-faithful v1; edge widths are
                recorded so size-weighted variants stay one formula away).
                None if unreachable in 2D (vertical link deferred to Stage 3).
  area, degree  the department's room-graph schema (S05-12), extended here
                with the perceptual layer above.
  n_points      evaluation support; small-n rooms flagged (variety is noisy
                below ~30 points).
  is_stair      depth-only nodes: no point statistics by design (Stage 1 D7).

Edge (threshold) attributes
  kind          'door' | 'opening' (Stage 1 D4/D6).
  width         clear width of the threshold (m), major axis of the door /
                open-strip footprint's minimum rotated rectangle. Recorded
                now, weighted later — data before judgment.
  jump          |Δ prospect| across the threshold: the serial-vision
                transition sharpness (Appleton 1984 — successive prospect/
                refuge experiences; the theoretical licence for measuring
                character change AT thresholds rather than within rooms).
  door_guid     IFC identity for write-back (None for openings).
"""

import math

import networkx as nx
import numpy as np
import shapely
from shapely.geometry import Polygon

TYPOLOGIES = ["Narrow-Closed", "Closed", "Semi-Closed", "Open", "Wide-Open"]
MIN_POINTS_RELIABLE = 30      # variety flagged as noisy below this support
CARRIER = "EXTERIOR"          # Hillier & Hanson's carrier space


# ----------------------------------------------------------------------------
# point -> room assignment
# ----------------------------------------------------------------------------
def assign_points(df, spaces):
    """Assign each scored point to the room containing it.

    Returns (df with 'room_guid' column, coverage fraction). Points inside
    no room (door gaps, healed slivers) get None — they are real walkable
    area that belongs to thresholds, not rooms; reported, not hidden.
    """
    df = df.copy()
    df["room_guid"] = None
    assigned = np.zeros(len(df), dtype=bool)
    xs, ys = df.x.values, df.y.values
    for r in spaces:
        inside = shapely.contains_xy(r["poly"], xs, ys) & ~assigned
        df.loc[inside, "room_guid"] = r["guid"]
        assigned |= inside
    return df, assigned.mean()


# ----------------------------------------------------------------------------
# threshold width
# ----------------------------------------------------------------------------
def _clear_width(poly):
    """Clear width of a threshold footprint: the MAJOR axis of its minimum
    rotated rectangle (a door leaf's long dimension IS the passage width;
    the strip of an opening likewise). Robust to orientation."""
    if poly is None or poly.is_empty:
        return None
    mrr = poly.minimum_rotated_rectangle
    coords = list(mrr.exterior.coords)[:4]
    d1 = math.dist(coords[0], coords[1])
    d2 = math.dist(coords[1], coords[2])
    return round(max(d1, d2), 3)


def _opening_strip(pa, pb, wall_solid):
    """The clear passage between two rooms connected without a door:
    the meeting strip of their footprints minus solid wall (Stage 1 D6)."""
    strip = pa.buffer(0.12).intersection(pb.buffer(0.12))
    return strip.difference(wall_solid)


def _local_jump(df, thresh_geom, guid_a, guid_b, reach=0.9):
    """Experiential transition sharpness measured AT the threshold, not from
    room averages (Appleton 1984, serial vision). Take the scored points
    within `reach` metres of the doorway on each side (by room) and compare
    their means. Falls back to None if either side lacks local support.
    """
    if thresh_geom is None or thresh_geom.is_empty:
        return None
    near = df[shapely.distance(shapely.points(df.x.values, df.y.values),
                               thresh_geom) <= reach]
    side_a = near[near.room_guid == guid_a].quality_score
    side_b = near[near.room_guid == guid_b].quality_score
    if len(side_a) < 3 or len(side_b) < 3:
        return None
    return round(abs(side_a.mean() - side_b.mean()), 2)


def _exterior_doors(storey):
    """[(room_guid, door_guid)] for every door connecting a room to EXTERIOR."""
    return [(a if b == CARRIER else b, tag)
            for a, b, tag in storey["access_edges"]
            if CARRIER in (a, b) and tag != "OPENING"]


# ----------------------------------------------------------------------------
# the construct
# ----------------------------------------------------------------------------
def build_scp_graph(storey, df_scored, wall_solid=None, entrances=None):
    """storey: Stage 1 extraction dict. df_scored: Stage 0 output for that
    storey. entrances: optional list of room GUIDs the designer designates as
    entrances; if None, the PRIMARY (front) entrance is auto-chosen (the
    widest exterior door) and used alone — designer choice overrides, and may
    name several (back doors, multi-entry plans). Returns (graph, coverage).
    """
    spaces = storey["spaces"]
    df, coverage = assign_points(df_scored, spaces)

    G = nx.Graph()
    G.add_node(CARRIER, kind="carrier", long_name="EXTERIOR")

    touch_of = {r["guid"]: r.get("exterior_touch", 0.0) for r in spaces}

    # ---- nodes ----
    for r in spaces:
        pts = df[df.room_guid == r["guid"]]
        n = len(pts)
        cen = r["poly"].centroid
        base = dict(kind="room", long_name=r["long_name"], name=r["name"],
                    area=round(r["poly"].area, 2),
                    centroid=(round(cen.x, 3), round(cen.y, 3)),
                    exterior_touch=touch_of[r["guid"]])  # D10: carrier exposure
        if r.get("is_stair") or n == 0:
            G.add_node(r["guid"], is_stair=bool(r.get("is_stair")), n_points=n,
                       prospect=None, variety=None, mix=None,
                       mix_entropy=None, cv_mean=None, ov_mean=None,
                       complexity=None, reliable=False, **base)
            continue
        q = pts.quality_score.values
        mix = {t: round(float((pts.spatial_type == t).mean()), 4)
               for t in TYPOLOGIES}
        probs = np.array([v for v in mix.values() if v > 0])
        entropy = max(0.0, float(-(probs * np.log2(probs)).sum())) if len(probs) else 0.0
        # PERCEPTUAL complexity axis (Wiener et al. 2007; Dosen & Ostwald 2016).
        # Reuses features every scored point already carries — NO new geometry:
        #   Cv = circularity = 4*pi*Area/Perimeter^2 (low Cv = broken-up outline)
        #   Ov = occlusivity = hidden-edge fraction  (high Ov = much hidden)
        # complexity: broken-up AND occluded boundary -> high. 0..100, plan-free.
        # (Reachability is a SEPARATE, configurational axis — see structure.py
        # legibility_tier — do not conflate the two; that was the Flur lesson.)
        if {"Cv", "Ov"}.issubset(pts.columns):
            cv_mean = float(pts.Cv.mean()); ov_mean = float(pts.Ov.mean())
            complexity = round(100.0 * (1.0 - cv_mean) * (0.5 + 0.5 * ov_mean), 2)
        else:
            cv_mean = ov_mean = complexity = None
        G.add_node(r["guid"], is_stair=False, n_points=n,
                   prospect=round(float(q.mean()), 2),
                   variety=round(float(q.std()), 2),
                   mix=mix, mix_entropy=round(entropy, 3),
                   cv_mean=None if cv_mean is None else round(cv_mean, 4),
                   ov_mean=None if ov_mean is None else round(ov_mean, 4),
                   complexity=complexity,
                   reliable=n >= MIN_POINTS_RELIABLE, **base)

    # ---- edges: width + BOTH jumps (room-average and local-at-threshold) ----
    poly_of = {r["guid"]: r["poly"] for r in spaces}
    door_poly = {d["guid"]: d["poly"] for d in storey["doors"]}
    for a, b, tag in storey["access_edges"]:
        if tag == "OPENING":
            kind, guid = "opening", None
            thresh_geom = None
            width = None
            if wall_solid is not None and a in poly_of and b in poly_of:
                thresh_geom = _opening_strip(poly_of[a], poly_of[b], wall_solid)
                width = _clear_width(thresh_geom)
        else:
            kind, guid = "door", tag
            thresh_geom = door_poly.get(tag)
            width = _clear_width(thresh_geom)

        pa = G.nodes[a].get("prospect") if a in G else None
        pb = G.nodes[b].get("prospect") if b in G else None
        jump_avg = round(abs(pa - pb), 2) if (pa is not None and pb is not None) else None
        jump_local = _local_jump(df, thresh_geom, a, b) if thresh_geom is not None else None
        # Primary jump = local-at-threshold (truer to lived experience,
        # Appleton 1984); fall back to the room-average difference where a
        # threshold lacks enough nearby scored points on both sides.
        jump = jump_local if jump_local is not None else jump_avg
        txy = None
        if thresh_geom is not None and not thresh_geom.is_empty:
            tc = thresh_geom.centroid
            txy = (round(tc.x, 3), round(tc.y, 3))
        G.add_edge(a, b, kind=kind, width=width, jump=jump,
                   jump_local=jump_local, jump_avg=jump_avg,
                   jump_source=("local" if jump_local is not None else "average"),
                   thresh_xy=txy, door_guid=guid)

    # ---- entrances: designer choice, else auto-primary (widest exterior door) ----
    ext_doors = [(rm, tag) for rm, other, tag in
                 [(a, b, t) for a, b, t in storey["access_edges"]] if other == CARRIER] \
        if False else _exterior_doors(storey)
    entrance_is_guess = False
    if entrances:
        chosen = set(entrances)
    elif ext_doors:
        # Auto-default (flagged as a guess; designer choice should override).
        # Prefer a door whose NAME signals a front entrance; else fall back to
        # the single exterior door; else the widest. Width alone is unreliable
        # (a terrace door is often wider than a front door), so it is last.
        ENTRANCE_HINTS = ("haust", "front", "entrance", "entree", "main", "eingang")
        door_name = {d["guid"]: (d.get("name") or "").lower() for d in storey["doors"]}
        hinted = [rd for rd in ext_doors
                  if any(h in door_name.get(rd[1], "") for h in ENTRANCE_HINTS)]
        if hinted:
            chosen = {hinted[0][0]}
        elif len(ext_doors) == 1:
            chosen = {ext_doors[0][0]}
        else:
            # Multiple exterior doors and no name hint (e.g. a two-unit
            # duplex with one front door per unit): guessing ONE would
            # strand whole units with misleading depths. Default to ALL
            # exterior doors (pure-Hillier), flagged for confirmation.
            chosen = {rd[0] for rd in ext_doors}
        entrance_is_guess = True
    else:
        chosen = set()

    # rebuild carrier edges to reflect ONLY chosen entrances
    for rm, tag in ext_doors:
        if G.has_edge(rm, CARRIER):
            G.remove_edge(rm, CARRIER)
    for rm, tag in ext_doors:
        if rm in chosen:
            dp = door_poly.get(tag)
            txy = None
            if dp is not None and not dp.is_empty:
                tc = dp.centroid
                txy = (round(tc.x, 3), round(tc.y, 3))
            G.add_edge(rm, CARRIER, kind="door", width=_clear_width(dp),
                       jump=None, jump_local=None, jump_avg=None,
                       jump_source=None, thresh_xy=txy,
                       door_guid=tag, is_entrance=True)
    G.graph["entrances"] = sorted(chosen)
    G.graph["exterior_doors"] = [rm for rm, _ in ext_doors]
    G.graph["entrance_is_guess"] = entrance_is_guess  # True => designer should confirm

    # ---- carrier depth from chosen entrance(s) ----
    if G.has_node(CARRIER) and chosen:
        lengths = nx.single_source_shortest_path_length(G, CARRIER)
        for node in G.nodes:
            if G.nodes[node].get("kind") == "room":
                G.nodes[node]["depth"] = lengths.get(node)
    else:
        for node in G.nodes:
            if G.nodes[node].get("kind") == "room":
                G.nodes[node]["depth"] = None
    return G, coverage


# ----------------------------------------------------------------------------
# convenience: tabular view (for reports, tests, and the Pset write-back)
# ----------------------------------------------------------------------------
def scp_table(G):
    import pandas as pd
    rows = []
    for n, d in G.nodes(data=True):
        if d.get("kind") != "room":
            continue
        rows.append({
            "room": d["long_name"], "guid": n[:8] + "…",
            "area": d["area"], "n_points": d["n_points"],
            "prospect": d["prospect"], "variety": d["variety"],
            "mix_entropy": d["mix_entropy"], "depth": d.get("depth"),
            "degree": G.degree(n),
            "is_stair": d["is_stair"], "reliable": d["reliable"],
        })
    return pd.DataFrame(rows).sort_values("depth", na_position="last")
