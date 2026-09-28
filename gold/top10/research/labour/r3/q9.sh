#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
until [ -f $R/q8.done ]; do sleep 15; done
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $R/goldg56_refs.jsonl $C/full_lab_pE12.py $R/goldg56_lab_pE12.jsonl > $R/goldg56_lab_pE12.log 2>&1
PIN_GIDS=$R/ids_live60.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_lab_pE12.py $R/live60_q9.jsonl offhand > $R/live60_q9.log 2>&1
echo done > $R/q9.done
