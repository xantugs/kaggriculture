#!/bin/bash
# main-session gate queue: pin249 and 2800+ for sf8 / copy-takeover day 22 / 23, then a closed-loop subset
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
PY=../.venv/Scripts/python.exe; export PYTHONIOENCODING=utf-8
until [ "$(wc -l < gold/top10/gates/live_sf8_copyday.jsonl)" -ge 955 ]; do sleep 30; done
F=gold/top10/full
NPROC=12 $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 gold/top10/lean_sf8.py,$F/sf8_c22.py,$F/sf8_c23.py gold/top10/gates/pin249_sf8.jsonl offhand > gold/top10/gates/pin249_sf8.log 2>&1
NPROC=12 $PY gold/harness/pinned4.py moon/strong2800.json,moon/strong_new.json 144 gold/top10/lean_sf8.py,$F/sf8_c22.py,$F/sf8_c23.py gold/top10/gates/s2800_sf8.jsonl offhand > gold/top10/gates/s2800_sf8.log 2>&1
for opp in omw_v15a pub_metav4v13; do
  for c in gold/top10/lean_sf8.py $F/sf8_c23.py $F/sf8_c22.py; do
    n=$(basename $c .py)
    NPROC=12 $PY gold/harness/batch4.py $c arena/cand/$opp.py 6100-6199 gold/top10/gates/cl_${n}_${opp}.jsonl 01 > gold/top10/gates/cl_${n}_${opp}.log 2>&1
  done
done
echo QUEUE1 DONE
