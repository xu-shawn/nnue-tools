#!/bin/bash
# Fishtest-style STC match between two nets on one Stockfish binary.
#
#   match.sh <name> <net A> <net B> <game pairs>
#
# Writes <name>.pgn and <name>.log. Run from the directory setup.sh filled.
# Environment: TC (default 8+0.08), NODESTIME (unset = timed), RESERVE (cores
# left idle, default 2), SEED (same seed = same openings in every match).
NAME=$1 A=$(realpath -s $2) B=$(realpath -s $3) PAIRS=$4
SF=${SF:-Stockfish/src/stockfish}
BOOK=${BOOK:-UHO_Lichess_4852_v1.epd}
ulimit -n 65536 || ulimit -n $(ulimit -Hn)   # each game holds 12 pipe ends

# One logical cpu per physical core, among the cpus this shell may use.
CPUS=$(python3 -c "
import os
seen, pick = set(), []
for c in sorted(os.sched_getaffinity(0)):
    t = f'/sys/devices/system/cpu/cpu{c}/topology/'
    core = open(t + 'physical_package_id').read(), open(t + 'core_id').read()
    if core not in seen:
        seen.add(core); pick.append(str(c))
print(','.join(pick))")
N=$(( $(echo $CPUS | tr , '\n' | wc -l) - ${RESERVE:-2} ))

for net in $A $B; do   # the bench signature identifies the net in the log
  printf "setoption name EvalFile value $net\nbench 16 1 10\nquit\n" | $SF 2>&1 |
    grep "Nodes searched" | sed "s|^|$net: |"
done > $NAME.log

taskset -c $CPUS fastchess/fastchess \
  -engine cmd=$SF name=$(basename $A .nnue) option.EvalFile=$A \
  -engine cmd=$SF name=$(basename $B .nnue) option.EvalFile=$B \
  -each proto=uci tc=${TC:-8+0.08} option.Hash=16 option.Threads=1 \
    ${NODESTIME:+option.nodestime=$NODESTIME} \
  -openings file=$BOOK format=epd order=random -srand ${SEED:-20261110} \
  -rounds $PAIRS -games 2 -repeat -concurrency $N -recover \
  -draw movenumber=34 movecount=8 score=20 \
  -resign movecount=3 score=600 twosided=true \
  -ratinginterval 200 -pgnout file=$NAME.pgn >> $NAME.log 2>&1
