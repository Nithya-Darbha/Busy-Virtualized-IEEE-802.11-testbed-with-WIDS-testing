"""Rule-based detector: threshold on the deauth count (fit on train only)."""
import sys, os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from split import load, folds

FEATS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "processed", "features.csv")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results")

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
    div = lambda a, b: a / b if b else 0.0
    return dict(precision=div(tp, tp + fp), recall=div(tp, tp + fn),
        f1=div(2 * tp, 2 * tp + fp + fn), fpr=div(fp, fp + tn),
        accuracy=div(tp + tn, tp + fp + tn + fn))

def fit(train):
    best_T, best_f1 = 0, -1.0
    for T in range(0, max(int(r["n_deauth"]) for r in train) + 1):
        f1 = metrics(*confusion(train, predict(train, T)))["f1"]
        if f1 >= best_f1: best_T, best_f1 = T, f1
    return best_T

def main():
    rows = load(FEATS)
    out, tested, pred = [], [], []
    print(f"[rule] {len(rows)} windows, leave-one-capture-out")
    for cell, train, test in folds(rows):
        T = fit(train)
        p = predict(test, T)
        print(f"  held out {cell:28} threshold: attack if n_deauth > {T}")
        tested += test; pred += p
        out += [dict(cell=r["cell"], rate=r["rate"], load=r["load"], win=r["win"],
                     label=r["label"], threshold=T, pred_rule=q) for r, q in zip(test, p)]
    m = metrics(*confusion(tested, pred))
    print(f" P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} FPR={m['fpr']:.3f} Acc={m['accuracy']:.3f}")

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "rule_based_predictions.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(f"out-of-fold predictions --> {path}")

if __name__ == "__main__":
    main()