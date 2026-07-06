"""
SCF core scoring engine — Stage 0.

Exact functional port of the capstone inference pipeline
(`ML Prediction(lighter).ipynb`, cell 4 — the definitive final approach).

Chain: (land, wall) shapely polygons
        -> walkable grid (topologicpy, adaptive spacing)
        -> five isovist features per point (Av, Uv, Cv, Ov, Hv; Benedikt 1979)
        -> per-plan MinMax scaling -> global StandardScaler -> literature weights
        -> RandomForest typology + probabilities + quality score (0-100)
        -> optional confidence-based label smoothing.

Design contract:
- NO new analytical logic relative to the capstone. Any numerical deviation
  from the notebook on identical input is a bug in this module.
- Input boundary is geometry (shapely), never files: upstream layers
  (ResPlan, IFC, Revit) all reduce to (land, wall) polygons.
- Every step is independently callable; `score_plan` is a thin orchestrator.
"""

import math
import os
import pickle

import joblib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import MultiPolygon
from shapely.ops import triangulate
from shapely.validation import make_valid
from sklearn.preprocessing import MinMaxScaler

from topologicpy.Cluster import Cluster
from topologicpy.Edge import Edge
from topologicpy.Face import Face
from topologicpy.Grid import Grid
from topologicpy.Vertex import Vertex
from topologicpy.Wire import Wire

EPS = 1e-9

# ----------------------------------------------------------------------------
# Capstone constants (verbatim)
# ----------------------------------------------------------------------------
FEATURES = ["Av", "Uv", "Cv", "Ov", "Hv"]
WEIGHTS = {"Av": 1.0, "Uv": 1.0, "Cv": 0.5, "Ov": -0.6, "Hv": 1.0}
RANK_MAP = {"Narrow-Closed": 0, "Closed": 1, "Semi-Closed": 2, "Open": 3, "Wide-Open": 4}
QUALITY_MAP = {"Wide-Open": 1.0, "Open": 0.75, "Semi-Closed": 0.5, "Closed": 0.25, "Narrow-Closed": 0.0}
CONFIDENCE_THRESHOLD = 0.65  # below this, smoothing may reassign the label
GRID_DIVISIONS = 50          # spacing = min(plan dimension) / 50
SHRINK_FACTOR = 0.1          # walkable boundary shrink = spacing * 0.1


# ----------------------------------------------------------------------------
# Model artifacts
# ----------------------------------------------------------------------------
def load_models(models_dir):
    """Load the trained RF and the global StandardScaler."""
    rf = joblib.load(os.path.join(models_dir, "trained_rf_model.joblib"))
    global_scaler = joblib.load(os.path.join(models_dir, "data_scaler.joblib"))
    return rf, global_scaler


# ----------------------------------------------------------------------------
# Geometry: shapely -> topologic faces (verbatim port)
# ----------------------------------------------------------------------------
def _make_wire(coords):
    if len(coords) < 3:
        return None
    edges = [
        Edge.ByVertices([
            Vertex.ByCoordinates(float(coords[i][0]), float(coords[i][1]), 0.0),
            Vertex.ByCoordinates(float(coords[(i + 1) % len(coords)][0]),
                                 float(coords[(i + 1) % len(coords)][1]), 0.0),
        ])
        for i in range(len(coords))
    ]
    edges = [e for e in edges if e]
    return Wire.ByEdges(edges) if len(edges) >= 3 else None


def _to_faces(geom):
    """Convert a shapely (Multi)Polygon into topologic Faces, with the
    capstone's triangulation fallback for faces topologic rejects."""
    geom = make_valid(geom).simplify(0.1, preserve_topology=True)
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    faces = []
    for poly in polys:
        outer = _make_wire(list(poly.exterior.coords)[:-1])
        if outer:
            inner = [w for w in (_make_wire(list(h.coords)[:-1]) for h in poly.interiors) if w]
            face = Face.ByWires(outer, inner) if inner else Face.ByWire(outer)
            if face:
                faces.append(face)
                continue
        for tri in triangulate(poly, tolerance=0.01):
            if not poly.contains(tri.centroid):
                continue
            w = _make_wire(list(tri.exterior.coords)[:-1])
            if w:
                faces.append(Face.ByWire(w))
    return [f for f in faces if f]


