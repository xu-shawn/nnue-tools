# Options of nettest main (d49d991, the #587 recipe). Sourced by run.sh.
# Only the run length, batch size and data are changed for a proxy; see run.sh.

MODEL="--features=Full_Threats+PP_3Wide+K32H3^ --l1=1024 --l2=32
 --ls-keys=piececount:queen:pawnhalf:manyoffi
 --ls-factors=piececount+queen:pawnhalf:manyoffi
 --ls-remap-data=$DATA/fishpack32.binpack --ls-remap-min=50"

TRAIN="--optimizer-name=adamw --lr=0.4e-3 --factorized-weight-decay=4.0e-5
 --random-fen-skipping=3 --early-fen-skipping=18 --soft-early-fen_skipping=32
 --pc-y0=-0.20 --pc-y1=0.45 --pc-y2=1.0 --pc-y3=0.95 --pc-y4=0.75
 --ply-x1=0.00 --ply-y1=0.025 --ply-x2=22.0 --ply-y2=0.05
 --ply-x3=25.5 --ply-y3=0.20 --ply-x4=29.5 --ply-y4=0.80
 --pow-exp=2.4340402395048404 --qp-asymmetry=0.22866886710086187
 --in-scaling=295.6539508488627 --out-scaling=379.98724077106635
 --in-offset=285.2706341467852 --out-offset=289.1258344152218
 --one-cycle-warmup-pct=0.05 --one-cycle-final-div=1e3
 --lambda-cycle-jitter --jitter-lambda-sample=0.0035 --jitter-lambda-batch=0.0070
 --jitter-decay-lambda-batch=0.999 --start-lambda=1.0 --end-lambda=1.0
 --lambda-cycle-warmup-pct=0.25 --lambda-cycle-delta=-0.3
 --ft-bucket-lr-mult=0.25 --threat-lr-mult=0.5
 --ft-weight-decay=0.02 --virtual-ft-weight-decay=0.02"
