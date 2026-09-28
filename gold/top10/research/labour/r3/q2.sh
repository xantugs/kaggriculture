#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
until [ -f $R/q1.done ]; do sleep 20; done
PIN_GIDS=$R/ids_live60.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_lab_w27.py,$C/full_lab_w27all.py,$C/full_lab_ehs.py,$C/full_lab_ehsA.py $R/live60_q2.jsonl offhand > $R/live60_q2.log 2>&1
echo done > $R/q2.done
