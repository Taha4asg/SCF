"""
SCF ifc_layer — Stage 1: teaching the system to read a building.

IFC file  ->  per-storey (land, wall) shapely pair   [Stage 0 engine contract]
          +  semantic spaces (GUID, name, footprint) [Stage 2 aggregation]
          +  access & adjacency room graphs          [Stage 3 measures]

KEY DESIGN DECISIONS (Stage 1 report, section 'method evaluation'):

D1. Wall geometry is extracted with opening subtraction DISABLED, then door
    footprints are explicitly subtracted. Consequence: windows remain SOLID
    to vision at plan level, doors become gaps — exactly the ResPlan
    convention the Stage 0 model was trained on. Enabling openings instead
    would punch window holes through walls and let isovists leak out of the
    building at sill level.

D2. Element plan footprints are obtained by projecting the 3D mesh triangles
    to 2D and unioning them. Robust for the prismatic geometry of walls and
    spaces; independent of how the authoring tool modelled the extrusion.

D3. land := union(space footprints, wall footprint), morphologically healed.
    Therefore walkable = land - wall ~= union(spaces): the walkable domain
    is DEFINED by the model's own semantic spaces, keeping geometry and
    semantics consistent by construction.

D4. Access graph: a door connects the spaces whose (buffered) footprints it
    touches; a door touching exactly one space is an ENTRANCE and connects
    that space to the virtual node 'EXTERIOR' (Stage 3 depth-from-entrance
    needs this anchor). Adjacency graph: spaces whose footprints, buffered
    by half a typical wall, overlap. Access ⊆ Adjacency in a sane model.

D5. Storeys are processed independently (2D per storey). Vertical
    connectivity (stairs, double-height voids like FZK's Galerie) is
    surfaced as data but deliberately deferred to Stage 3.
"""

import numpy as np
import ifcopenshell
import ifcopenshell.geom
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

# tolerances (metres)
HEAL = 0.03            # morphological closing to heal space/wall seams
DOOR_BUFFER = 0.15     # widen door footprint so the cut spans the wall
TOUCH_BUFFER = 0.30    # door<->space association reach
ADJ_BUFFER = 0.25      # half a generous wall thickness, for adjacency
MIN_AREA = 1e-4        # drop degenerate projected triangles

WALL_TYPES = ("IfcWall", "IfcWallStandardCase", "IfcCurtainWall")


# ----------------------------------------------------------------------------
# low-level geometry
# ----------------------------------------------------------------------------
def _settings(disable_openings=False):
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    if disable_openings:
        s.set("disable-opening-subtractions", True)
    return s


def element_footprint(element, disable_openings=False):
    """Plan footprint of an element: union of its mesh triangles projected
    to 2D (decision D2). Returns a shapely (Multi)Polygon or None."""
    try:
        shape = ifcopenshell.geom.create_shape(_settings(disable_openings), element)
    except Exception:
        return None
    v = np.array(shape.geometry.verts).reshape(-1, 3)
    f = np.array(shape.geometry.faces).reshape(-1, 3)
    tris = []
    for a, b, c in f:
        p = Polygon([v[a][:2], v[b][:2], v[c][:2]])
        if p.area > MIN_AREA:
            tris.append(p)
    if not tris:
        return None
    return make_valid(unary_union(tris))


# ----------------------------------------------------------------------------
# model navigation
# ----------------------------------------------------------------------------
def storeys_with_spaces(model):
    """Storeys that actually decompose into IfcSpaces, sorted by elevation."""
    out = []
    for st in model.by_type("IfcBuildingStorey"):
        spaces = [s for s in model.by_type("IfcSpace")
                  if s.Decomposes and s.Decomposes[0].RelatingObject == st]
        if spaces:
            out.append((st, spaces))
    return sorted(out, key=lambda t: t[0].Elevation or 0.0)


def contained_elements(model, storey, ifc_classes):
    """Elements contained in a storey via IfcRelContainedInSpatialStructure."""
    els = []
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        if rel.RelatingStructure == storey:
            for e in rel.RelatedElements:
                if any(e.is_a(c) for c in ifc_classes):
                    els.append(e)
    return els


