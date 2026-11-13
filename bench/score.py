"""Evaluate a net on the benchmark sets, quantized as the engine would.

Run from the nnue-pytorch directory, with the model options you would give serialize.py:

    python <nnue-tools>/bench/score.py net.nnue out_dir --features=Full_Threats+PP_3Wide+K32H3^ ...

Writes out_dir/<set>.npy: one static eval per position, internal units, side to move.
Accepts .nnue and .ckpt.
"""

import lzma
import os
import sys
import time
from dataclasses import dataclass, field

import numpy as np
import torch
import tyro
from tyro.conf import OmitArgPrefixes, Positional

sys.path.insert(0, os.getcwd())
import model as M  # noqa: E402
from data_loader import destroy_sparse_batch, get_sparse_batch_from_fens  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BATCH = 16384


@dataclass(frozen=True)
class Cli:
    net: Positional[str]
    out: Positional[str]
    sets: str = "lb,ltc,tree"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    nnue_config: OmitArgPrefixes[M.NNUEConfig] = field(default_factory=M.NNUEConfig)


def load(path, cfg):
    if path.endswith(".ckpt"):
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        M.use_checkpoint_stack_table(cfg, ckpt)
        nnue = M.NNUE(config=cfg)
        nnue.load_state_dict(ckpt["state_dict"])
        return nnue.model
    with open(path, "rb") as f:
        return M.NNUEReader(f, cfg.features, config=cfg.model_config).model


def fens_of(name):
    with lzma.open(f"{DATA}/{name}.tsv.xz", "rt") as f:
        next(f)
        return [line.split("\t", 1)[0] for line in f]


def main():
    args = tyro.cli(Cli)
    model = load(args.net, args.nnue_config)
    model.clip_weights(include_input=True)
    model = model.to(args.device).eval()
    scale = model.quantization.nnue2score
    os.makedirs(args.out, exist_ok=True)
    for name in args.sets.split(","):
        fens, t0 = fens_of(name), time.time()
        evals = np.zeros(len(fens), np.float32)
        for i in range(0, len(fens), BATCH):
            chunk = fens[i : i + BATCH]
            zeros = [0] * len(chunk)
            b = get_sparse_batch_from_fens(
                model.input_feature_name, chunk, zeros, zeros, zeros, model.ls_keys
            )
            us, them, wi, bi, _, _, ls = b.contents.get_tensors(args.device)
            with torch.no_grad():
                # True, True: fake-quantized activations and weights. Float scoring
                # of low-LR checkpoints can be badly off.
                out = model(us, them, wi, bi, ls, True, True)
            evals[i : i + len(chunk)] = (out.view(-1) * scale).float().cpu().numpy()
            destroy_sparse_batch(b)
        np.save(f"{args.out}/{name}.npy", evals)
        print(f"{name}: {len(fens)} positions, {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
