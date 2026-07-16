"""
SCF viz_layer — Stage 5 v3: the Visual Instrument (views).

v3 — the design-language pass (architect's gradient system, applied as law):

THE THREE GRADIENTS (author-specified, applied everywhere):
  OPENNESS      #002D72 navy (enclosed) → #573894 → #81459E → #A0E5D9 mint (open)
  PRIVACY       #FFF3E6 cream (public)  → #722F37 wine (private)
  REACHABILITY  #3B3432 umber (hardest) → #44573F moss → #EDF1E6 sage (easiest)
                (author gave moss→umber; both ends were dark, so a light sage
                 head was added to give the ramp luminance travel — both author
                 colours kept in-ramp, and the shared rule below is preserved)
  ONE SHARED RULE unifying all three: LIGHT = open / public / reachable;
  DARK = enclosed / private / withdrawn. Cream paper ground (#FBF8F2).
  ACCENT: vermilion #E8590C = register divergence (outside all three ramps).

v3 structural changes (author review):
  • j-graph: HALF-MOON nodes — left half = openness, right half = privacy
    (the two core qualities on one simple shape; ring/fill dual coding
    retired). Carrier drawn as text, no box. Legend moved clear of the
    drawing and made comprehensive (incl. how to read the Δ jump numbers).
  • genotype: petal restyle after the author's reference — tapered petals
    (width = floor area), rim name-bubbles on thin spokes, dotted radial
    guides, cream ground. Encodings unchanged (radius = integration,
    centre = most integrated; colour = privacy; sectors = privacy zones).
  • triptych: probes now follow the EXPERIENTIAL SEQUENCE — entrance,
    middle of each room, stair bottom (looking around below), stair top
    (arriving above), through to the destination's threshold. The middle
    curve is explained: it is the SAME 0–100 score as the quality lens,
    sampled along the walk — the plans show the whole field; this shows
    the sequence you actually walk. Room band uses the openness gradient.
  • rosettes: ¾-circle radials (gap holds the reading guides), room NAME
    (≤10 chars) at centre, register-coloured stems, vermilion divergence
    ring; master legend states BOTH poles of every axis.
"""

import math

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Wedge, Circle
from shapely.geometry import MultiPolygon

CARRIER = "EXTERIOR"

OPEN_CMAP = LinearSegmentedColormap.from_list(
    "scf_open", ["#002D72", "#573894", "#81459E", "#A0E5D9"])
PRIV_CMAP = LinearSegmentedColormap.from_list(
    "scf_privacy", ["#FFF3E6", "#722F37"])
REACH_CMAP = LinearSegmentedColormap.from_list(
    "scf_reach", ["#3B3432", "#44573F", "#EDF1E6"])

ACCENT = "#E8590C"          # divergence — outside all three ramps
JUMP_C = "#8A5A00"          # threshold-jump labels (amber, neutral to ramps)
PERCEPT_C = "#573894"       # register colour (from the openness family)
CONFIG_C = "#722F37"        # register colour (wine)
PAPER = "#FBF8F2"
EDGE_STYLE = {"door": "-", "opening": "--", "stair": ":"}


def _polys(geom):
    return list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]


def _short(s, n=10):
    s = str(s)
    return s if len(s) <= n else s[:n - 1].rstrip() + "."


def _draw_shell(ax, storey, wall_color="#DDD5C9"):
    for p in _polys(storey["wall"]):
        ax.fill(*p.exterior.xy, color=wall_color, zorder=1)
        for h in p.interiors:
            ax.fill(*h.xy, color="white", zorder=1)
    ax.set_aspect("equal")
    ax.axis("off")


def _rooms(B):
    return {n: B.nodes[n] for n in B.nodes if B.nodes[n].get("kind") == "room"}


def _caption(ax, text, y=-0.02, fontsize=6.6):
    ax.text(0.5, y, text, transform=ax.transAxes, ha="center", va="top",
            fontsize=fontsize, color="#4a4a4a", wrap=True)


def _cbar(ax, cmap, vmin, vmax, label, left_word, right_word):
    sm = cm.ScalarMappable(norm=plt.Normalize(vmin, vmax), cmap=cmap)
    cb = plt.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.045,
                      pad=0.03, aspect=28)
    cb.set_label(label, fontsize=6.8)
    cb.ax.tick_params(labelsize=6)
    cb.outline.set_linewidth(0.5)
    cb.ax.text(0.0, -3.9, left_word, transform=cb.ax.transAxes, ha="left",
               fontsize=6.4, color="#333")
    cb.ax.text(1.0, -3.9, right_word, transform=cb.ax.transAxes, ha="right",
               fontsize=6.4, color="#333")
    return cb


