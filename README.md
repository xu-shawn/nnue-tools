# nnue-tools

Cheap tests for Stockfish NNUE training ideas, to run before a full
[nettest](https://github.com/vondele/nettest) run.

| | |
|---|---|
| [proxy/](proxy) | The nettest recipe cut down to 40 minutes on one GPU. |
| [bench/](bench) | Three fixed position sets, and scripts that score a net on them. |
| [match/](match) | Play two nets against each other and score the games. |

## A typical test

1. Train a baseline and a variant with the same seed ([proxy/](proxy)).
2. Compare them on the fixed sets ([bench/](bench)).
3. If the variant looks better, play a match ([match/](match)).
4. If it wins, open a nettest PR.

```bash
bash nnue-tools/proxy/setup.sh                       # once per box
cd nnue-pytorch && . venv/bin/activate
../nnue-tools/proxy/run.sh base 1
../nnue-tools/proxy/run.sh wd04 1 --ft-weight-decay=0.04
python ../nnue-tools/bench/compare.py runs/base/bench runs/wd04/bench
```

Everything targets [nnue-pytorch](https://github.com/official-stockfish/nnue-pytorch)
at `0a1c697` and the recipe of nettest main at `d49d991`.
