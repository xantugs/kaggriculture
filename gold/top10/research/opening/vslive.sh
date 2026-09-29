#!/bin/bash
# vslive.sh : final candidates head to head vs the live pair (v31 = v29fc, v32 = PFcfc), fresh seeds 9000-9039, both seats
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; F=gold/final; S=gold/submit
for a in FWt T8fcWt c2tr; do
  for b in v29fc PFcfc; do
    NPROC=3 $PY gold/harness/batch4.py $F/${a}_final.py $S/main_ctl_$b.py 9000-9039 $O/vslive/${a}_vs_$b.jsonl 01 > /dev/null 2>&1 &
  done
done
wait
echo "vslive done $(date -u +%H:%M)"
