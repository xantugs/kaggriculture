#!/bin/bash
# fresh28_run.sh : the frozen tapes on the fresh elite gate (851 seats of top-45 teams from the 27-28 Sep daily datasets)
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; G=gold/top10/gates
for f in FWt T8fcWt; do
  NPROC=8 $PY gold/elite/elite_gate.py run $G/fresh28_games.jsonl.gz $G/fresh28_refs.jsonl gold/final/${f}_final.py $O/fresh28/$f.jsonl > $O/fresh28/$f.log 2>&1 &
done
wait
echo "tapes done $(date -u +%H:%M)"
NPROC=16 $PY gold/elite/elite_gate.py run $G/fresh28_games.jsonl.gz $G/fresh28_refs.jsonl gold/final/c2tr_final.py $O/fresh28/c2tr.jsonl > $O/fresh28/c2tr.log 2>&1
echo "fresh28 done $(date -u +%H:%M)"