# ----------------------------------------------------------------------------
# per-storey extraction
# ----------------------------------------------------------------------------
def extract_storey(model, storey, spaces):
    """One storey -> geometry + semantics + graphs.

    Returns dict:
      land, wall            : shapely polygons (Stage 0 contract)
      spaces                : [{guid, name, long_name, poly}]
      doors                 : [{guid, name, poly, connects:[space_guids or 'EXTERIOR']}]
      access_edges          : [(guid_a, guid_b_or_EXTERIOR, door_guid)]
      adjacency_edges       : [(guid_a, guid_b)]
    """
    # -- spaces (semantic layer) ---------------------------------------------
    space_recs = []
    for s in spaces:
        poly = element_footprint(s)
        if poly is None or poly.is_empty:
            continue
        space_recs.append({
            "guid": s.GlobalId,
            "name": s.Name,
            "long_name": s.LongName or s.Name or "?",
            "poly": poly,
        })

    # -- walls: solid (openings disabled), then subtract doors (D1) ----------
    wall_polys = []
    for w in contained_elements(model, storey, WALL_TYPES):
        p = element_footprint(w, disable_openings=True)
        if p is not None and not p.is_empty:
            wall_polys.append(p)
    wall_solid = make_valid(unary_union(wall_polys)) if wall_polys else Polygon()

    # -- D8: windows are WALL. FZK-style walls carry native window reveals
    # (niches) that leave walkable slivers and visible notches; unioning
    # IfcWindow footprints into the solid wall closes them for both
    # gridding and vision — the plan-level convention the model knows.
    win_polys = []
    for w in contained_elements(model, storey, ("IfcWindow",)):
        p = element_footprint(w)
        if p is not None and not p.is_empty:
            win_polys.append(p.buffer(0.02))
    if win_polys:
        wall_solid = make_valid(unary_union([wall_solid] + win_polys))

    # -- D7: stair zones. Stair bodies/spaces are EXCLUDED from point
    # evaluation (a 2D isovist on a climbing volume is architecturally
    # meaningless) but stay TRANSPARENT to vision and stay graph nodes
    # (Stage 3 vertical anchors).
    stair_polys = []
    for s_el in contained_elements(model, storey, ("IfcStair", "IfcStairFlight")):
        # IfcStair is often a geometry-less AGGREGATE: its body lives on
        # child parts (flights, landings) linked by IfcRelAggregates.
        parts = [s_el]
        for rel in getattr(s_el, "IsDecomposedBy", []) or []:
            parts.extend(rel.RelatedObjects)
        for part in parts:
            p = element_footprint(part)
            if p is not None and not p.is_empty:
                stair_polys.append(p)

    door_recs = []
    door_cut = []
    for d in contained_elements(model, storey, ("IfcDoor",)):
        p = element_footprint(d)
        if p is None or p.is_empty:
            continue
        door_recs.append({"guid": d.GlobalId, "name": d.Name, "poly": p})
        door_cut.append(p.buffer(DOOR_BUFFER))
    wall = wall_solid.difference(unary_union(door_cut)) if door_cut else wall_solid
    wall = make_valid(wall)

    # -- land: spaces ∪ walls, healed (D3) ------------------------------------
    land = unary_union([r["poly"] for r in space_recs] + [wall_solid])
    land = make_valid(land).buffer(HEAL).buffer(-HEAL)

    # -- access graph via doors (D4) ------------------------------------------
    access_edges = []
    MIN_TOUCH_AREA = 0.02   # ignore grazing near-zero contacts (float hairlines)
    for d in door_recs:
        reach = d["poly"].buffer(TOUCH_BUFFER)
        touching = [r["guid"] for r in space_recs
                    if r["poly"].intersection(reach).area > MIN_TOUCH_AREA]
        if len(touching) >= 2:
            # connect the two largest-overlap spaces (robust to grazing thirds)
            touching = sorted(
                touching,
                key=lambda g: next(r["poly"] for r in space_recs if r["guid"] == g)
                .intersection(reach).area, reverse=True)[:2]
            access_edges.append((touching[0], touching[1], d["guid"]))
            d["connects"] = touching
        elif len(touching) == 1:
            access_edges.append((touching[0], "EXTERIOR", d["guid"]))
            d["connects"] = [touching[0], "EXTERIOR"]
        else:
            d["connects"] = []

    # -- D10: exterior-touch (carrier exposure, recorded not yet scored) -------
    # A room "touches the carrier" if its footprint borders the outer edge of
    # the building. Cheap to record now (we have land + walls); becomes a
    # second privacy axis later without rework. Measured as the length of the
    # room's boundary that lies on the land's outer boundary.
    # buffer past the outer wall thickness (rooms end at the INNER face, the
    # land boundary is at the OUTER face ~one wall away); measure frontage
    # against the land's outer boundary.
    land_boundary = land.boundary
    wall_reach = 0.45  # slightly more than a typical exterior wall thickness
    for r in space_recs:
        shared = r["poly"].buffer(wall_reach).intersection(land_boundary)
        r["exterior_touch"] = round(shared.length, 2) if not shared.is_empty else 0.0

    # -- adjacency graph (D4) --------------------------------------------------
    adjacency_edges = []
    for i in range(len(space_recs)):
        for j in range(i + 1, len(space_recs)):
            a, b = space_recs[i], space_recs[j]
            if a["poly"].buffer(ADJ_BUFFER).intersects(b["poly"]):
                adjacency_edges.append((a["guid"], b["guid"]))

    # -- D6: door-less OPENINGS (archways, open passages) ----------------------
    # Real buildings connect rooms through openings as often as doors (FZK's
    # Flur->Wohnen archway has no IfcDoor). For each adjacent pair, take the
    # thin strip where the two footprints meet; if a significant part of that
    # strip is NOT covered by solid wall, movement and vision pass: access.
    door_connected = {tuple(sorted((a, b))) for a, b, _ in access_edges}
    for a_guid, b_guid in adjacency_edges:
        if tuple(sorted((a_guid, b_guid))) in door_connected:
            continue
        pa = next(r["poly"] for r in space_recs if r["guid"] == a_guid)
        pb = next(r["poly"] for r in space_recs if r["guid"] == b_guid)
        strip = pa.buffer(0.12).intersection(pb.buffer(0.12))
        open_part = strip.difference(wall_solid)
        if open_part.area > 0.05:          # > 5 cm x 1 m of clear passage
            access_edges.append((a_guid, b_guid, "OPENING"))

    # D7 (revised after architect review): stair ELEMENTS are OPAQUE — a
    # stair device in mid-space works as a (mostly) sight-blocking obstacle,
    # so the zone behind it correctly reads more enclosed. Stair-named
    # SPACES (whole stairwell rooms) stay transparent rooms: excluded from
    # points, but their enclosure comes from their own walls.
    stair_obstacle = make_valid(unary_union(stair_polys)) if stair_polys else Polygon()

    # stair-space detection: NAME match OR GEOMETRIC overlap with a stair
    # element (>30% of the space) — real models mislabel stair spaces
    # (Duplex unit B: LongName 'Room'); geometry does not lie.
    STAIR_WORDS = ("stair", "treppe", "escalier")
    space_zone_polys = []
    for r in space_recs:
        label = f"{r['long_name']} {r['name']}".lower()
        by_name = any(w in label for w in STAIR_WORDS)
        by_geom = (not stair_obstacle.is_empty and
                   r["poly"].intersection(stair_obstacle).area > 0.30 * r["poly"].area)
        r["is_stair"] = by_name or by_geom
        if r["is_stair"]:
            space_zone_polys.append(r["poly"])
    stair_space_zone = make_valid(unary_union(space_zone_polys)) if space_zone_polys else Polygon()

    return {
        "storey_name": storey.Name,
        "stair_obstacle": stair_obstacle,
        "stair_space_zone": stair_space_zone,
        "elevation": storey.Elevation,
        "land": land,
        "wall": wall,
        "spaces": space_recs,
        "doors": door_recs,
        "access_edges": access_edges,
        "adjacency_edges": adjacency_edges,
    }


