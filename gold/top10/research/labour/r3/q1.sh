#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
PIN_GIDS=$R/ids_live60.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_T7.py,$C/full_lab_pA.py,$C/full_lab_pB.py $R/live60_q1.jsonl offhand > $R/live60_q1.log 2>&1
for v in T7 lab_pA lab_pB; do
  $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $R/goldg56_refs.jsonl $C/full_$v.py $R/goldg56_$v.jsonl > $R/goldg56_$v.log 2>&1
done
echo done > $R/q1.done
