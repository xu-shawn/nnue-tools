"""Score a fastchess match from its PGN, or compare two matches.

    python pgn_score.py match.pgn[.gz] [--pov NAME]    Elo of NAME against the other
    python pgn_score.py a.pgn[.gz] b.pgn[.gz]          paired difference a - b

Game pairs with a time forfeit, crash or missing game are dropped. The paired
mode needs two matches against the same opponent on the same openings (same
book, seed and round count).
"""

import argparse
import gzip
import math
import re
import sys

TAG = re.compile(r'^\[(\w+) "(.*)"\]')
POINTS = {"1-0": (1.0, 0.0), "0-1": (0.0, 1.0), "1/2-1/2": (0.5, 0.5)}
CLEAN = ("normal", "adjudication")


def rounds_of(path):
    """Round number -> list of its games (header tags only)."""
    opener = gzip.open if path.endswith(".gz") else open
    rounds, game = {}, {}
    with opener(path, "rt", errors="replace") as f:
        for line in f:
            m = TAG.match(line)
            if not m:
                continue
            if m.group(1) == "Event":
                game = {}
            game[m.group(1)] = m.group(2)
            if m.group(1) == "Round":
                rounds.setdefault(m.group(2), []).append(game)
    return rounds


def players(rounds):
    first = next(iter(rounds.values()))[0]
    return first["White"], first["Black"]


def pair_scores(rounds, pov):
    """Round -> points of `pov` in the round's two games (0..2); clean pairs only."""
    scores = {}
    for r, gs in rounds.items():
        if len(gs) == 2 and all(
            g.get("Result") in POINTS and g.get("Termination") in CLEAN for g in gs
        ):
            scores[r] = sum(POINTS[g["Result"]][g["White"] != pov] for g in gs)
    return scores


def elo(s):
    s = min(max(s, 1e-9), 1 - 1e-9)
    return -400 * math.log10(1 / s - 1)


def mean_var(xs):
    m = sum(xs) / len(xs)
    return m, sum((x - m) ** 2 for x in xs) / len(xs)


def report(path, pov):
    rounds = rounds_of(path)
    names = players(rounds)
    pov = pov or names[0]
    if pov not in names:
        sys.exit(f"--pov must be one of {names[0]}, {names[1]}")
    other = names[1] if pov == names[0] else names[0]
    scores = pair_scores(rounds, pov)
    xs = [s / 2 for s in scores.values()]
    mu, var = mean_var(xs)
    se = math.sqrt(var / len(xs))
    k = 800 / math.log(10) / math.sqrt(2 * var)
    ptnml = [sum(1 for s in scores.values() if s == v) for v in (0, 0.5, 1, 1.5, 2)]
    print(
        f"{pov} vs {other}: {2 * len(xs)} games, {len(rounds) - len(xs)} pairs dropped"
    )
    print(
        f"Elo  {elo(mu):+.2f} +/- {(elo(mu + 1.96 * se) - elo(mu - 1.96 * se)) / 2:.2f}"
    )
    print(f"nElo {(mu - 0.5) * k:+.2f} +/- {1.96 * se * k:.2f}")
    print(f"Ptnml(0-2) {ptnml}")


def compare(path_a, path_b):
    ra, rb = rounds_of(path_a), rounds_of(path_b)
    a, b = players(ra)[0], players(rb)[0]
    shared = set(players(ra)) & set(players(rb))
    if len(shared) == 1:  # the shared name is the common opponent
        (opponent,) = shared
        a = next(p for p in players(ra) if p != opponent)
        b = next(p for p in players(rb) if p != opponent)
    sa, sb = pair_scores(ra, a), pair_scores(rb, b)
    both = [r for r in sa if r in sb]
    if any(ra[r][0].get("FEN") != rb[r][0].get("FEN") for r in both):
        sys.exit("the two matches did not use the same openings")
    ma, _ = mean_var([sa[r] / 2 for r in both])
    mb, _ = mean_var([sb[r] / 2 for r in both])
    _, var = mean_var([(sa[r] - sb[r]) / 2 for r in both])
    se = math.sqrt(var / len(both))
    mid = (ma + mb) / 2
    slope = 400 / math.log(10) / (mid * (1 - mid))
    print(f"{a} - {b}: {len(both)} shared pairs")
    print(f"Elo difference {elo(ma) - elo(mb):+.2f} +/- {1.96 * se * slope:.2f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pgn", nargs="+")
    p.add_argument("--pov", help="default: White in the first game of the file")
    args = p.parse_args()
    if len(args.pgn) == 1:
        report(args.pgn[0], args.pov)
    else:
        compare(args.pgn[0], args.pgn[1])