def _divergence_handle():
    return Line2D([], [], marker="o", color="none", markerfacecolor=ACCENT,
                  markeredgecolor="#5a2410", markersize=7,
                  label="divergence: the two registers disagree here")


# ---------------------------------------------------------------------------
# 0. QUALITY LENS — the capstone field, on the openness gradient
# ---------------------------------------------------------------------------
def quality_lens(ax, storey, df, res=300):
    from scipy.interpolate import griddata
    _draw_shell(ax, storey, wall_color="#D8D0C4")
    if df is None or df.empty:
        ax.set_title("(storey not scored)", fontsize=9)
        return
    xi = np.linspace(df.x.min(), df.x.max(), res)
    yi = np.linspace(df.y.min(), df.y.max(), res)
    XI, YI = np.meshgrid(xi, yi)
    ZI = griddata((df.x, df.y), df.quality_score, (XI, YI), method="linear")
    ZI = np.clip(ZI, 0, 100)
    ax.contourf(XI, YI, ZI, levels=24, cmap=OPEN_CMAP, vmin=0, vmax=100,
                zorder=2)
    for p in _polys(storey["wall"]):
        ax.fill(*p.exterior.xy, color="#D8D0C4", zorder=3)
        for h in p.interiors:
            ax.fill(*h.xy, color="white", zorder=3)
    ax.set_title(f"Experiential quality lens — {storey['storey_name']}",
                 fontsize=9)
    _cbar(ax, OPEN_CMAP, 0, 100, "quality score (per walkable point)",
          "enclosed / narrow", "open / expansive")
    _caption(ax, "each walkable point scored by the trained model\n"
                 "(five isovist features → class probabilities → 0–100)",
             y=-0.34)


# ---------------------------------------------------------------------------
# 1. CHOROPLETH GRADIENT PLAN
# ---------------------------------------------------------------------------
CHORO_META = {
    "prospect": (OPEN_CMAP, "Prospect (openness)", False,
                 "enclosed", "open",
                 "mean point-quality of the room —\nhow open it feels inside"),
    "complexity": (OPEN_CMAP, "Complexity (boundary)", True,
                   "intricate", "plain",
                   "how broken-up and hidden-behind-thresholds\nthe view is"),
    "privacy": (PRIV_CMAP, "Privacy gradient", False,
                "public", "private",
                "½ segregation (RRA: how deep the plan holds the room)\n"
                "+ ½ closability (door 1.0 · stair 0.8 · archway 0.35)"),
    "reach": (REACH_CMAP, "Reachability", False,
              "hard to reach", "easy to reach",
              "½ threshold effort (door 1 · archway .55 · stair 1.6)\n"
              "+ ½ walking distance from the chosen entrance"),
    "integration": (PRIV_CMAP, "Integration (publicness)", True,
                    "integrated", "segregated",
                    "closeness on the access graph — the social-hub measure"),
}


def choropleth(ax, B, storey, attr, vmin=None, vmax=None, show_cbar=True):
    cmap, label, invert, lo_w, hi_w, explain = CHORO_META[attr]
    R = _rooms(B)
    vals = [d[attr] for d in R.values() if d.get(attr) is not None]
    lo = vmin if vmin is not None else (min(vals) if vals else 0)
    hi = vmax if vmax is not None else (max(vals) if vals else 1)
    _draw_shell(ax, storey)
    any_div = False
    for r in storey["spaces"]:
        d = R.get(r["guid"])
        if d is None:
            continue
        v = d.get(attr)
        if v is None:
            ax.fill(*r["poly"].exterior.xy, color="#CFCADF", zorder=2)
            continue
        t = (v - lo) / (hi - lo) if hi > lo else 0.5
        if invert:
            t = 1 - t
        face = cmap(t)
        unreliable = (cmap is OPEN_CMAP and not d.get("reliable", True))
        ax.fill(*r["poly"].exterior.xy, color=face, zorder=2,
                hatch="///" if unreliable else None,
                edgecolor="#4a4a4a", linewidth=0.7,
                alpha=0.55 if unreliable else 0.97)
        c = r["poly"].centroid
        dark_bg = (t > 0.55) if cmap in (PRIV_CMAP,) else (t < 0.45)
        ax.annotate(f"{d['long_name']}\n{v:.0f}", (c.x, c.y), ha="center",
                    va="center", fontsize=7.3, fontweight="bold", zorder=4,
                    color="white" if dark_bg else "#1c1c1c")
        if d.get("char_divergence"):
            any_div = True
            ax.scatter([c.x], [c.y + 0.85], s=34, c=ACCENT,
                       edgecolors="#5a2410", linewidths=0.6, zorder=5)
    ax.set_title(f"{label} — {storey['storey_name']}", fontsize=9)
    if show_cbar:
        _cbar(ax, cmap, lo, hi, f"{label.lower()} (relative to this building)",
              lo_w, hi_w)
        _caption(ax, explain, y=-0.34)
    if any_div:
        ax.legend(handles=[_divergence_handle()], loc="upper left",
                  fontsize=5.8, frameon=True, framealpha=0.9, borderpad=0.3)


