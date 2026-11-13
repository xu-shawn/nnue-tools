#!/bin/bash
# Build what a match needs in the current directory: Stockfish, fastchess, the book.
#   setup.sh [ARCH]      e.g. x86-64-avx2 (default), x86-64-avx512icl
set -e
ARCH=${1:-x86-64-avx2}
git clone -q https://github.com/official-stockfish/Stockfish.git
(cd Stockfish && git checkout -q 43e01e07 && cd src && make -j profile-build ARCH=$ARCH > build.log 2>&1)
git clone -q https://github.com/Disservin/fastchess.git
(cd fastchess && git checkout -q f08ca02 && make -j > build.log 2>&1)
curl -sLO https://github.com/official-stockfish/books/raw/master/UHO_Lichess_4852_v1.epd.zip
unzip -o -q UHO_Lichess_4852_v1.epd.zip
Stockfish/src/stockfish bench 2>&1 | grep "Nodes searched"
