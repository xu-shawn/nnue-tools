# Benchmark sets

Three fixed sets of positions with labels. A net is scored by how well its
static eval predicts the label.

| Set | Positions | What | Label |
|---|---|---|---|
| `lb` | 1,557,645 from 248,083 games | Game positions like the trainer sees: a third each from Stockfish 5000-node self-play, Leela test60 and Leela test80 games | BT4 eval, as in the training data |
| `ltc` | 1,548,261 from 43,168 games | Quiet positions from fishtest LTC games (60+0.6) | The engine's own search score, and the game result |
| `tree` | 54,875 | Positions from inside Stockfish's search during self-play: fresh evals, PV nodes and game positions | Stockfish depth-12 search |

`lb` shows whether a net fits its training target, `ltc` whether its eval
agrees with deep search and results in real games, and `tree` whether it is
right where search actually asks for an eval.

## Usage

Run from the `nnue-pytorch` directory. `score.py` takes the same model options
as `serialize.py`; the defaults fit the current master net.

```bash
python ../nnue-tools/bench/score.py base.nnue out/base --features=Full_Threats+PP_3Wide+K32H3^
python ../nnue-tools/bench/score.py new.nnue  out/new  --features=Full_Threats+PP_3Wide+K32H3^
python ../nnue-tools/bench/compare.py out/base out/new
```

Scoring a net takes a few minutes on a CPU. `compare.py` accepts several
nets and prints one column each:

```
error change vs base in % (negative = better)

                                  new
tree           all                -3.66 ± 0.27
               quiet              -4.39 ± 0.54
               ...
lb             all                +2.08 ± 0.14
ltc vs search  all                +3.19 ± 0.12
ltc vs result  all                +1.07 ± 0.07
```

## The metric

1. Evals are computed with the trainer's quantized forward pass, which matches
   the engine. For `ltc` they also get the engine's material scaling and
   50-move damping.
2. Each net's evals are mapped to an expected score by the best monotone fit to
   the labels (isotonic regression), so the eval scale does not matter.
3. Error is the mean squared difference from the label's expected score.
4. The table shows error(net) / error(baseline) − 1, with a bootstrap standard
   error over games (`lb`, `ltc`) or positions (`tree`).

## Files

All files in `data/` are tab-separated text, xz-compressed, one position per
line. Scores are from the side to move's view.

**`lb.tsv.xz`**: `fen`, `score` (BT4 eval, Stockfish internal units), `result`
(−1, 0, 1), `source` (`n5k`, `t60`, `t80`), `game`. Sampled from nettest
training files with the trainer's filters, so not held out.

**`ltc.tsv.xz`**: `fen`, `search` (score the engine reported in the game,
internal units), `result` (0, 0.5, 1), `game`. From fishtest run
`6ad263a2733e627f7058c476`. Quiet means not in check and the move played was
not a capture or promotion.

**`tree.tsv.xz`**: `fen`, `score_cp` (depth-12 search by Stockfish with net
`nn-d1ee674a62ca`, centipawns), then:

| Column | Meaning |
|---|---|
| `kind` | `eval`: a node where search asked for a static eval. `pv`: a PV node. `root`: a game position. |
| `tc` | Time control of the self-play game: `stc`, `ltc`, `vltc`. |
| `fresh` | 1 if the net computed the eval, 0 if it came from the hash table (always 0 for `root`). |
| `qsearch` | 1 if the node was in quiescence search. |
| `wins_material` | 1 if the side to move has a promotion or a winning capture. |
| `hanging` | 1 if the opponent would have one, were it their move. |

"Quiet" in the table means neither of the last two.
