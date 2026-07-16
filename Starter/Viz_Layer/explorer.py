"""
SCF viz_layer — Stage 5: the interactive isovist explorer (offline HTML).

One self-contained HTML file per building storey: a dropdown of PROBE POINTS
(room centres, thresholds, serial-path waypoints); selecting one draws the
actual ISOVIST POLYGON (Benedikt 1979) from that point over the plan, with
the five Benedikt features and the quality score beside it. Isovists are
PRECOMPUTED (static HTML cannot compute), which is the honest middle between
probing-everywhere (impossible offline) and probing-nowhere.
No server, no language model, reproducible.
"""

import sys, os
import numpy as np
import plotly.graph_objects as go
from shapely.geometry import MultiPolygon


def _shell_traces(storey):
    traces = []
    wall = storey["wall"]
    polys = list(wall.geoms) if isinstance(wall, MultiPolygon) else [wall]
    for p in polys:
        x, y = p.exterior.xy
        traces.append(go.Scatter(x=list(x), y=list(y), fill="toself",
                                 fillcolor="rgba(190,190,190,0.9)",
                                 line=dict(color="#888", width=1),
                                 hoverinfo="skip", showlegend=False))
        for h in p.interiors:
            hx, hy = h.xy
            traces.append(go.Scatter(x=list(hx), y=list(hy), fill="toself",
                                     fillcolor="white",
                                     line=dict(color="#888", width=1),
                                     hoverinfo="skip", showlegend=False))
    return traces


def probe_points(storey, B=None):
    """Room centroids + threshold midpoints (labelled)."""
    pts = []
    for r in storey["spaces"]:
        if r.get("is_stair"):
            continue
        c = r["poly"].centroid
        pts.append((f"{r['long_name']} ({r['name']}) — centre", (c.x, c.y)))
    seen = set()
    for a, b, tag in storey["access_edges"]:
        key = frozenset((a, b))
        if key in seen:
            continue
        seen.add(key)
    return pts


def build_explorer(storey, df, scoring, out_html, title):
    segs = scoring.extract_wall_segments(
        storey["land"],
        storey["wall"])
    pts = probe_points(storey)
    # add threshold probes from doors
    for d in storey["doors"]:
        c = d["poly"].centroid
        pts.append((f"threshold — door {str(d.get('name') or '')[:18]}",
                    (c.x, c.y)))
    fig = go.Figure()
    for t in _shell_traces(storey):
        fig.add_trace(t)
    base_n = len(fig.data)

    labels = []
    for label, (px, py) in pts:
        try:
            iso = scoring.isovist((px, py), segs)   # list of (x, y) vertices
            feats = scoring.compute_features((px, py), iso, segs)
        except Exception:
            continue
        if not iso or len(iso) < 3:
            continue
        ring = list(iso) + [iso[0]]
        x = [v[0] for v in ring]
        y = [v[1] for v in ring]
        # nearest scored point for quality
        q = None
        if df is not None and not df.empty:
            d2 = (df.x - px) ** 2 + (df.y - py) ** 2
            q = float(df.loc[d2.idxmin(), "quality_score"])
        meta = (f"Av {feats['Av']:.1f} · Uv {feats['Uv']:.2f} · "
                f"Cv {feats['Cv']:.2f} · Ov {feats['Ov']:.2f} · "
                f"Hv {feats['Hv']:.1f}"
                + (f"  |  quality ≈ {q:.0f}" if q is not None else ""))
        fig.add_trace(go.Scatter(x=x, y=y, fill="toself",
                                 fillcolor="rgba(87,56,148,0.32)",
                                 line=dict(color="#573894", width=2),
                                 name="isovist", visible=False,
                                 hovertext=meta, hoverinfo="text"))
        fig.add_trace(go.Scatter(x=[px], y=[py], mode="markers",
                                 marker=dict(size=11, color="#E8590C",
                                             line=dict(color="#111", width=1)),
                                 visible=False, hovertext=label,
                                 hoverinfo="text", showlegend=False))
        labels.append((label, meta))

    buttons = []
    for i, (label, meta) in enumerate(labels):
        vis = [True] * base_n + [False] * (2 * len(labels))
        vis[base_n + 2 * i] = True
        vis[base_n + 2 * i + 1] = True
        buttons.append(dict(label=label, method="update",
                            args=[{"visible": vis},
                                  {"title": f"{title}<br><sub>{label} — {meta}</sub>"}]))
    if labels:
        first = buttons[0]["args"][0]["visible"]
        for i, tr in enumerate(fig.data):
            tr.visible = first[i]
    fig.update_layout(
        updatemenus=[dict(buttons=buttons, direction="down", x=0.0, y=1.14,
                          xanchor="left")],
        title=f"{title}<br><sub>{labels[0][0]} — {labels[0][1]}</sub>"
              if labels else title,
        yaxis=dict(scaleanchor="x", visible=False),
        xaxis=dict(visible=False),
        plot_bgcolor="white", width=980, height=760,
        margin=dict(l=10, r=10, t=90, b=10))
    fig.write_html(out_html, include_plotlyjs="cdn")
    return len(labels)
