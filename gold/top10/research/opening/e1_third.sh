#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
until grep -q "e2 reacting done" $O/e2_test.log 2>/dev/null; do sleep 20; done
for v in c0tp e1b e1a; do
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_T8fcW.py 7800-7839 $O/eg_${v}_T8W.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_v29fc_FW.py 7800-7839 $O/eg_${v}_FW.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "e1 third set done $(date -u +%H:%M)"