# ---------------------------------------------------------------------------
# 2. CHARACTER JUSTIFIED GRAPH — half-moon nodes (openness | privacy)
# ---------------------------------------------------------------------------
NODE_R = 0.30


def justified_graph(ax, B):
    """Hillier & Hanson's depth diagram carrying the two core qualities on
    ONE simple shape: each room is a half-moon — LEFT half = openness,
    RIGHT half = privacy (the author's two system gradients). Carrier is
    text, not a box. Δ numbers on edges = the felt jump."""
    R = _rooms(B)
    rows = {}
    for n, d in R.items():
        dep = d.get("depth")
        if dep is not None:
            rows.setdefault(dep, []).append(n)
    pvals = [d.get("privacy") for d in R.values()
             if d.get("privacy") is not None]
    plo, phi = (min(pvals), max(pvals)) if pvals else (0, 1)
    pos = {CARRIER: (0.0, 0.0)}
    for dep in sorted(rows):
        row = sorted(rows[dep], key=lambda n: R[n].get("name") or "")
        for i, n in enumerate(row):
            pos[n] = ((i - (len(row) - 1) / 2) * 1.9, dep * 1.35)
    for a, b, e in B.edges(data=True):
        if a in pos and b in pos:
            xa, ya = pos[a]; xb, yb = pos[b]
            ax.plot([xa, xb], [ya, yb], EDGE_STYLE.get(e.get("kind"), "-"),
                    color="#6a6a6a", lw=1.2, zorder=1)
            if e.get("jump") is not None:
                ax.annotate(f"Δ{e['jump']:.0f}",
                            ((xa + xb) / 2, (ya + yb) / 2), fontsize=5.8,
                            color=JUMP_C, ha="center", zorder=4,
                            bbox=dict(boxstyle="round,pad=0.08", fc="white",
                                      alpha=0.85, ec="none"))
    # carrier: text as the node (no box), with a short ground line
    ax.plot([-0.55, 0.55], [0, 0], color="#3a3a3a", lw=1.4, zorder=2)
    ax.annotate("CARRIER · outside", (0, -0.30), ha="center", fontsize=7.2,
                color="#3a3a3a", zorder=3)
    for n, (x, y) in pos.items():
        if n == CARRIER:
            continue
        d = R[n]
        pr = d.get("prospect")
        left = OPEN_CMAP(pr / 100) if pr is not None else "#CFCFCF"
        pv = d.get("privacy")
        t = (pv - plo) / (phi - plo) if (pv is not None and phi > plo) else 0.5
        right = PRIV_CMAP(t)
        ax.add_patch(Wedge((x, y), NODE_R, 90, 270, fc=left, ec="none",
                           zorder=3))
        ax.add_patch(Wedge((x, y), NODE_R, -90, 90, fc=right, ec="none",
                           zorder=3))
        ax.add_patch(Circle((x, y), NODE_R, fc="none", ec="#3a3a3a", lw=0.9,
                            zorder=4))
        if d.get("char_divergence"):
            ax.scatter([x + NODE_R], [y + NODE_R], s=30, c=ACCENT,
                       edgecolors="#5a2410", linewidths=0.5, zorder=5)
        nm = _short(d["long_name"], 8)
        ax.annotate(str(nm), (x, y - NODE_R - 0.16), ha="center", va="top",
                    fontsize=6.2, color="#222", zorder=4)
    xs = [x for x, _ in pos.values()]; ys = [y for _, y in pos.values()]
    ax.set_xlim(min(xs) - 1.7, max(xs) + 1.7)
    ax.set_ylim(min(ys) - 1.0, max(ys) + 0.85)
    for dep in sorted(rows):
        ax.annotate(f"depth {dep}", (min(xs) - 1.55, dep * 1.35), fontsize=7,
                    color="#8a8a8a", va="center")
    ax.set_title("Character justified graph — Hillier's depth diagram, "
                 "carrying the two core qualities", fontsize=9)
    ax.set_aspect("equal"); ax.axis("off")
    handles = [
        Line2D([], [], color="#6a6a6a", ls="-", label="door"),
        Line2D([], [], color="#6a6a6a", ls="--", label="open passage"),
        Line2D([], [], color="#6a6a6a", ls=":", label="stair"),
        Line2D([], [], color=JUMP_C, marker="$Δ$", ls="none",
               label=("Δ n — felt jump: the change in the 0–100 quality "
                      "score as you cross that threshold")),
        Line2D([], [], color="none",
               label="   (Δ0 seamless · Δ~20 eased · Δ~45+ a dramatic reveal "
                     "or compression)"),
        _divergence_handle(),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.34, -0.06),
              ncol=2, fontsize=6.0, frameon=False)
    # the two halves, keyed by their ACTUAL gradients (same style as the plans)
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    for k, (cmap, head, lo_w, hi_w) in enumerate(
            [(OPEN_CMAP, "LEFT half — openness", "enclosed", "open"),
             (PRIV_CMAP, "RIGHT half — privacy", "public", "private")]):
        ia = ax.inset_axes([0.02, -0.115 - 0.075 * k, 0.26, 0.030],
                           transform=ax.transAxes)
        ia.imshow(grad, aspect="auto", cmap=cmap)
        ia.set_xticks([]); ia.set_yticks([])
        for sp in ia.spines.values():
            sp.set_linewidth(0.4); sp.set_color("#8a8a8a")
        ia.set_title(head, fontsize=6.0, color="#3a3a3a", pad=1.5, loc="left")
        ia.text(-0.02, -0.55, lo_w, transform=ia.transAxes, ha="right",
                va="top", fontsize=5.6, color="#4a4a4a")
        ia.text(1.02, -0.55, hi_w, transform=ia.transAxes, ha="left",
                va="top", fontsize=5.6, color="#4a4a4a")


