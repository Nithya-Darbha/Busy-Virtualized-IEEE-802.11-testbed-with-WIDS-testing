#!/usr/bin/env python3
import sys, os, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from random_forest import CSV, COUNT, STRUCT, SEM, loco_rf, metrics

SETS = [
    ("count", COUNT),
    ("structural", STRUCT),
    ("semantic", SEM),
    ("count + structural", COUNT + STRUCT),
    ("count + semantic", COUNT + SEM),
    ("structural + semantic", STRUCT + SEM),
    ("count + structural + semantic", COUNT + STRUCT + SEM),
]

def main():
    df = pd.read_csv(CSV); y = df["label"].values
    rows = []
    print("random forest per feature set (leave-one-capture-out):")
    for name, feats in SETS:
        yh = loco_rf(df, feats)
        m = metrics(y, yh)
        rows.append(dict(features=name, n_features=len(feats), **m))
        print(f"  {name:30} P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} FPR={m['fpr']:.3f}")
        for load in ("low", "moderate", "high"):
            k = (df["load"] == load).values
            rows[-1][f"fpr_{load}"] = metrics(y[k], yh[k])["fpr"]
            rows[-1][f"recall_{load}"] = metrics(y[k], yh[k])["recall"]
    p = os.path.join(ROOT, "results", "feature_sets.csv")
    pd.DataFrame(rows).to_csv(p, index=False)
    print(f"--> {p}")

if __name__ == "__main__":
    main()