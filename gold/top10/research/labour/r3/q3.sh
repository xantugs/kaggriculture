#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
until [ -f $R/q2.done ]; do sleep 10; done
for v in lab_w27 lab_w27all lab_ehs lab_ehsA lab_pC lab_pD; do
  $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $R/goldg56_refs.jsonl $C/full_$v.py $R/goldg56_$v.jsonl > $R/goldg56_$v.log 2>&1
done
PIN_GIDS=$R/ids_live60.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_lab_pC.py,$C/full_lab_pD.py $R/live60_q3.jsonl offhand > $R/live60_q3.log 2>&1
echo done > $R/q3.done
