#!/bin/bash
# divergent-path ablations on the current-top gates (after queue2's sf8 baselines)
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
PY=../.venv/Scripts/python.exe; export PYTHONIOENCODING=utf-8
until grep -q "lean_sf8.py:" gold/top10/gates/goldg_sf8.log 2>/dev/null; do sleep 30; done
for c in a_s2toff a_d18 a_dpoff a_herdoff a_melonoff a_tickoff a_d15 a_rw2 a_care8; do
  for g in top10g goldg; do
    NPROC=${NPROC:-10} $PY gold/elite/elite_gate.py run gold/top10/gates/${g}_games.jsonl.gz gold/top10/gates/${g}_refs.jsonl gold/top10/cands/full_$c.py gold/top10/gates/${g}_$c.jsonl > gold/top10/gates/${g}_$c.log 2>&1
  done
done
echo QUEUE3 DONE
