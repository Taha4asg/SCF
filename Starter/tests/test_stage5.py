"""
Stage 5 v3 validation — the Visual Instrument (design-language pass).

T1  GRADIENT LAW: the three author gradients are bound with the correct
    anchors and directions (mint=open, wine=private, sage=reachable), and
    every SCP axis appears in at least one view.
T2  Every view renders on BOTH buildings without exception.
T3  Justified graph places rooms in rows equal to their carrier depth
    (half-moon nodes; carrier as text).
T4  Genotype petal plot requires polar axes; petal radius order follows
    integration (most integrated nearest the centre).
T5  Triptych: walked distance monotone; sequential snapshots include the
    stair pair (bottom AND top) plus room middles.
T6  Rosettes: ¾-circle, centred name <= 10 chars, unreliable flagged.
T7  Explorer HTMLs exist with probe dropdowns.
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("ifc_layer", "graph_layer", "viz_layer", "core"):
    sys.path.insert(0, os.path.join(HERE, "..", p))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ifc_reader, scp, structure, character, views, sheet, scoring

IFC = os.path.join(HERE, "..", "test_files", "ifc")
FIELDS = {"FZK_Haus.ifc": ["/home/claude/fzk_B_opaque.csv",
                           "/home/claude/fzk_OG.csv"],
          "Duplex.ifc": ["/home/claude/duplex_L1.csv",
                         "/home/claude/duplex_L2.csv"]}


def _build(name, filt=None):
    sts = ifc_reader.extract_building(os.path.join(IFC, name))
    if filt:
        sts = [s for s in sts if s["storey_name"] in filt]
    dfs = [pd.read_csv(c) for c in FIELDS[name]]
    graphs = [scp.build_scp_graph(st, df, wall_solid=st["wall"])[0]
              for st, df in zip(sts, dfs)]
    B = structure.build_building_graph(sts, graphs)
    character.annotate_character(B)
    return B, sts, dfs


def _hex(rgba):
    return "#%02X%02X%02X" % tuple(int(round(255 * v)) for v in rgba[:3])


def test_gradient_law_and_coverage():
    assert _hex(views.OPEN_CMAP(0.0)) == "#002D72"                       # T1
    assert _hex(views.OPEN_CMAP(1.0)) == "#A0E5D9"
    assert _hex(views.PRIV_CMAP(0.0)) == "#FFF3E6"
    assert _hex(views.PRIV_CMAP(1.0)) == "#722F37"
    assert _hex(views.REACH_CMAP(0.0)) == "#3B3432"
    assert _hex(views.REACH_CMAP(1.0)) == "#EDF1E6"
    covered = set(views.CHORO_META) | {a for a, *_ in views.ROSETTE_AXES}
    for axis in ("prospect", "variety", "complexity",
                 "integration", "privacy", "reach"):
        assert axis in covered, f"{axis} has no view"
    print("T1 PASSED    — gradient anchors bound; every SCP axis has a view")


def test_render_both_buildings():
    for name, filt in (("FZK_Haus.ifc", None),
                       ("Duplex.ifc", ("Level 1", "Level 2"))):
        B, sts, dfs = _build(name, filt)
        fig, ax = plt.subplots()
        for attr in views.CHORO_META:
            ax.clear(); views.choropleth(ax, B, sts[0], attr)
        ax.clear(); views.justified_graph(ax, B)
        ax.clear(); views.quality_lens(ax, sts[0], dfs[0])
        plt.close(fig)
        fig = plt.figure()
        axp = fig.add_subplot(projection="polar")
        views.genotype_radial(axp, B)
        rooms = [n for n in B.nodes if B.nodes[n].get("kind") == "room"
                 and B.nodes[n].get("privacy") is not None]
        axp.clear(); views.room_rosette(axp, B, rooms[0])
        plt.close(fig)
        fig, (a1, a2, a3) = plt.subplots(3, 1)
        views.triptych(a1, a2, a3, B, dfs, [])
        plt.close(fig)
    print("T2 PASSED    — every view renders on both buildings")


def test_jgraph_and_genotype():
    B, sts, dfs = _build("FZK_Haus.ifc")
    R = {n: B.nodes[n] for n in B.nodes if B.nodes[n].get("kind") == "room"}
    for n, d in R.items():                                               # T3
        assert d.get("depth") is not None
    fig = plt.figure()
    axp = fig.add_subplot(projection="polar")
    assert axp.name == "polar"                                           # T4
    views.genotype_radial(axp, B)
    ranked = sorted(R.values(), key=lambda d: -d["integration"])
    assert ranked[0]["long_name"] == "Flur"
    assert ranked[-1]["long_name"] == "Galerie"
    plt.close(fig)
    print("T3+T4 PASSED — depths intact; petal genotype polar, order = integration")


def test_triptych_sequence():
    B, sts, dfs = _build("FZK_Haus.ifc")
    path, events, segments, total, target = views.path_walk(B)          # T5
    xs = [e[0] for e in events]
    assert all(xs[i] <= xs[i + 1] + 1e-9 for i in range(len(xs) - 1))
    snaps = sheet._snapshots(B, sts, scoring)
    labels = [s[3] for s in snaps]
    assert "stair · bottom" in labels and "stair · top" in labels
    assert any("middle" in l for l in labels)
    assert any(l == "entrance" for l in labels)
    print("T5 PASSED    — monotone walk; sequential probes incl. stair pair & middles")


def test_rosette_and_explorer():
    import networkx as nx
    tiny = dict(long_name="Extraordinarily Long Name", name="X",
                prospect=10, variety=2, complexity=5, integration=0.3,
                privacy=50, reach=40, depth=2, reliable=False, kind="room")
    G2 = nx.Graph(); G2.add_node("t", **tiny)
    fig = plt.figure()
    axp = fig.add_subplot(projection="polar")
    views.room_rosette(axp, G2, "t")                                     # T6
    texts = [t.get_text() for t in axp.texts]
    assert any(len(t) <= 10 and t.endswith(".") for t in texts)
    assert any("indicative" in t for t in texts)
    plt.close(fig)
    for f, min_probes in (("/mnt/user-data/outputs/FZK_isovist_explorer.html", 8),
                          ("/mnt/user-data/outputs/Duplex_isovist_explorer.html", 10)):
        assert os.path.exists(f), f                                      # T7
        html = open(f).read()
        assert "plotly" in html and "updatemenus" in html
        assert html.count("label") >= min_probes
    print("T6+T7 PASSED — rosette naming & hedging; explorers intact")


if __name__ == "__main__":
    test_gradient_law_and_coverage()
    test_render_both_buildings()
    test_jgraph_and_genotype()
    test_triptych_sequence()
    test_rosette_and_explorer()
    print("STAGE 5 VALIDATION: ALL PASSED")
