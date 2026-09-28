#!/bin/bash
# run_smoke.sh CAND [CAND...]: opening-winner seats of goldg and top10g + live0927 2500+ games from step 0, NPROC=4
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/openmine/tp/out
for c in "$@"; do
  for g in goldg top10g; do
    NPROC=${NPROC:-4} ../.venv/Scripts/python.exe gold/top10/research/openmine/tp/tp_diag.py elite $g gold/top10/cands/full_$c.py $O/${g}_$c.jsonl OW 2>&1 | grep -v "Loading env" >> $O/smoke.log
  done
  NPROC=${NPROC:-4} ../.venv/Scripts/python.exe gold/top10/research/openmine/tp/tp_diag.py live gold/top10/gates/live0927_2500.json gold/top10/cands/full_$c.py $O/live_$c.jsonl 2>&1 | grep -v "Loading env" >> $O/smoke.log
  echo "done $c $(date -u +%H:%M)" >> $O/smoke.log
done
