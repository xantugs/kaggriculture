#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_a.py a hf 8 both > $O/run_a.log 2>&1
NPROC=3 bash $O/live.sh gold/top10/cands/full_OP_a.py a > $O/lpair_a.log 2>&1
echo CHAIN_DONE >> $O/run_a.log
