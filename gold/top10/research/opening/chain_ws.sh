#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
O=gold/top10/research/opening
until grep -q CHAIN_DONE $O/run_m2.log 2>/dev/null; do sleep 20; done
export PYTHONIOENCODING=utf-8
for N in w1 s1; do
  NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run gold/top10/cands/full_OP_$N.py $N hf 8 both > $O/run_$N.log 2>&1
  NPROC=3 bash $O/live.sh gold/top10/cands/full_OP_$N.py $N > $O/lpair_$N.log 2>&1
  echo CHAIN_DONE >> $O/run_$N.log
done
