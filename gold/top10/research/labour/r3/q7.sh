#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
R=gold/top10/research/labour/r3; C=gold/top10/cands; PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=3
until [ -f $R/q6.done ]; do sleep 15; done
v=lab_pE2
$PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz $R/top10g90_refs.jsonl $C/full_$v.py $R/top10g90_$v.jsonl > $R/top10g90_$v.log 2>&1
PIN_GIDS=$R/ids_pin83.txt $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 $C/full_$v.py $R/pin83_$v.jsonl offhand > $R/pin83_$v.log 2>&1
PIN_GIDS=$R/ids_s2800_90.txt $PY gold/harness/pinned4.py moon/strong2800.json,moon/strong_new.json 144 $C/full_$v.py $R/s2800_90_$v.jsonl offhand > $R/s2800_90_$v.log 2>&1
$PY gold/harness/pinned4.py gold/top10/gates/live0927.json 288 $C/full_$v.py $R/live0927_$v.jsonl offhand > $R/live0927_$v.log 2>&1
echo done > $R/q7.done