# ---------------------------------------------------------------------------
# 3. GENOTYPE — radial PETAL plot (reference-styled)
# ---------------------------------------------------------------------------
ZONE_ORDER = ["public", "semi-public", "semi-private", "private",
              "innermost/intimate"]
ZONE_SHORT = {"public": "PUBLIC", "semi-public": "SEMI-PUBLIC",
              "semi-private": "SEMI-PRIVATE", "private": "PRIVATE",
              "innermost/intimate": "INNERMOST"}


def _petal(ax, th, r0, r1, w_max, color, outline=None, z=2):
    """Tapered petal, GEOMETRICALLY VALID AT ANY ANGULAR WIDTH.
    Fundamental guards (added after a wide-room distortion on FZK's Galerie):
      · the tip is closed by a SAMPLED ARC at r1, never a straight chord —
        a chord across a wide angle cuts back through the chart's centre
        and self-intersects the fill into a twisted ribbon;
      · the petal glyph's half-width is CAPPED (the room's true area share
        stays visible as its allocated angular chunk / sector shading);
      · a MINIMUM radial length guarantees the most-integrated rooms render
        as a visible nub instead of a hairline at the void edge."""
    r1 = max(r1, r0 + 0.055)                       # visible nub
    w_max = min(w_max, np.deg2rad(11.0))           # glyph sanity cap
    s = np.linspace(0.02, 1.0, 30)
    r = r0 + (r1 - r0) * s
    w = w_max * np.sqrt(s)
    n_tip = 18
    tip_th = np.linspace(th - w_max, th + w_max, n_tip)
    thetas = np.concatenate([th - w, tip_th, (th + w)[::-1]])
    rs = np.concatenate([r, np.full(n_tip, r1), r[::-1]])
    ax.fill(thetas, rs, color=color, alpha=0.85, lw=0, zorder=z)
    if outline:
        ax.plot(np.append(thetas, thetas[0]), np.append(rs, rs[0]),
                color=outline, lw=1.4, zorder=z + 2)


