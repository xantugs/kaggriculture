#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
O=gold/top10/research/opening
export PYTHONIOENCODING=utf-8
NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_mf1.py mf1 hf 8 both > $O/run_mf1.log 2>&1
NPROC=3 bash $O/live.sh gold/top10/cands/full_OP_mf1.py mf1 > $O/lpair_mf1.log 2>&1
echo CHAIN_DONE >> $O/run_mf1.log
