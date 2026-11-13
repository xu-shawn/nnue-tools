#!/bin/bash
# Set up a fresh GPU box for proxy runs: trainer, Python environment, data.
# Written for the image nvidia/cuda:12.8.1-devel-ubuntu24.04 (host driver must
# support CUDA 12.8). Leaves everything in ./nnue-pytorch. About 35 GB of disk.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git cmake g++ curl aria2 xz-utils python3 python3.12-dev > /dev/null
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=$HOME/.local/bin:$PATH

git clone -q https://github.com/official-stockfish/nnue-pytorch.git
cd nnue-pytorch
git checkout -q 0a1c697   # the trainer nettest main uses
uv venv -q -p 3.12 venv && . venv/bin/activate
uv pip install -q torch --index-url https://download.pytorch.org/whl/cu128
grep -v -E "^(ruff|numpy)" requirements.txt > /tmp/requirements.txt
uv pip install -q -r /tmp/requirements.txt "numpy<2.0" cupy-cuda12x
bash scripts/compile_data_loader.sh > loader.log 2>&1

mkdir -p data && cd data
HF=https://huggingface.co/datasets
T80=$HF/xushawn/test80-bt4-relabel/resolve/main
aria2c -q -x 16 -s 16 -o jan.binpack $T80/test80-2024-01-jan-2tb7p.min-v2.v6.relabel.binpack
aria2c -q -x 16 -s 16 -o feb.binpack $T80/test80-2024-02-feb-2tb7p.min-v2.v6.relabel.binpack
aria2c -q -x 16 -s 16 -o fishpack32.binpack \
  $HF/official-stockfish/master-binpacks/resolve/main/fishpack32.binpack
ls -la
python -c "import torch, cupy; print('ready:', torch.cuda.get_device_name(0))"
