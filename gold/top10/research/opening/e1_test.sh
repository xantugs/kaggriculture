#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
for v in e1a e1b e1c; do
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_T8fcW.py 7000-7039 $O/e_${v}_T8W.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_v29fc_FW.py 7000-7039 $O/e_${v}_FW.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "e1 reacting done $(date -u +%H:%M)"
