#!/bin/bash
# One proxy run: train, export, score on the benchmark sets.
#
#   run.sh <name> <seed> [extra train.py options]
#
# Run from the nnue-pytorch directory. Output goes to runs/<name>/:
# train.log, net.nnue (ready for matches) and bench/*.npy for bench/compare.py.
# Give every net you want to compare the same seed.
set -e
NAME=$1 SEED=$2; shift 2
TOOLS=$(cd "$(dirname "$0")/.." && pwd)
DATA=${DATA:-data}
FILES=${FILES:-"$DATA/jan.binpack $DATA/feb.binpack"}
STEPS=${STEPS:-8192} EPOCHS=${EPOCHS:-15} BATCH=${BATCH:-16384}
TOTAL=$((STEPS * EPOCHS))
. "$TOOLS/proxy/options.sh"
R=runs/$NAME; mkdir -p $R

python -u train.py $FILES --default_root_dir=$R $MODEL $TRAIN \
  --batch-size=$BATCH --epoch-size=$((BATCH * STEPS)) --validation-size=$((BATCH * 256)) \
  --max_epochs=$EPOCHS --one-cycle-steps=$TOTAL --lambda-schedule-steps=$TOTAL \
  --fake-quant-warmup-steps=$((TOTAL / 20)) --network-save-period=0 \
  --init-seed=$SEED --seed=$((41 + SEED)) \
  --num-workers=${WORKERS:-32} --threads=2 "$@" > $R/train.log 2>&1

CKPT=$(ls $R/training_logs/*/checkpoints/last.ckpt | head -1)
python -u serialize.py $CKPT $R/net.nnue $MODEL --compression=none \
  --ft-optimize --ft-optimize-data=$DATA/fishpack32.binpack --ft-optimize-count=100000 \
  > $R/export.log 2>&1
python -u "$TOOLS/bench/score.py" $R/net.nnue $R/bench $MODEL > $R/score.log 2>&1
rm -f $R/training_logs/*/checkpoints/*.ckpt   # over 1 GB each
grep -o "train_loss_epoch=[0-9.e-]*" $R/train.log | tail -1
