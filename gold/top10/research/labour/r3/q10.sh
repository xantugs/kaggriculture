#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
v=T7lab_nf
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_$v.py $R/goldg111_$v.jsonl > $R/goldg111_$v.log 2>&1
$PY gold/harness/pinned4.py gold/top10/gates/live0927.json 288 $C/full_$v.py $R/live0927_$v.jsonl offhand > $R/live0927_$v.log 2>&1
PIN_GIDS=$R/ids_live60.txt $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_$v.py $R/live60_$v.jsonl offhand > $R/live60_$v.log 2>&1
echo done > $R/q10.done
