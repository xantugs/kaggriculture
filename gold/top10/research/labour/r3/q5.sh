#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
for v in lab_pE lab_pG lab_pH lab_pI; do
  $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $R/goldg55_refs.jsonl $C/full_$v.py $R/goldg55_$v.jsonl > $R/goldg55_$v.log 2>&1
done
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $R/goldg56_refs.jsonl $C/full_lab_pH.py $R/goldg56_lab_pH.jsonl > $R/goldg56_lab_pH.log 2>&1
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $R/goldg56_refs.jsonl $C/full_lab_pI.py $R/goldg56_lab_pI.jsonl > $R/goldg56_lab_pI.log 2>&1
PIN_GIDS=$R/ids_live60.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_lab_pH.py,$C/full_lab_pI.py $R/live60_q5.jsonl offhand > $R/live60_q5.log 2>&1
PIN_GIDS=$R/ids_live131.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_lab_pE.py,$C/full_lab_pG.py,$C/full_lab_pH.py,$C/full_lab_pI.py $R/live131_q5.jsonl offhand > $R/live131_q5.log 2>&1
echo done > $R/q5.done
