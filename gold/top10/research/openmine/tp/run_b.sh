#!/bin/bash
# run_b.sh CAND [CAND...]: stage-B smoke = opening-winner seats of goldg + top10g and live0927 2500+ from step 0 (tp_diag)
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/openmine/tp/out
for c in "$@"; do
  for g in goldg top10g; do
    NPROC=${NPROC:-3} ../.venv/Scripts/python.exe gold/top10/research/openmine/tp/tp_diag.py elite $g gold/top10/cands/full_$c.py $O/${g}_$c.jsonl OW 2>&1 | grep -v "Loading env" >> $O/smoke_b.log
  done
  NPROC=${NPROC:-3} ../.venv/Scripts/python.exe gold/top10/research/openmine/tp/tp_diag.py live gold/top10/gates/live0927_2500.json gold/top10/cands/full_$c.py $O/live_$c.jsonl 2>&1 | grep -v "Loading env" >> $O/smoke_b.log
  echo "done $c $(date -u +%H:%M)" >> $O/smoke_b.log
done
