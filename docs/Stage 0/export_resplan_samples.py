"""
Run this ON YOUR PC (where ResPlan.pkl lives) to enable the one deferred
Stage 0 test: exact geometry-half reproduction against capstone features.
Exports land/wall of 3 plans as WKT into test_files/resplan_samples/.
Then commit + push via GitHub Desktop.
"""
import os, pickle
from shapely import wkt

DATASET_PATH = r"D:\Architecture\cardiff\Algorithmic Thinking\floorplans\ResPlan\ResPlan.pkl"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_files", "resplan_samples")
PLAN_IDS = [250, 489, 800]   # 250 = the inference notebook's own demo plan

os.makedirs(OUT, exist_ok=True)
with open(DATASET_PATH, "rb") as f:
    dataset = pickle.load(f)
for pid in PLAN_IDS:
    plan = dataset[pid]
    for key in ("land", "wall"):
        with open(os.path.join(OUT, f"plan_{pid}_{key}.wkt"), "w") as f:
            f.write(plan[key].wkt)
    print(f"exported plan {pid}")
print("Done — commit test_files/resplan_samples/ and push.")
