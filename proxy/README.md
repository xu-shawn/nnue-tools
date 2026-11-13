# Proxy runs

A proxy is nettest's stage 1 with less data and a much shorter schedule.
Model, loss, position filters, learning rates and weight decay are unchanged
([options.sh](options.sh)).

| | nettest stage 1 | proxy |
|---|---|---|
| Data | 43 files | test80 Jan + Feb 2024, BT4 relabel (17.7 GB) |
| Batch size | 131072 over 4 GPUs | 16384 on 1 GPU |
| Steps | 4,587,520 (560 epochs) | 122,880 (15 epochs) |
| Positions seen | 601 billion | 2 billion |
| LR and lambda schedules | about 5.1M steps | 122,880 steps |
| Fake-quant warm-up | first 5% of steps | first 5% of steps |
| Stage 2 | yes | no |

One run takes about 40 minutes on an RTX 4090.

## Usage

```bash
bash setup.sh                    # trainer, Python environment, data
cd nnue-pytorch && . venv/bin/activate
../nnue-tools/proxy/run.sh <name> <seed> [extra train.py options]
```

Extra options override the recipe. A run leaves `runs/<name>/train.log`,
`net.nnue` (playable) and `bench/` (input for [compare.py](../bench)).

To test a trainer change, check out your branch in `nnue-pytorch` and rebuild
the loader with `scripts/compile_data_loader.sh`.

## Reading the results

- **Use the same seed for every net you compare.** Across three seeds, final
  loss varied by 0.12% and `lb` error by 0.07% (standard deviation). The ±
  from `compare.py` covers position sampling only, not this.
- **Loss cannot judge a change to the training data**, because the loss is
  measured on that data. Use the fixed sets and a match.
- **For other changes, loss is a fair guide**: about −1.6 Elo per +1% final
  training loss at equal engine speed, fitted on finished nettest runs.
- **A proxy gain is an estimate.** A shorter version of this recipe tracked
  eight nettest runs with r = 0.94, at about 0.6 of the full run's loss gap.
  New input features are the least reliable: often overstated about 2×,
  sometimes gone in the full run.
- **Proxy loss says nothing about engine speed.** Measure that separately.