def genotype_radial(ax, B, r_void=0.30, gap_deg=13.0, min_span=6.0):
    """The inequality genotype (Hillier 1996) as a radial petal plot:
    radius = integration with topological honesty (the most integrated rooms
    sit nearest the CENTRE — closeness drawn as closeness); each room's
    ANGULAR CHUNK is sized by its floor area (Wohnen wider than Bad because
    it IS bigger — no extra marker needed); petal colour = privacy (the wine
    gradient); sectors = privacy zones with gaps; names sit at the rim behind
    a minimal dash. Vermilion outline = divergence. Requires polar axes."""
    R = _rooms(B)
    rooms = [n for n in R if R[n].get("integration") is not None]
    ivals = [R[n]["integration"] for n in rooms]
    ilo, ihi = min(ivals), max(ivals)
    zones = {}
    for n in rooms:
        zones.setdefault(R[n].get("privacy_word") or "semi-private",
                         []).append(n)
    present = [z for z in ZONE_ORDER if z in zones]
    # angular allocation: proportional to floor area, with a minimum span
    avail = 360.0 - gap_deg * len(present)
    total_area = sum(R[n].get("area") or 5 for n in rooms)
    span = {n: max(min_span, avail * (R[n].get("area") or 5) / total_area)
            for n in rooms}
    scale = avail / sum(span.values())
    span = {n: v * scale for n, v in span.items()}
    # dotted radial guides
    gtheta = np.linspace(0, 2 * np.pi, 140)
    for gr in (r_void, 0.55, 0.80, 1.00):
        ax.plot(gtheta, [gr] * 140, color="#C9C2B4", ls=":", lw=0.6, zorder=0)
    ax.annotate("centre = most integrated\n(the plan's social heart)",
                (np.deg2rad(90), 0.02), ha="center", va="center",
                fontsize=5.6, color="#8a8a8a")
    theta0 = 90.0
    for z in present:
        members = sorted(zones[z], key=lambda n: -R[n]["integration"])
        z_span = sum(span[n] for n in members)
        mid_priv = np.mean([R[n].get("privacy") or 50 for n in members])
        ax.bar(np.deg2rad(theta0 - z_span / 2), 1.06 - r_void,
               width=np.deg2rad(z_span), bottom=r_void,
               color=PRIV_CMAP(mid_priv / 100), alpha=0.10,
               edgecolor="none", zorder=0)
        cursor = theta0
        for j, n in enumerate(members):
            sp = span[n]
            th = np.deg2rad(cursor - sp / 2)
            t = (R[n]["integration"] - ilo) / (ihi - ilo) if ihi > ilo else 0.5
            r = r_void + (1 - t) * (1.0 - r_void)
            col = PRIV_CMAP(0.18 + 0.82 * (R[n].get("privacy") or 50) / 100)
            w_max = np.deg2rad(sp) * 0.42
            _petal(ax, th, r_void, r, w_max, col,
                   outline=(ACCENT if R[n].get("char_divergence") else None))
            # minimal dash emerging to the name at the rim; alternate radii
            # so dense sectors (mirror units, many small rooms) stay legible
            r_name = 1.17 if j % 2 == 0 else 1.29
            ax.plot([th, th], [1.04, r_name - 0.07], color="#9a9384",
                    lw=0.8, zorder=1)
            ax.annotate(_short(R[n]["long_name"], 9), (th, r_name),
                        fontsize=6.0, ha="center", va="center",
                        color="#3a3a3a")
            cursor -= sp
        ax.annotate(ZONE_SHORT[z],
                    (np.deg2rad(theta0 - z_span / 2), 1.44), fontsize=6.4,
                    ha="center", color="#6a6a6a", fontweight="bold")
        theta0 -= z_span + gap_deg
    ax.plot(gtheta, [r_void] * 140, color="#A9A294", lw=0.8, zorder=1)
    ax.set_ylim(0, 1.50)
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor("none")
    ax.set_title("The inequality genotype — radial petal plot\n"
                 "(Hillier 1996: the ranking IS the plan's signature)",
                 fontsize=9, pad=16)
    handles = [
        Patch(facecolor=PRIV_CMAP(0.75),
              label="petal colour: privacy (cream = public · wine = private)"),
        Patch(facecolor=PRIV_CMAP(0.35),
              label="chunk width: floor area (bigger room = wider petal)"),
        Line2D([], [], color="#8a8a8a", lw=1,
               label="radius: integration — shorter petal = more integrated"),
        Line2D([], [], color=ACCENT, lw=1.4,
               label="vermilion outline: the two registers disagree here"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.05),
              fontsize=5.8, frameon=False, ncol=2)


