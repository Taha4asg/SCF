"""
Stage 2 validation — the Spatial Character Profile.

T1  FZK: point->room assignment coverage > 95%.
T2  FZK: prospect reproduces the Stage-1 per-room means on identical data
    (Wohnen 83.4, Küche ~99.9 on the opaque-stair field).
T3  FZK: carrier depths match the hand-derived justified graph
    (Flur=1; Schlafzimmer/Bad/Buero/Wohnen/Küche=2).
T4  FZK: variety discriminates — Küche is monotype (variety < 3,
    entropy < 0.1); Schlafzimmer is the most-mixed reliable room.
T5  FZK: every access edge carries kind ∈ {door, opening}, width > 0,
    and jump == |Δprospect| where both ends have prospect.
T6  Duplex L1: mirrored units produce near-identical SCPs
    (|ΔP| < 3 for Living and Kitchen pairs); mislabeled stair space
    ('Room') is a depth-only node via GEOMETRIC detection.
T7  Duplex L2 (no scoring needed): rooms unreachable from the carrier
    degrade to depth=None — never an exception.
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("ifc_layer", "graph_layer", "core"):
    sys.path.insert(0, os.path.join(HERE, "..", p))

import pandas as pd
import ifc_reader, scp

IFC = os.path.join(HERE, "..", "test_files", "ifc")
FZK_CSV = "/home/claude/fzk_B_opaque.csv"
DUP_CSV = "/home/claude/duplex_L1.csv"


def _named(G):
    return {G.nodes[n]["long_name"]: dict(G.nodes[n]) for n in G.nodes
            if G.nodes[n].get("kind") == "room"}


def test_fzk():
    st = ifc_reader.extract_building(os.path.join(IFC, "FZK_Haus.ifc"))[0]
    df = pd.read_csv(FZK_CSV)
    G, cov = scp.build_scp_graph(st, df, wall_solid=st["wall"])
    assert cov > 0.95, f"coverage {cov:.1%}"                              # T1
    R = _named(G)
    assert abs(R["Wohnen"]["prospect"] - 83.4) < 0.5                       # T2
    assert R["Küche"]["prospect"] > 99.0                                   # T2
    assert R["Flur"]["depth"] == 1                                         # T3
    for r in ("Schlafzimmer", "Bad", "Buero", "Wohnen", "Küche"):
        assert R[r]["depth"] == 2, f"{r} depth {R[r]['depth']}"            # T3
    # entrance detection: both exterior doors found; front door auto-chosen
    name = {n: G.nodes[n]["long_name"] for n in G.nodes if G.nodes[n].get("kind")=="room"}
    ext = {name[g] for g in G.graph["exterior_doors"]}
    assert ext == {"Flur", "Wohnen"}, f"exterior doors {ext}"
    assert [name[g] for g in G.graph["entrances"]] == ["Flur"], "front door not auto-chosen"
    assert G.graph["entrance_is_guess"] is True
    # exterior-touch recorded (D10): perimeter rooms > 0, none negative
    assert all(R[r]["exterior_touch"] >= 0 for r in R)
    assert R["Wohnen"]["exterior_touch"] > 5 and R["Flur"]["exterior_touch"] >= 0
    assert R["Küche"]["variety"] < 3 and R["Küche"]["mix_entropy"] < 0.1   # T4
    rel = {k: v for k, v in R.items() if v["reliable"]}
    assert max(rel, key=lambda k: rel[k]["variety"]) == "Schlafzimmer"     # T4
    for a, b, d in G.edges(data=True):                                     # T5
        assert d["kind"] in ("door", "opening") and d["width"] and d["width"] > 0
        pa, pb = G.nodes[a].get("prospect"), G.nodes[b].get("prospect")
        if pa is not None and pb is not None:
            # jump_avg must equal |Δprospect|; primary jump is local when available
            assert abs(d["jump_avg"] - abs(pa - pb)) < 0.02
            assert d["jump_source"] in ("local", "average")
            if d["jump_source"] == "local":
                assert d["jump"] == d["jump_local"]
    print("T1–T5 PASSED — FZK: coverage, prospect identity, justified depths,")
    print("               variety discrimination, edge attribute integrity")


def test_duplex():
    sts = ifc_reader.extract_building(os.path.join(IFC, "Duplex.ifc"))
    l1 = next(s for s in sts if s["storey_name"] == "Level 1")
    df = pd.read_csv(DUP_CSV)
    G, cov = scp.build_scp_graph(l1, df, wall_solid=l1["wall"])
    assert cov > 0.95
    rooms = [dict(G.nodes[n]) for n in G.nodes if G.nodes[n].get("kind") == "room"]
    for name in ("Living Room", "Kitchen"):                                # T6
        pair = sorted(r["prospect"] for r in rooms
                      if r["long_name"] == name and r["prospect"] is not None)
        assert len(pair) == 2 and abs(pair[0] - pair[1]) < 3, f"{name}: {pair}"
    mislabeled = [r for r in rooms if r["long_name"] == "Room"]
    assert mislabeled and mislabeled[0]["is_stair"] and mislabeled[0]["prospect"] is None
    print("T6 PASSED    — Duplex L1: mirror-unit consistency; geometric stair detection")

    l2 = next(s for s in sts if s["storey_name"] == "Level 2")             # T7
    G2, _ = scp.build_scp_graph(l2, df.iloc[0:0], wall_solid=l2["wall"])
    depths = [G2.nodes[n].get("depth") for n in G2.nodes
              if G2.nodes[n].get("kind") == "room"]
    assert all(d is None for d in depths)
    print("T7 PASSED    — Duplex L2: unreachable rooms degrade to depth=None")


if __name__ == "__main__":
    test_fzk(); test_duplex()
    print("STAGE 2 VALIDATION: ALL PASSED")
