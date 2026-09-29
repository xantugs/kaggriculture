#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
O=gold/top10/research/opening
export PYTHONIOENCODING=utf-8
NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_mf3.py mf3 hf 8 both > $O/run_mf3.log 2>&1
NPROC=3 bash $O/live.sh gold/top10/cands/full_OP_mf3.py mf3 > $O/lpair_mf3.log 2>&1
echo CHAIN_DONE >> $O/run_mf3.log