# ---------------------------------------------------------------------------
# 4. SERIAL VISION — the Triptych Journey Map (sequential probes)
# ---------------------------------------------------------------------------
def path_walk(B, target=None):
    """Shared spine: events [(x, kind, src, dst, thresh_xy, jump)] and room
    segments [(x0, x1, node)] along entrance -> deepest room."""
    R = _rooms(B)
    if target is None:
        target = max((n for n in R if R[n].get("depth") is not None),
                     key=lambda n: R[n]["depth"])
    path = nx.shortest_path(B, CARRIER, target)
    events, segments = [], []
    walked, prev_pt, seg_start, cur_room = 0.0, None, 0.0, None
    for i in range(len(path) - 1):
        e = B.edges[path[i], path[i + 1]]
        t_xy = e.get("thresh_xy")
        nxt = path[i + 1]
        if t_xy:
            if prev_pt:
                walked += math.dist(prev_pt, t_xy)
            if cur_room is not None:
                segments.append((seg_start, walked, cur_room))
            events.append((walked, e.get("kind"), path[i], nxt, t_xy,
                           e.get("jump")))
            seg_start = walked
            prev_pt = t_xy
        cen = R.get(nxt, {}).get("centroid")
        if cen:
            walked += math.dist(prev_pt, cen) if prev_pt else 0
            prev_pt = cen
        cur_room = nxt
    if cur_room is not None:
        segments.append((seg_start, walked, cur_room))
    return path, events, segments, walked, target


