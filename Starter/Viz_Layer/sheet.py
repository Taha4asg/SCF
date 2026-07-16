"""
SCF viz_layer — Stage 5 v3: the Character Sheet (composer).

Board A: quality lens · privacy L1+L2 side by side (one scale, one legend) ·
reachability L1+L2 side by side (same treatment, per review) · the half-moon
character justified graph · the radial petal genotype · the sequential
triptych. Cream paper ground; the author's three gradients everywhere.
Board B: master legend + ¾-circle rosettes, names at centre.
"""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec

import views
from views import _rooms, _short


def _snapshots(B, storeys, scoring):
    """Isovist probes in EXPERIENTIAL SEQUENCE (author's ruling): the
    entrance threshold · the middle of every room crossed · stair BOTTOM
    (looking around below) · stair TOP (arriving on the upper storey) ·
    each subsequent threshold through to the destination. Stair probes are
    the same footprint point seen against the two storeys' geometry — the
    'existing view' below, the 'emerging view' above (Cullen's pair)."""
    path, events, segments, total, target = views.path_walk(B)
    R = _rooms(B)
    storey_of = {}
    for i, st in enumerate(storeys):
        for r in st["spaces"]:
            storey_of[r["guid"]] = i
    segs_cache = {}

    def _segs(i):
        if i not in segs_cache:
            st = storeys[i]
            segs_cache[i] = scoring.extract_wall_segments(st["land"],
                                                          st["wall"])
        return segs_cache[i]

    probes = []
    for x, kind, src, dst, t_xy, jump in events:
        if kind == "stair":
            lo = storey_of.get(src, 0)
            hi = storey_of.get(dst, lo)
            probes.append((x, t_xy, lo, "stair · bottom"))
            probes.append((x + total * 0.045, t_xy, hi, "stair · top"))
        else:
            lbl = ("entrance" if src == views.CARRIER
                   else f"enter {_short(B.nodes[dst].get('long_name', '?'), 9)}")
            probes.append((x, t_xy, storey_of.get(dst, 0), lbl))
    for x0, x1, n in segments:
        d = R.get(n, {})
        if d.get("is_stair") or not d.get("centroid"):
            continue
        if (x1 - x0) < total * 0.07:
            continue
        probes.append(((x0 + x1) / 2, d["centroid"], storey_of.get(n, 0),
                       f"{_short(d.get('long_name', '?'), 9)} · middle"))
    snaps = []
    for x, xy, sidx, label in sorted(probes):
        try:
            verts = scoring.isovist(xy, _segs(sidx))
        except Exception:
            continue
        if verts and len(verts) >= 3:
            snaps.append((x, verts, xy, label))
    return snaps


def _shared_row(fig, spec, B, storeys, attr):
    """Two storeys of one axis, side by side, ONE scale and one colorbar."""
    R = _rooms(B)
    vals = [d[attr] for d in R.values() if d.get(attr) is not None]
    lo, hi = (min(vals), max(vals)) if vals else (0, 100)
    axes = []
    for i in range(min(2, len(storeys))):
        ax = fig.add_subplot(spec[i])
        views.choropleth(ax, B, storeys[i], attr, vmin=lo, vmax=hi,
                         show_cbar=(i == 0))
        if i > 0:
            views._caption(ax, "same scale and legend as the storey beside —\n"
                               "one gradient, read across levels", y=-0.10)
        axes.append(ax)
    return axes


def board_spatial(B, storeys, df_by_storey, out_path, building_name,
                  scoring=None):
    fig = plt.figure(figsize=(22, 17.5))
    fig.patch.set_facecolor(views.PAPER)
    gs = GridSpec(3, 1, figure=fig, hspace=0.42,
                  height_ratios=[1.02, 1.18, 1.0])

    row0 = GridSpecFromSubplotSpec(1, 5, subplot_spec=gs[0], wspace=0.22)
    ax = fig.add_subplot(row0[0])
    views.quality_lens(ax, storeys[0], df_by_storey[0])
    _shared_row(fig, [row0[1], row0[2]], B, storeys, "privacy")
    _shared_row(fig, [row0[3], row0[4]], B, storeys, "reach")

    row1 = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[1], wspace=0.16)
    ax = fig.add_subplot(row1[0])
    views.justified_graph(ax, B)
    ax = fig.add_subplot(row1[1], projection="polar")
    views.genotype_radial(ax, B)

    sub = GridSpecFromSubplotSpec(3, 1, subplot_spec=gs[2],
                                  height_ratios=[1.15, 1.05, 0.5],
                                  hspace=0.12)
    ax_top = fig.add_subplot(sub[0])
    ax_mid = fig.add_subplot(sub[1])
    ax_bot = fig.add_subplot(sub[2], sharex=ax_mid)
    snaps = _snapshots(B, storeys, scoring) if scoring is not None else []
    views.triptych(ax_top, ax_mid, ax_bot, B, df_by_storey, snaps)

    fig.suptitle(
        f"SCF CHARACTER SHEET — {building_name} — Board A · spatial structure\n"
        f"the three gradients: OPENNESS mint→navy (mint = open) · PRIVACY "
        f"cream→wine (wine = private) · REACHABILITY sage→moss→umber (sage = "
        f"easy to reach) — one rule: light = open/public/reachable · "
        f"vermilion = register divergence · every value relative to this "
        f"building", fontsize=11.5, y=0.995)
    fig.savefig(out_path, dpi=140, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)


def board_rooms(B, out_path, building_name, cols=5):
    R = _rooms(B)
    nodes = [n for n, d in sorted(R.items(),
                                  key=lambda kv: (kv[1].get("depth") is None,
                                                  kv[1].get("depth") or 0,
                                                  kv[1].get("name") or ""))
             if d.get("prospect") is not None or d.get("privacy") is not None]
    total_cells = len(nodes) + 1
    rows = (total_cells + cols - 1) // cols
    fig = plt.figure(figsize=(3.6 * cols, 3.3 * rows))
    fig.patch.set_facecolor(views.PAPER)
    gs = GridSpec(rows, cols, figure=fig, hspace=0.30, wspace=0.30)

    ax = fig.add_subplot(gs[0, 0])
    views.rosette_legend(ax)
    for k, n in enumerate(nodes, start=1):
        r, c = divmod(k, cols)
        ax = fig.add_subplot(gs[r, c], projection="polar")
        views.room_rosette(ax, B, n)

    fig.suptitle(
        f"SCF CHARACTER SHEET — {building_name} — Board B · room identities "
        f"(¾-circle radial rosettes)\nindigo = perceptual register · wine = "
        f"configurational register · stem length = position within this "
        f"building's range · vermilion ring = divergence",
        fontsize=11.5, y=0.995)
    fig.savefig(out_path, dpi=140, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
