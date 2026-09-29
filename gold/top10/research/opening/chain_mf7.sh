#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
O=gold/top10/research/opening
until grep -q CHAIN_DONE $O/run_mf5.log 2>/dev/null; do sleep 20; done
export PYTHONIOENCODING=utf-8
NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_mf7.py mf7 hf 8 both > $O/run_mf7.log 2>&1
NPROC=3 bash $O/live.sh gold/top10/cands/full_OP_mf7.py mf7 > $O/lpair_mf7.log 2>&1
echo CHAIN_DONE >> $O/run_mf7.log
