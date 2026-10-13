import csv, random
from collections import defaultdict

SEED = 14
TEST_FRAC = 0.3

def load(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def split(rows, test_frac=TEST_FRAC, seed=SEED):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["cell"], r["label"])].append(r)
    rng = random.Random(seed)
    train, test = [], []
    for key in sorted(groups):
        g = sorted(groups[key], key=lambda r: float(r["win"]))
        rng.shuffle(g)
        k = round(len(g) * test_frac)
        test += g[:k]; train += g[k:]
    return train, test