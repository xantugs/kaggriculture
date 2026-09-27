#!/bin/bash
# sf8 baselines on the new current-top gates, after the pin249 run
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
PY=../.venv/Scripts/python.exe; export PYTHONIOENCODING=utf-8
until grep -q "gold/top10/full/sf8_c23.py:" gold/top10/gates/pin249_sf8.log 2>/dev/null; do sleep 30; done
for g in top10g goldg; do
  NPROC=8 $PY gold/elite/elite_gate.py run gold/top10/gates/${g}_games.jsonl.gz gold/top10/gates/${g}_refs.jsonl gold/top10/lean_sf8.py gold/top10/gates/${g}_sf8.jsonl > gold/top10/gates/${g}_sf8.log 2>&1
done
echo QUEUE2 DONE