def extract_wall_segments(land, wall):
    """All boundary segments seen by the ray caster: land outline + wall outlines.

    DELIBERATE DEVIATION (Stage 0, documented): the capstone read polygon
    EXTERIORS only, which is correct for ResPlan (walls are solid pieces) but
    silently blinds the ray caster to room-facing surfaces if a wall geometry
    arrives as a merged polygon with holes (e.g. unioned walls, some IFC
    exports). Interior rings are therefore included as well. On hole-free
    geometry — all of ResPlan, hence the entire capstone — the output is
    byte-identical to the notebook.
    """
    def _segments(geom):
        polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
        segs = []
        for p in polys:
            rings = [list(p.exterior.coords)[:-1]] + \
                    [list(h.coords)[:-1] for h in p.interiors]
            for c in rings:
                segs += [(c[i], c[(i + 1) % len(c)]) for i in range(len(c))]
        return segs
    return _segments(land) + _segments(wall)


# ----------------------------------------------------------------------------
# Grid generation (verbatim port; topologicpy Grid, origin at bbox centre)
# ----------------------------------------------------------------------------
def generate_grid(land, wall, spacing=None):
    """Walkable grid points for a plan.

    Returns (points, spacing, walkable) where points is a list of (x, y).
    spacing=None reproduces the capstone's adaptive rule exactly.
    """
    walkable = land.difference(wall)
    minx, miny, maxx, maxy = walkable.bounds
    if spacing is None:
        spacing = min(maxx - minx, maxy - miny) / GRID_DIVISIONS
    walkable_shrunk = walkable.buffer(-spacing * SHRINK_FACTOR)

    cx, cy = minx + (maxx - minx) / 2, miny + (maxy - miny) / 2
    origin = Vertex.ByCoordinates(cx, cy, 0.0)
    u_range = list(np.arange(-(maxx - minx) / 2, (maxx - minx) / 2 + spacing, spacing))
    v_range = list(np.arange(-(maxy - miny) / 2, (maxy - miny) / 2 + spacing, spacing))

    points = []
    for face in _to_faces(walkable_shrunk):
        grid = Grid.VerticesByDistances(face=face, origin=origin,
                                        uRange=u_range, vRange=v_range,
                                        clip=True, silent=True)
        if grid:
            points.extend((Vertex.X(v), Vertex.Y(v)) for v in Cluster.Vertices(grid))
    return points, spacing, walkable


# ----------------------------------------------------------------------------
# Isovist + features (verbatim port)
# ----------------------------------------------------------------------------
def isovist(pt, walls):
    """Isovist polygon vertices from `pt`, ray-cast to every wall-corner angle
    (with +/-1e-4 jitter) against all wall segments."""
    angles = set()
    for s, e in walls:
        for c in (s, e):
            a = math.atan2(c[1] - pt[1], c[0] - pt[0])
            for d in (-1e-4, 0, 1e-4):
                angles.add(a + d)

    def hit(a):
        dx, dy = math.cos(a), math.sin(a)
        dists = []
        for (sx, sy), (ex, ey) in walls:
            wx, wy = ex - sx, ey - sy
            det = dx * wy - dy * wx
            if abs(det) < EPS:
                continue
            fx, fy = sx - pt[0], sy - pt[1]
            t = (fx * wy - fy * wx) / det
            u = (fx * dy - fy * dx) / det
            if t > -EPS and -EPS < u < 1 + EPS:
                dists.append(max(t, 0))
        return min(dists) if dists else None

    iso = []
    for a in sorted(angles):
        t = hit(a)
        if t is not None:
            iso.append((pt[0] + t * math.cos(a), pt[1] + t * math.sin(a)))
    return [v for i, v in enumerate(iso)
            if i == 0 or math.hypot(v[0] - iso[i - 1][0], v[1] - iso[i - 1][1]) > 1e-6]


