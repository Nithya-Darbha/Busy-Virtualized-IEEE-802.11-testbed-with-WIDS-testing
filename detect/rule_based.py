#!/usr/bin/env python3
"""Rule-based detector: threshold on the deauth count (fit on train only)."""
import sys, os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from split import load, split

FEATS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "processed", "features.csv")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results")
RATES = ["none", "low", "moderate", "high"]
LOADS = ["low", "moderate", "high"]

def predict(rows, T):
    return [1 if int(r["n_deauth"]) > T else 0 for r in rows]

def confusion(rows, pred):
    tp = fp = tn = fn = 0
    for r, p in zip(rows, pred):
        y = int(r["label"])
        if y and p: tp += 1
        elif y: fn += 1
        elif p: fp += 1
        else: tn += 1
    return tp, fp, tn, fn

def metrics(tp, fp, tn, fn):
    div = lambda a, b: a / b if b else None
    return dict(tp=tp, fp=fp, tn=tn, fn=fn,
        precision=div(tp, tp + fp), recall=div(tp, tp + fn),
        f1=div(2 * tp, 2 * tp + fp + fn), fpr=div(fp, fp + tn),
        accuracy=div(tp + tn, tp + fp + tn + fn))

def fit(train):
    sweep = []
    for T in range(0, max(int(r["n_deauth"]) for r in train) + 1):
        sweep.append(dict(threshold=T, **metrics(*confusion(train, predict(train, T)))))
    best = max(sweep, key=lambda s: (s["f1"] or 0.0, s["threshold"]))
    return best["threshold"], sweep

def fmt(v):
    return "" if v is None else (f"{v:.4f}" if isinstance(v, float) else v)

def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
        w.writerows({k: fmt(v) for k, v in r.items()} for r in rows)

def main():
    train, test = split(load(FEATS))
    T, sweep = fit(train)
    pred = predict(test, T)
    print(f"train={len(train)}  test={len(test)}  threshold: attack if n_deauth > {T}")

    summary = []
    def add(scope, rate, load_, rows, p):
        m = metrics(*confusion(rows, p)); summary.append(dict(scope=scope, rate=rate, load=load_, **m))
        print(f"  {scope:7} {rate:9} {load_:9} " + "  ".join(
            f"{k}={'-' if m[k] is None else format(m[k], '.3f')}" for k in ("precision", "recall", "f1", "fpr", "accuracy")))
    add("train", "all", "all", train, predict(train, T))
    add("test", "all", "all", test, pred)
    for rate in RATES:
        for load_ in LOADS:
            idx = [i for i, r in enumerate(test) if r["rate"] == rate and r["load"] == load_]
            if idx: add("test", rate, load_, [test[i] for i in idx], [pred[i] for i in idx])

    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, "rule_based_threshold_sweep.csv"), sweep)
    write(os.path.join(OUT, "rule_based_summary.csv"), summary)
    write(os.path.join(OUT, "rule_based_predictions.csv"),
        [dict(cell=r["cell"], rate=r["rate"], load=r["load"], win=r["win"],
              n_deauth=r["n_deauth"], label=r["label"], pred=p) for r, p in zip(test, pred)])
    print(f"wrote sweep, summary and predictions -> {OUT}")

if __name__ == "__main__":
    main()