"""

The map is NOT a scatter of classified points: it is the probability-blended
Quality Score (each point's five class probabilities blended to 0-100)
interpolated into a continuous field and drawn as a topography — high scores
read as open 'peaks', low scores as enclosed 'valleys', contour lines as the
iso-lines of spatial character. This is the capstone's own representation
(ML Prediction notebook, final map), which absorbs point-level class flicker
by construction: the blend is continuous even where hard labels disagree.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import shapely
from shapely.geometry import MultiPolygon


def _iter_polys(geom):
    if geom is None or geom.is_empty:
        return []
    return list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]


def render_quality_map(df, land, wall, spaces=None, exclusion=None,
                       title="Spatial character — probability-blended quality",
                       out_path=None, resolution=480, levels=24, ax=None):
    """

    df: scored points (x, y, quality_score). land/wall: shapely.
    spaces: optional [{long_name, poly, is_stair?}] for labels.
    exclusion: stair zone — masked out (no field where nothing is evaluated).
    """
    walkable = land.difference(wall)
    minx, miny, maxx, maxy = land.bounds
    gx, gy = np.meshgrid(np.linspace(minx, maxx, resolution),
                         np.linspace(miny, maxy, resolution))

    pts = df.drop_duplicates(subset=["x", "y"])
    z = griddata((pts.x, pts.y), pts.quality_score, (gx, gy), method="linear")
    # clip AFTER interpolation: griddata's arithmetic can overshoot the data
    # range by ~1e-13; anything above the top contour level renders blank
    # (the 'white dots' — R8).
    z = np.clip(z, 0.0, 100.0)

    # mask: outside walkable, or inside the exclusion (stairs)
    inside = shapely.contains_xy(walkable, gx.ravel(), gy.ravel()).reshape(gx.shape)
    if exclusion is not None and not exclusion.is_empty:
        halo = exclusion.buffer(0.05)   # small halo: field never touches the device edge
        excl = shapely.contains_xy(halo, gx.ravel(), gy.ravel()).reshape(gx.shape)
        inside &= ~excl
    z = np.where(inside, z, np.nan)

    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(11, 9))
    cf = ax.contourf(gx, gy, z, levels=np.linspace(0, 100, levels),
                     cmap="RdYlBu", vmin=0, vmax=100, extend="both")
    # iso-lines at INTERIOR levels only: lines at the exact data extremes
    # draw degenerate speckle across flat plateaus
    ax.contour(gx, gy, z, levels=np.linspace(10, 90, 9),
               colors="k", linewidths=0.5, alpha=0.25)

    for p in _iter_polys(wall):
        ax.fill(*p.exterior.xy, color="#2b2b2b", zorder=4)
        for h in p.interiors:
            ax.fill(*h.xy, color="white", zorder=4)
    # draw the exclusion at EXACTLY the masked extent (same 0.05 halo):
    # fill and mask share one outline -> clean butt joint, no white ring
    draw_excl = exclusion.buffer(0.05) if (exclusion is not None and not exclusion.is_empty) else exclusion
    for p in _iter_polys(draw_excl):
        ax.fill(*p.exterior.xy, color="#4a4a4a", hatch="///",
                edgecolor="#1f1f1f", linewidth=1.6,
                joinstyle="round", zorder=5)

    if spaces:
        for r in spaces:
            c = r["poly"].centroid
            ax.annotate(r["long_name"], (c.x, c.y), ha="center", fontsize=10.5,
                        fontweight="bold", color="#111", zorder=6,
                        bbox=dict(boxstyle="round,pad=0.25", fc="white",
                                  alpha=0.75, ec="none"))

    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=13)
    if own_fig:
        cb = plt.colorbar(cf, ax=ax, shrink=0.7)
        cb.set_label("Quality Score (0–100) — enclosed ⟶ open")
        plt.tight_layout()
        if out_path:
            plt.savefig(out_path, dpi=150)
            plt.close(fig)
    return ax
