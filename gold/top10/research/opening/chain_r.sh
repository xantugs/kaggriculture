#!/bin/bash
# chain_r.sh NAME : identity on 12 C2S3 elite seats, then 24 herd-first seats, then the 51-game live slice
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; N=$1
NPROC=${NPROC:-3} ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_$N.py ${N}c "Azat A,mtmr_s,TheEgg" 4 both > $O/run_${N}c.log 2>&1
NPROC=${NPROC:-3} ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_$N.py $N hf 8 both > $O/run_$N.log 2>&1
NPROC=${NPROC:-3} bash $O/live.sh gold/top10/cands/full_OP_$N.py $N > $O/lpair_$N.log 2>&1
echo CHAIN_DONE >> $O/run_$N.log
