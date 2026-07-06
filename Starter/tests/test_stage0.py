"""
Stage 0 validation — FINAL (both tests pass; see docs/stage0_report.md).

TEST 1 (geometry half): synthetic two-room plan, walls as a merged holed
polygon (the hard case), 0.9 m door. Verifies rays are blocked, isovist
areas match physical room areas, and quality ordering follows enclosure.

TEST 2 (scoring half): the module must be NUMERICALLY IDENTICAL to an
independent re-implementation of notebook cell 4's ML block on all 221
capstone plans (84,560 points): zero prediction mismatches, quality
deviation < 1e-9.

NOTE: kmeans_model.pkl / cluster_map.pkl are STALE artifacts from a
pre-GMM pipeline generation (55% purity vs the final RF) and are NOT part
of the inference chain. Do not use them as an oracle.
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core"))

import joblib
import numpy as np
import pandas as pd
from shapely.geometry import box
from shapely.ops import unary_union
from sklearn.preprocessing import MinMaxScaler

import scoring

CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")

def test_geometry_half():
    t = 0.3
    outer = [box(0,0,12,t), box(0,8-t,12,8), box(0,0,t,8), box(12-t,0,12,8)]
    partition = [box(7.0,t,7.3,6.0), box(7.0,6.9,7.3,8-t)]      # 0.9 m door
    land, wall = box(0,0,12,8), unary_union(outer + partition)  # holed union
    df, meta = scoring.score_plan(land, wall, CORE)
    z = lambda x0,x1,y0,y1: df[(df.x>x0)&(df.x<x1)&(df.y>y0)&(df.y<y1)]
    big, small = z(2,5,3,5), z(9,11,1,3)
    assert meta["n_points"] > 1000
    assert np.isfinite(df[scoring.FEATURES].values).all()
    assert abs(big.Av.mean() - 51.6) < 2.0,  "big-room isovist area != physical area"
    assert abs(small.Av.mean() - 33.1) < 2.0, "small-room isovist area != physical area"
    assert big.quality_score.mean() > small.quality_score.mean()
    print("TEST 1 PASSED — geometry half: rays blocked, areas physical, ordering correct")

def test_scoring_half():
    rf = joblib.load(os.path.join(CORE, "trained_rf_model.joblib"))
    gs = joblib.load(os.path.join(CORE, "data_scaler.joblib"))
    master = pd.read_csv(os.path.join(CORE, "master_dataset.csv"))
    QMAP = scoring.QUALITY_MAP
    W = np.array([scoring.WEIGHTS[f] for f in scoring.FEATURES])
    mism, qdev, total = 0, 0.0, 0
    for pid in master.plan_id.unique():
        sub = master[master.plan_id == pid]
        if len(sub) < 30: continue
        Xn = gs.transform(MinMaxScaler().fit_transform(sub[scoring.FEATURES])) * W
        pred_nb = rf.predict(Xn)
        proba = rf.predict_proba(Xn)
        q_nb = (proba * np.array([QMAP[c] for c in rf.classes_])).sum(axis=1) * 100
        out = scoring.score_features(sub.reset_index(drop=True), rf, gs, smoothing=False)
        mism += (out["spatial_type"].values != pred_nb).sum()
        qdev = max(qdev, np.abs(out["quality_score"].values - q_nb).max())
        total += len(sub)
    assert mism == 0 and qdev < 1e-9, f"mismatches={mism}, qdev={qdev}"
    print(f"TEST 2 PASSED — scoring half: identical to notebook on {total} points")

if __name__ == "__main__":
    test_geometry_half()
    test_scoring_half()
    print("STAGE 0 VALIDATION: ALL PASSED")
