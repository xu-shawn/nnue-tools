# Matches

Two nets on the same Stockfish binary, fishtest STC conditions: 8+0.08, one
thread, 16 MB hash, `UHO_Lichess_4852_v1`, fishtest's draw and resign rules.

```bash
bash setup.sh x86-64-avx2                           # Stockfish, fastchess, book
bash match.sh new_vs_base new.nnue base.nnue 10000  # 10000 pairs = 20000 games
python pgn_score.py new_vs_base.pgn --pov new
```

20,000 games take about 2 hours on 64 cores.

## Notes

- **Openings are fixed by the seed.** Two matches against the same baseline
  play the same openings, so they can be compared pair by pair:
  `python pgn_score.py a_vs_base.pgn b_vs_base.pgn`.
- **`pgn_score.py` drops pairs with a time forfeit or crash.** Busy machines
  produce a few, and they are not the net's fault.
- **Longer time controls**: `TC=60+0.6 bash match.sh ...`.
- **Shared or noisy machines**: `TC=80+0.8 NODESTIME=60 bash match.sh ...`
  counts nodes instead of time (the same search budget as 8+0.08 at 600 knps),
  and games come out the same on any machine. This hides speed differences, so
  use it only for nets of the same architecture.
- The log starts with each net's bench signature, to confirm which net played.
