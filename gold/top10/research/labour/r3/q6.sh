#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
until [ -f $R/q5.done ]; do sleep 15; done
for v in lab_pJ lab_pK lab_pEw; do
  $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $R/goldg56_refs.jsonl $C/full_$v.py $R/goldg56_$v.jsonl > $R/goldg56_$v.log 2>&1
done
PIN_GIDS=$R/ids_live60.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_lab_pJ.py,$C/full_lab_pK.py,$C/full_lab_pEw.py $R/live60_q6.jsonl offhand > $R/live60_q6.log 2>&1
PIN_GIDS=$R/ids_live3.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_lab_pE2.py $R/ident_pE2.jsonl offhand > $R/ident_pE2.log 2>&1
echo done > $R/q6.done