def triptych(ax_top, ax_mid, ax_bot, B, df_by_storey, snapshots,
             target=None):
    """Three layers, one walked-distance axis (Cullen 1961; Ganis 1998):
      TOP    the emerging view — isovist snapshots in EXPERIENTIAL SEQUENCE
             (entrance · middle of each space · stair bottom · stair top ·
             the destination's threshold)
      MIDDLE the measured curve — the SAME 0–100 score as the quality lens,
             sampled along the walk (the plans show the whole field; this
             shows the sequence a person actually walks)
      BOTTOM the rooms crossed, coloured on the openness gradient, with the
             thresholds aligned beneath their data points.
    `snapshots`: [(x, verts, probe_xy, label)] precomputed by sheet.py."""
    R = _rooms(B)
    path, events, segments, total, target = path_walk(B, target)

    # ---- MIDDLE ----
    xs, ys = [], []
    for x, kind, src, dst, t_xy, jump in events:
        q = _local_quality(df_by_storey, t_xy)
        if q is not None:
            xs.append(x); ys.append(q)
        p = R.get(dst, {}).get("prospect")
        if p is not None:
            seg = next(s for s in segments if s[2] == dst)
            xs.append((seg[0] + seg[1]) / 2); ys.append(p)
    order = np.argsort(xs)
    xs = list(np.array(xs)[order]); ys = list(np.array(ys)[order])
    ax_mid.plot(xs, ys, "-", color=PERCEPT_C, lw=2, zorder=2)
    ax_mid.fill_between(xs, ys, 0, color=PERCEPT_C, alpha=0.08)
    ax_mid.scatter(xs, ys, s=30, c=[OPEN_CMAP(v / 100) for v in ys],
                   edgecolors="#3a3a3a", linewidths=0.6, zorder=3)
    for x, kind, src, dst, t_xy, jump in events:
        for a in (ax_mid, ax_bot):
            a.axvline(x, color="#9a9a9a", lw=0.9,
                      ls=EDGE_STYLE.get(kind, "-"))
        if jump is not None:
            ax_mid.annotate(f"Δ{jump:.0f}", (x, 5), ha="center", fontsize=6.2,
                            color=JUMP_C)
    ax_mid.set_ylim(0, 108)
    ax_mid.set_ylabel("experiential quality\n(0–100, the lens score)",
                      fontsize=7.2)
    ax_mid.tick_params(labelsize=7)
    ax_mid.spines[["top", "right"]].set_visible(False)
    ax_mid.set_xlim(-0.4, total + 0.4)

    # ---- BOTTOM ----
    for x0, x1, n in segments:
        d = R.get(n, {})
        p = d.get("prospect")
        col = OPEN_CMAP(p / 100) if p is not None else "#CFCADF"
        ax_bot.fill_between([x0, x1], 0, 1, color=col, alpha=0.95)
        nm = d.get("long_name", "?")
        ax_bot.annotate(nm, ((x0 + x1) / 2, 0.5), ha="center", va="center",
                        fontsize=7, fontweight="bold",
                        color="white" if (p is not None and p < 45) else "#111",
                        rotation=0 if (x1 - x0) > total * 0.12 else 90)
    for x, kind, *_ in events:
        glyph = {"door": "▮", "opening": "◫", "stair": "☰"}.get(kind, "|")
        ax_bot.annotate(glyph, (x, 1.12), ha="center", fontsize=8,
                        color="#3a3a3a")
    ax_bot.set_ylim(0, 1.35)
    ax_bot.set_yticks([])
    ax_bot.set_xlabel("walked distance from the entrance (m)", fontsize=8)
    ax_bot.tick_params(labelsize=7)
    ax_bot.spines[["top", "right", "left"]].set_visible(False)
    ax_bot.set_xlim(-0.4, total + 0.4)

    # ---- TOP: staggered isovist snapshots in sequence ----
    ax_top.set_xlim(-0.4, total + 0.4)
    ax_top.set_ylim(0, 1)
    ax_top.axis("off")
    n_sn = max(1, len(snapshots))
    tw = min(total * 0.13, total / math.ceil(n_sn / 2) * 0.80)
    for k, (x, verts, probe, label) in enumerate(sorted(snapshots)):
        hi = (k % 2 == 0)
        y0 = 0.52 if hi else 0.02
        x0 = min(max(x - tw / 2, 0), total - tw)
        ia = ax_top.inset_axes([x0, y0, tw, 0.42],
                               transform=ax_top.transData)
        vx = [v[0] for v in verts] + [verts[0][0]]
        vy = [v[1] for v in verts] + [verts[0][1]]
        ia.fill(vx, vy, color=PERCEPT_C, alpha=0.34, zorder=2)
        ia.plot(vx, vy, color=PERCEPT_C, lw=0.9, zorder=3)
        ia.scatter([probe[0]], [probe[1]], s=13, c=ACCENT, zorder=4)
        ia.set_aspect("equal"); ia.axis("off")
        ia.set_title(label, fontsize=5.4, color="#4a4a4a", pad=1.5)
        ax_top.plot([x, x], [y0 if not hi else y0, 0.0], ":",
                    color="#B0A99B", lw=0.7)
    ax_top.set_title(
        f"Serial vision — the journey from the entrance to "
        f"{R[target]['long_name']}   (the emerging view · the measured "
        f"curve · the rooms crossed — one shared axis)", fontsize=9)

    handles = [
        Line2D([], [], color=PERCEPT_C, lw=2,
               label="the walk's cross-section through the quality field "
                     "(same score as the lens — plans show the field, this "
                     "shows the sequence)"),
        Line2D([], [], color="#9a9a9a", ls="-", label="door"),
        Line2D([], [], color="#9a9a9a", ls="--", label="open passage"),
        Line2D([], [], color="#9a9a9a", ls=":", label="stair"),
        Patch(facecolor=OPEN_CMAP(0.85),
              label="band: room on the openness gradient (mint = open)"),
        Patch(facecolor=PERCEPT_C, alpha=0.34,
              label="snapshot: the isovist — what you SEE from that point of "
                    "the sequence"),
        Line2D([], [], color=JUMP_C, marker="$Δ$", ls="none",
               label="Δ: felt jump crossing the threshold"),
    ]
    ax_bot.legend(handles=handles, loc="upper center",
                  bbox_to_anchor=(0.5, -0.78), ncol=3, fontsize=6.0,
                  frameon=False)


def _local_quality(df_by_storey, xy, reach=0.9):
    for df in df_by_storey:
        if df is None or df.empty:
            continue
        m = ((df.x - xy[0]) ** 2 + (df.y - xy[1]) ** 2) <= reach ** 2
        if m.any():
            return float(df.loc[m, "quality_score"].mean())
    return None


# ---------------------------------------------------------------------------
# 5. ROOM ROSETTE — ¾-circle radial identity, name at centre
# ---------------------------------------------------------------------------
ROSETTE_AXES = [
    ("prospect",    "open",        "perceptual"),
    ("variety",     "contrasting", "perceptual"),
    ("complexity",  "intricate",   "perceptual"),
    ("integration", "integrated",  "configurational"),
    ("privacy",     "private",     "configurational"),
    ("reach",       "reachable",   "configurational"),
]
R_VOID = 0.34
SPOKE_START = 66.0      # degrees; six spokes sweep 270° clockwise from here
SPOKE_STEP = 54.0       # 270 / 5 — the upper-left quadrant stays open


