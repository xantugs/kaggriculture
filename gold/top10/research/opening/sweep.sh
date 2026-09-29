#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
for N in 6 8 10 12 14; do
  NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/hf60_refs.jsonl $C/full_OP_h${N}r.py $O/sw_h${N}r_hf60.jsonl > /dev/null 2>&1 &
done
wait
echo "sweep elite done $(date -u +%H:%M)"
for N in 6 8 10 12 14; do
  NPROC=1 $PY gold/harness/batch4.py $C/full_OP_h${N}.py ../pubnb/x_kaggriculture-v01-drip.py 7500-7519 $O/sw_h${N}_drip.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "sweep done $(date -u +%H:%M)"