def compute_features(pt, iso, walls):
    """Five isovist features at a point: Av area, Uv open perimeter,
    Cv circularity, Ov occlusivity ratio, Hv max radial. Rounded to 3 dp
    exactly as in the capstone."""
    n = len(iso)
    dl = lambda i: math.hypot(iso[i][0] - iso[(i + 1) % n][0], iso[i][1] - iso[(i + 1) % n][1])
    Av = abs(sum(iso[i][0] * iso[(i + 1) % n][1] - iso[(i + 1) % n][0] * iso[i][1]
                 for i in range(n))) / 2
    Pv = sum(dl(i) for i in range(n))

    def on_wall(i):
        a, b = iso[i], iso[(i + 1) % n]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        for (sx, sy), (ex, ey) in walls:
            wx, wy = ex - sx, ey - sy
            sl2 = wx ** 2 + wy ** 2
            if sl2 < EPS or abs(wx * (mid[1] - sy) - wy * (mid[0] - sx)) > 0.01:
                continue
            t = ((mid[0] - sx) * wx + (mid[1] - sy) * wy) / sl2
            if -EPS <= t <= 1 + EPS:
                return True
        return False

    occ = sum(dl(i) for i in range(n) if not on_wall(i))
    Uv = Pv - occ
    Cv = (4 * math.pi * Av / Pv ** 2) if Pv > EPS else 0
    Ov = occ / Pv if Pv > EPS else 0
    Hv = max(math.hypot(v[0] - pt[0], v[1] - pt[1]) for v in iso)
    return {k: round(v, 3) for k, v in dict(Av=Av, Uv=Uv, Cv=Cv, Ov=Ov, Hv=Hv).items()}


def compute_feature_table(land, wall, spacing=None):
    """Grid the plan and compute the five features at every walkable point.
    Returns (DataFrame[x, y, Av, Uv, Cv, Ov, Hv], spacing, walkable)."""
    points, spacing, walkable = generate_grid(land, wall, spacing)
    walls = extract_wall_segments(land, wall)
    rows = []
    for pt in points:
        iso = isovist(pt, walls)
        if len(iso) < 3:
            continue
        f = compute_features(pt, iso, walls)
        f["x"], f["y"] = pt[0], pt[1]
        rows.append(f)
    return pd.DataFrame(rows).dropna(), spacing, walkable


# ----------------------------------------------------------------------------
# Scoring (verbatim port of the ML block)
# ----------------------------------------------------------------------------
def scale_and_weight(df_features, global_scaler):
    """Per-plan MinMax -> global StandardScaler -> literature weights.
    NOTE (critical order): weights multiply AFTER both scalings."""
    plan_scaler = MinMaxScaler()
    X = global_scaler.transform(plan_scaler.fit_transform(df_features[FEATURES]))
    w = np.array([WEIGHTS[f] for f in FEATURES])
    return X * w


def score_features(df, rf, global_scaler, smoothing=True, spacing=None):
    """Adds spatial_type, rank, confidence, quality_score (0-100) to a feature
    table. Optional smoothing reassigns labels with confidence <
    CONFIDENCE_THRESHOLD by confident-neighbour majority within
    r = spacing * 1.2 — labels only; quality_score is never smoothed
    (capstone behaviour)."""
    df = df.copy()
    X_final = scale_and_weight(df, global_scaler)

    df["spatial_type"] = rf.predict(X_final)
    proba = rf.predict_proba(X_final)
    df["confidence"] = np.max(proba, axis=1)
    class_quality = np.array([QUALITY_MAP[c] for c in rf.classes_])
    df["quality_score"] = (proba * class_quality).sum(axis=1) * 100
    for j, cls in enumerate(rf.classes_):
        df[f"p_{cls}"] = proba[:, j]

    if smoothing:
        if spacing is None:
            raise ValueError("smoothing requires the grid spacing")
        tree = cKDTree(df[["x", "y"]].values)
        conf = df["confidence"].values
        labels = df["spatial_type"].copy()
        uncertain = conf < CONFIDENCE_THRESHOLD
        for i in range(len(df)):
            if uncertain[i]:
                nbrs = tree.query_ball_point([df.iloc[i]["x"], df.iloc[i]["y"]],
                                             r=spacing * 1.2)
                confident = [n for n in nbrs if conf[n] >= CONFIDENCE_THRESHOLD]
                if confident:
                    labels.iloc[i] = df["spatial_type"].iloc[confident].value_counts().index[0]
        df["spatial_type"] = labels

    df["rank"] = df["spatial_type"].map(RANK_MAP)
    return df


# ----------------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------------
def score_plan(land, wall, models_dir, spacing=None, smoothing=True):
    """Full capstone chain on one plan. Returns (scored DataFrame, meta dict)."""
    rf, global_scaler = load_models(models_dir)
    df, spacing, walkable = compute_feature_table(land, wall, spacing)
    df = score_features(df, rf, global_scaler, smoothing=smoothing, spacing=spacing)
    meta = {"spacing": spacing, "n_points": len(df), "walkable": walkable}
    return df, meta
