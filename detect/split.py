import csv

def load(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def folds(rows):
    for cell in sorted({r["cell"] for r in rows}):
        yield cell, [r for r in rows if r["cell"] != cell], [r for r in rows if r["cell"] == cell]