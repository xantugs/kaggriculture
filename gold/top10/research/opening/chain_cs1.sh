#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_cs1.py cs1 hf 8 both > $O/run_cs1.log 2>&1
NPROC=3 bash $O/c2s3.sh gold/top10/cands/full_OP_cs1.py cs1 > $O/c2s3_cs1.log 2>&1
NPROC=3 bash $O/live.sh gold/top10/cands/full_OP_cs1.py cs1 > $O/lpair_cs1.log 2>&1
echo CHAIN_DONE >> $O/run_cs1.log
