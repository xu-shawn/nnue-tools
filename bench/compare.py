"""Compare nets on the benchmark sets.

    python compare.py <baseline dir> <net dir> [<net dir> ...]

Each dir holds the .npy files written by score.py. Prints the change in error
against the baseline in percent (negative = better) with a bootstrap standard
error. See README.md for the metric.
"""

import lzma
import os
import sys

import numpy as np
from scipy.optimize import isotonic_regression

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
rng = np.random.default_rng(0)


def table(name):
    with lzma.open(f"{DATA}/{name}.tsv.xz", "rt") as f:
        head = next(f).rstrip("\n").split("\t")
        cols = list(zip(*(line.rstrip("\n").split("\t") for line in f)))
    return {h: np.array(c) for h, c in zip(head, cols)}


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def label_prob(score):
    """Expected score the trainer assigns to a label (internal units)."""
    off, scale = 289.1258344152218, 379.98724077106635  # out-offset, out-scaling
    return 0.5 * (1 + sigmoid((score - off) / scale) - sigmoid((-score - off) / scale))


def counts(fens, letters):
    boards = [f.split(" ", 1)[0] for f in fens]
    return np.array([sum(b.count(c) for c in letters) for b in boards])


def engine_scale(evals, fens):
    """Material scaling and 50-move damping the engine applies to the raw eval."""
    values = {"Pp": 521, "Nn": 781, "Bb": 825, "Rr": 1276, "Qq": 2538}
    material = sum(v * counts(fens, k) for k, v in values.items())
    rule50 = np.array([int(f.split(" ")[4]) for f in fens])
    return evals * (1 + material / 90649) * (1 - rule50 / 189)


def errors(evals, target):
    """Squared error after the best monotone map from eval to target."""
    _, inv = np.unique(evals, return_inverse=True)
    n = np.bincount(inv).astype(float)
    fit = isotonic_regression(np.bincount(inv, target) / n, weights=n).x[inv]
    return (fit - target) ** 2


def change(ea, eb, mask=None, groups=None, n_boot=200):
    """Error change in percent, with a bootstrap over positions or groups."""
    if mask is not None:
        ea, eb = ea[mask], eb[mask]
        groups = None if groups is None else groups[mask]
    if groups is None:
        sa, sb = ea, eb
    else:
        _, g = np.unique(groups, return_inverse=True)
        sa, sb = np.bincount(g, ea), np.bincount(g, eb)
    k = len(sa)
    boot = []
    for _ in range(n_boot):
        w = np.bincount(rng.integers(0, k, k), minlength=k)
        boot.append((w * sa).sum() / (w * sb).sum() - 1)
    return f"{100 * (ea.sum() / eb.sum() - 1):+.2f} ± {100 * np.std(boot):.2f}"


def name(path):
    parts = os.path.normpath(path).split(os.sep)
    return parts[-2] if parts[-1] == "bench" and len(parts) > 1 else parts[-1]


def by_pieces(fens):
    n = counts(fens, "PNBRQKpnbrqk")
    return [
        ("all", None),
        ("<=8 pieces", n <= 8),
        ("9-16 pieces", (n > 8) & (n <= 16)),
        ("17+ pieces", n > 16),
    ]


def main():
    base, arms = sys.argv[1], sys.argv[2:]
    tree, lb, ltc = table("tree"), table("lb"), table("ltc")

    quiet = (tree["wins_material"] == "0") & (tree["hanging"] == "0")
    tree_cp = tree["score_cp"].astype(float).clip(-3000, 3000)
    tree_splits = [
        ("all", None),
        ("quiet", quiet),
        ("quiet fresh evals", quiet & (tree["fresh"] == "1")),
        ("pv nodes", tree["kind"] == "pv"),
        ("roots", tree["kind"] == "root"),
        ("qsearch", tree["qsearch"] == "1"),
    ]
    lb_target = label_prob(lb["score"].astype(float).clip(-1500, 1500))
    ltc_splits = by_pieces(ltc["fen"])

    # title, file, target, bootstrap groups, splits
    tests = [
        ("tree", "tree", sigmoid(tree_cp / 361.0), None, tree_splits),
        ("lb", "lb", lb_target, lb["game"], by_pieces(lb["fen"])),
        (
            "ltc vs search",
            "ltc",
            label_prob(ltc["search"].astype(float)),
            ltc["game"],
            ltc_splits,
        ),
        ("ltc vs result", "ltc", ltc["result"].astype(float), ltc["game"], ltc_splits),
    ]

    def evals(directory, file):
        x = np.load(f"{directory}/{file}.npy").astype(float)
        return engine_scale(x, ltc["fen"]) if file == "ltc" else x

    print(f"error change vs {name(base)} in % (negative = better)\n")
    print((" " * 34 + "".join(f"{name(a):<16}" for a in arms)).rstrip())
    for title, file, target, groups, splits in tests:
        eb = errors(evals(base, file), target)
        ea = [errors(evals(a, file), target) for a in arms]
        for split, mask in splits:
            cells = "".join(f"{change(e, eb, mask, groups):<16}" for e in ea)
            print(f"{title:<15}{split:<19}{cells}".rstrip())
            title = ""


if __name__ == "__main__":
    main()
