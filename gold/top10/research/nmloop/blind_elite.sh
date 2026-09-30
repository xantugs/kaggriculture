#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
N=gold/top10/research/nmloop; PY=../.venv/Scripts/python.exe
$PY -c "import json; [print(g, s, t.replace(' ', '_')[:10]) for t, g, s in json.load(open('$N/blind_elite_pick.json'))]" | while read g s t; do
  CAND=gold/final/CGt_final.py $PY $N/blind_elite.py $g $s ${t}_$g $N/be_${t}_$g.jsonl 9700-9709 > /dev/null 2>&1 &
done
wait
echo "blind_elite done $(date -u +%H:%M)" >> $N/eval.log
