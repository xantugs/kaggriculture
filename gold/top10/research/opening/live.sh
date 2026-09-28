#!/bin/bash
# live.sh CAND TAG [gids_file] : pinned replay from step 0 on the live 2500+ slice, then paired vs T8
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
G=${3:-$O/gids_live51.txt}
PIN_GIDS=$G NPROC=${NPROC:-3} ../.venv/Scripts/python.exe gold/harness/pinned4.py gold/top10/gates/lv0928hi.json 0 "$1" $O/live_$2.jsonl offhand > $O/live_$2.log 2>&1
../.venv/Scripts/python.exe $O/lpair.py $O/live_$2.jsonl