def room_rosette(ax, B, node):
    """One room's identity: six stems over a ¾ circle (the open quadrant
    holds the reading guides), the room's NAME at the centre; perceptual
    stems in the openness-family indigo, configurational in wine; stem
    length = the room's position within THIS building's range; vermilion
    ring = the registers disagree."""
    d = B.nodes[node]
    R = _rooms(B)
    gtheta = np.linspace(0, 2 * np.pi, 90)
    for gr in (0.6, 1.0):
        ax.plot(gtheta, [gr] * 90, color="#D8D1C3", ls=":", lw=0.5, zorder=0)
    for i, (attr, tip, register) in enumerate(ROSETTE_AXES):
        th = np.deg2rad(SPOKE_START - i * SPOKE_STEP)
        col = PERCEPT_C if register == "perceptual" else CONFIG_C
        ax.plot([th, th], [R_VOID, 1.0], color="#DDD6C8", lw=1.0, zorder=1)
        v = d.get(attr)
        vals = [r.get(attr) for r in R.values() if r.get(attr) is not None]
        if v is not None and vals:
            lo, hi = min(vals), max(vals)
            t = (v - lo) / (hi - lo) if hi > lo else 0.5
            r = R_VOID + t * (1 - R_VOID)
            ax.plot([th, th], [R_VOID, r], color=col, lw=3.0,
                    solid_capstyle="round", zorder=2)
            ax.scatter([th], [r], s=30, c=col, edgecolors="#2a2a2a",
                       linewidths=0.6, zorder=3)
        ax.annotate(tip, (th, 1.24), ha="center", va="center", fontsize=5.5,
                    color="#5a5a5a")
    ax.plot(gtheta, [R_VOID] * 90, color="#C4BCAC", lw=0.8, zorder=1)
    if d.get("char_divergence"):
        ax.plot(gtheta, [1.12] * 90, color=ACCENT, lw=1.8, zorder=4)
    nm = _short(d.get("long_name") or d.get("name") or "?", 10)
    ax.annotate(nm, (0, 0), ha="center", va="center", fontsize=7.8,
                fontweight="bold",
                color=ACCENT if d.get("char_divergence") else "#1c1c1c")
    if not d.get("reliable", True) and d.get("prospect") is not None:
        ax.annotate("indicative", (np.deg2rad(270), 0.16), ha="center",
                    fontsize=5.4, color="#8a8a8a")
    ax.set_ylim(0, 1.32)
    ax.set_xticks([]); ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor("none")


def rosette_legend(ax):
    """Board-B master legend: every axis with BOTH poles stated."""
    ax.axis("off")
    lines = [
        ("ROOM ROSETTE — how to read", "#1c1c1c", 8.0, True),
        ("stem length = the room's place within THIS building's", "#4a4a4a", 6.2, False),
        ("range: rim = the most of any room here · centre = the least", "#4a4a4a", 6.2, False),
        ("", "#444", 3.4, False),
        ("PERCEPTUAL stems (indigo) — felt from within:", PERCEPT_C, 6.8, True),
        ("open — rim: the most open room · centre: the most enclosed", "#333", 6.1, False),
        ("contrasting — rim: strongest internal variety · centre: uniform", "#333", 6.1, False),
        ("intricate — rim: most broken-up view · centre: plainest", "#333", 6.1, False),
        ("", "#444", 3.4, False),
        ("CONFIGURATIONAL stems (wine) — the plan position:", CONFIG_C, 6.8, True),
        ("integrated — rim: the social hub · centre: most segregated", "#333", 6.1, False),
        ("private — rim: deepest, most closable · centre: most public", "#333", 6.1, False),
        ("reachable — rim: easiest to reach · centre: most withdrawn", "#333", 6.1, False),
        ("", "#444", 3.4, False),
        ("vermilion ring = DIVERGENCE: the registers disagree", ACCENT, 6.6, True),
        ("(e.g. visually intricate yet the most reachable — a control hall)", "#4a4a4a", 5.9, False),
        ("'indicative' = small room, low sampling support", "#7a7a7a", 5.9, False),
    ]
    y = 0.99
    for text, colr, fs, bold in lines:
        ax.text(0.02, y, text, fontsize=fs, color=colr,
                fontweight="bold" if bold else "normal",
                transform=ax.transAxes, va="top")
        y -= 0.060
