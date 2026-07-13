"""
Stage 3 validation — lexicon (3A) + building structure (3B).

3A  T1: prospect banding respects the model-ladder boundaries (12.5/37.5/62.5/87.5).
    T2: unreliable rooms are hedged ('indicatively'); stair nodes get the
        stair sentence; unreachable rooms get the neutral clause.
    T3: multi-exterior-door plans with no name hint default to ALL entrances
        (flagged as guess); FZK's name hint still picks the front door alone.
3B  T4: FZK — Galerie reconnects through the stair at depth 3; Flur is
        integration rank 1 (the hub).
    T5: Duplex — both stairs land in their unit's L2 Hallway; NO unreachable
        rooms; depth gradient reaches 5 (Utility deepest); Foyer rank 1.
    T6: every vertical edge has kind='stair' and one-step semantics
        (depth increments by exactly 1 across it).
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("ifc_layer", "graph_layer", "core"):
    sys.path.insert(0, os.path.join(HERE, "..", p))

import pandas as pd
import ifc_reader, scp, structure, lexicon

IFC = os.path.join(HERE, "..", "test_files", "ifc")
FZK_CSV = "/home/claude/fzk_B_opaque.csv"
DUP_CSV = "/home/claude/duplex_L1.csv"


def test_lexicon():
    # T1 band boundaries
    assert lexicon.band(87.5, lexicon.PROSPECT_BANDS)[0] == "expansive"
    assert lexicon.band(87.4, lexicon.PROSPECT_BANDS)[0] == "open"
    assert lexicon.band(12.5, lexicon.PROSPECT_BANDS)[0] == "intimate"
    assert lexicon.band(12.4, lexicon.PROSPECT_BANDS)[0] == "confined"
    assert lexicon.band(45.0, lexicon.JUMP_BANDS)[0] == "dramatic"
    # T2 hedging / stair / unreachable
    hedged = lexicon.room_sentence(dict(long_name="Tiny", name="T1", prospect=5,
                                        variety=1, reliable=False, depth=2), 3)
    assert "indicatively" in hedged and "low sampling support" in hedged
    stair = lexicon.room_sentence(dict(long_name="Stair", name="S", is_stair=True))
    assert "stair volume" in stair
    unreach = lexicon.room_sentence(dict(long_name="Attic", name="A", prospect=50,
                                         variety=5, reliable=True, depth=None), 3)
    assert "not reachable" in unreach
    print("T1+T2 PASSED — banding, hedging, stair & unreachable sentences")


def test_entrances():
    sts = ifc_reader.extract_building(os.path.join(IFC, "Duplex.ifc"))
    l1 = next(s for s in sts if s["storey_name"] == "Level 1")
    df = pd.read_csv(DUP_CSV)
    G, _ = scp.build_scp_graph(l1, df, wall_solid=l1["wall"])
    assert len(G.graph["entrances"]) == 2 and G.graph["entrance_is_guess"]
    fzk = ifc_reader.extract_building(os.path.join(IFC, "FZK_Haus.ifc"))[0]
    Gf, _ = scp.build_scp_graph(fzk, pd.read_csv(FZK_CSV), wall_solid=fzk["wall"])
    names = {n: Gf.nodes[n]["long_name"] for n in Gf.nodes
             if Gf.nodes[n].get("kind") == "room"}
    assert [names[g] for g in Gf.graph["entrances"]] == ["Flur"]
    print("T3 PASSED    — multi-entrance default (Duplex=2) & name-hint (FZK=Flur)")


def _building(ifc_name, csv, storey_names=None):
    sts = ifc_reader.extract_building(os.path.join(IFC, ifc_name))
    if storey_names:
        sts = [s for s in sts if s["storey_name"] in storey_names]
    df = pd.read_csv(csv)
    graphs = []
    for i, st in enumerate(sts):
        d = df if i == 0 else df.iloc[0:0]
        graphs.append(scp.build_scp_graph(st, d, wall_solid=st["wall"])[0])
    return structure.build_building_graph(sts, graphs)


def test_fzk_building():
    B = _building("FZK_Haus.ifc", FZK_CSV)
    R = {B.nodes[n]["long_name"]: B.nodes[n] for n in B.nodes
         if B.nodes[n].get("kind") == "room"}
    assert R["Galerie"]["depth"] == 3, f"Galerie {R['Galerie']['depth']}"
    assert R["Flur"]["integration_rank"] == 1
    assert any(d.get("kind") == "stair" for _, _, d in B.edges(data=True))
    print("T4 PASSED    — FZK: Galerie depth 3 via stair; Flur is the hub")


def test_duplex_building():
    B = _building("Duplex.ifc", DUP_CSV, ("Level 1", "Level 2"))
    rooms = [(n, B.nodes[n]) for n in B.nodes if B.nodes[n].get("kind") == "room"]
    assert all(d.get("depth") is not None for _, d in rooms), "unreachable rooms remain"
    stair_edges = [(a, b) for a, b, d in B.edges(data=True) if d.get("kind") == "stair"]
    assert len(stair_edges) == 2
    landings = {B.nodes[b]["name"] if B.nodes[b]["long_name"] == "Hallway"
                else B.nodes[a]["name"] for a, b in stair_edges}
    assert landings == {"A201", "B201"}, f"landings {landings}"
    depths = [d["depth"] for _, d in rooms]
    assert max(depths) == 5
    deepest = [d["long_name"] for _, d in rooms if d["depth"] == 5]
    assert set(deepest) == {"Utility"}
    hub = min(rooms, key=lambda nd: nd[1]["integration_rank"])[1]["long_name"]
    assert hub == "Foyer"
    for a, b, d in B.edges(data=True):                                   # T6
        if d.get("kind") == "stair":
            da, db = B.nodes[a].get("depth"), B.nodes[b].get("depth")
            if da is not None and db is not None:
                assert abs(da - db) == 1, "stair must be one topological step"
    print("T5+T6 PASSED — Duplex: reconnected, gradient to 5, hubs & one-step stairs")


if __name__ == "__main__":
    test_lexicon(); test_entrances(); test_fzk_building(); test_duplex_building()
    print("STAGE 3 VALIDATION: ALL PASSED")