# ----------------------------------------------------------------------------
# building-level orchestrator
# ----------------------------------------------------------------------------
def extract_building(path):
    """IFC path -> list of per-storey extraction dicts (D5: storeys independent)."""
    model = ifcopenshell.open(path)
    return [extract_storey(model, st, sps) for st, sps in storeys_with_spaces(model)]


def stair_vision_hull(st):
    """The ONE stair outline used everywhere (vision walls AND rendering):
    the device's convex hull — a spiral reads as its cylinder. One geometry,
    one clean edge; no double outlines."""
    if st["stair_obstacle"].is_empty:
        return st["stair_obstacle"]
    return st["stair_obstacle"].convex_hull.simplify(0.05)


def scoring_inputs(st):
    """Compose the Stage 0 contract from an extracted storey (D7 revised):
    wall_for_vision = wall ∪ stair obstacles (opaque devices);
    exclusion = stair-named spaces (transparent, point-free)."""
    stair_simple = stair_vision_hull(st)
    wall_vision = make_valid(unary_union([st["wall"], stair_simple]))
    # D9: vision-geometry simplification. Authoring-tool wall joins fragment
    # the polygon (Duplex: 938 segments -> 23 min/storey); a 2 cm topological
    # simplification (far below perceptual relevance) restores tractability
    # (389 segments -> ~4.5 min) with geometry unchanged beyond tolerance.
    wall_vision = wall_vision.simplify(0.02, preserve_topology=True)
    return st["land"], wall_vision, st["stair_space_zone"]
