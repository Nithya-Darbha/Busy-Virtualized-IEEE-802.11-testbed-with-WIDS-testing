#!/usr/bin/env python3
import sys, os, math
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results")
EXT = "svg"

RATES = ["none", "low", "moderate", "high"]
LOADS = ["low", "moderate", "high"]
DETECTORS = [("pred_rule", "Threshold", "#eb6834", "s"), ("pred_rf", "Random forest", "#2a78d6", "o")]
RATE_COLOR = {"low": "#86b6ef", "moderate": "#2a78d6", "high": "#0d366b"}
RATE_MARKER = {"low": "o", "moderate": "s", "high": "^"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "pdf.fonttype": 42, "svg.fonttype": "path",
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "legend.frameon": False})

def counts(d, col):
    y, p = d["label"], d[col]
    return (int(((y == 1) & (p == 1)).sum()), int(((y == 0) & (p == 1)).sum()),
            int(((y == 0) & (p == 0)).sum()), int(((y == 1) & (p == 0)).sum()))

def metrics(d, col):
    tp, fp, tn, fn = counts(d, col)
    div = lambda a, b: a / b if b else float("nan")
    return dict(tp=tp, fp=fp, tn=tn, fn=fn, precision=div(tp, tp + fp), recall=div(tp, tp + fn),
        f1=div(2 * tp, 2 * tp + fp + fn), fpr=div(fp, fp + tn), accuracy=div(tp + tn, tp + fp + tn + fn))

def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, max(0.0, p - (c - h)), max(0.0, (c + h) - p)

def save(fig, name):
    path = os.path.join(RES, f"{name}.{EXT}")
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    print(f"  {path}")

def load_axis(ax):
    ax.set_xticks(range(len(LOADS))); ax.set_xticklabels(LOADS)
    ax.set_xlim(-0.4, len(LOADS) - 0.6); ax.set_xlabel("Background traffic load")
    ax.grid(axis="x", visible=False)

def plot_detection(df):
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.8), sharey=True)
    for ax, (col, name, _, _) in zip(axes, DETECTORS):
        for i, rate in enumerate(RATES[1:]):
            xs, ps, lo, hi = [], [], [], []
            for j, load in enumerate(LOADS):
                d = df[(df["rate"] == rate) & (df["load"] == load) & (df["label"] == 1)]
                p, a, b = wilson(int(d[col].sum()), len(d))
                xs.append(j + (i - 1) * 0.08); ps.append(p); lo.append(a); hi.append(b)
            ax.errorbar(xs, ps, yerr=[lo, hi], color=RATE_COLOR[rate], marker=RATE_MARKER[rate], lw=1.6, ms=5,
                capsize=2.5, elinewidth=0.9, mec="white", mew=0.6, label=rate)
        ax.set_title(name, loc="left", color=INK); load_axis(ax); ax.set_ylim(0, 1.05)
    axes[0].set_ylabel("Detection rate (recall)")
    axes[1].legend(title="Attacker rate", loc="lower right")
    fig.tight_layout()
    save(fig, "fig_detection_vs_load")

def plot_fpr(df):
    fig, ax = plt.subplots(figsize=(4.2, 2.8))
    for i, (col, name, color, marker) in enumerate(DETECTORS):
        xs, ps, lo, hi = [], [], [], []
        for j, load in enumerate(LOADS):
            d = df[(df["load"] == load) & (df["label"] == 0)]
            p, a, b = wilson(int(d[col].sum()), len(d))
            xs.append(j + (i - 0.5) * 0.08); ps.append(p); lo.append(a); hi.append(b)
        ax.errorbar(xs, ps, yerr=[lo, hi], color=color, marker=marker, lw=1.6, ms=5, capsize=2.5,
            elinewidth=0.9, mec="white", mew=0.6, label=name)
        ax.annotate(f"{ps[-1]:.1%}", (xs[-1], ps[-1]), xytext=(8, 0), textcoords="offset points",
            va="center", color=INK, fontsize=8)
    load_axis(ax); ax.set_ylim(0, None); ax.set_ylabel("False positive rate")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.legend(loc="upper left")
    fig.tight_layout()
    save(fig, "fig_fpr_vs_load")

def plot_features(sets, rule):
    rows = [("Threshold: count", rule, DETECTORS[0][2])]
    rows += [(f"RF: {r['features']}", r, DETECTORS[1][2]) for _, r in sets.iterrows()]
    rows = rows[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.9), sharey=True)
    for ax, (key, title, pct) in zip(axes, [("f1", "F1-score", False), ("fpr", "False positive rate", True)]):
        vals = [r[key] for _, r, _ in rows]
        ax.barh(range(len(rows)), vals, height=0.62, color=[c for _, _, c in rows])
        for i, v in enumerate(vals):
            ax.text(v + max(vals) * 0.02, i, f"{v:.1%}" if pct else f"{v:.3f}", va="center", color=INK, fontsize=8)
        ax.set_title(title, loc="left", color=INK); ax.set_xlim(0, max(vals) * 1.2)
        ax.grid(axis="y", visible=False)
        if pct: ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axes[0].set_yticks(range(len(rows))); axes[0].set_yticklabels([n for n, _, _ in rows])
    axes[0].tick_params(axis="y", colors=INK, length=0)
    fig.tight_layout()
    save(fig, "fig_feature_sets")

def main():
    rule = pd.read_csv(os.path.join(RES, "rule_based_predictions.csv"))
    rf = pd.read_csv(os.path.join(RES, "rf_predictions.csv"))
    df = rule.merge(rf[["cell", "win", "label", "pred_rf"]], on=["cell", "win"], suffixes=("", "_rf"))
    if len(df) != len(rule) or len(df) != len(rf) or (df["label"] != df["label_rf"]).any():
        print("the two prediction files do not cover the same windows"); sys.exit(1)
    print(f"{len(df)} windows, {int(df['label'].sum())} attack, {df['cell'].nunique()} captures, same windows for both detectors\n")

    overall, cells = [], []
    for col, name, _, _ in DETECTORS:
        m = metrics(df, col); overall.append(dict(detector=name, **m))
        print(f"{name:14} P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} FPR={m['fpr']:.3f} Acc={m['accuracy']:.3f}")
        for rate in RATES:
            for load in LOADS:
                d = df[(df["rate"] == rate) & (df["load"] == load)]
                cells.append(dict(detector=name, rate=rate, load=load, **metrics(d, col)))
    pd.DataFrame(overall).to_csv(os.path.join(RES, "metrics_overall.csv"), index=False)
    pd.DataFrame(cells).to_csv(os.path.join(RES, "metrics_by_cell.csv"), index=False)

    print("\nfigures:")
    plot_detection(df)
    plot_fpr(df)
    sets = os.path.join(RES, "feature_sets.csv")
    if os.path.exists(sets):
        plot_features(pd.read_csv(sets), overall[0])

if __name__ == "__main__":
    main()