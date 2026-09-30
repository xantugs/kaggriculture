#!/bin/bash
# quick.sh CAND TAG : ladder mini-gate + blind panels only (no fresh960); "TAG quick done" in nmloop/eval.log
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
C=$1; T=$2; N=gold/top10/research/nmloop; D=gold/top10/research/v33loss; PY=../.venv/Scripts/python.exe
$PY $D/ladder_gate.py run $C $N/lg_$T.jsonl > /dev/null 2>&1 &
for spec in "115335380 1 RSTurley" "115338309 1 SiyuanWang" "115333932 1 YandG" "115336805 0 pangzi233"; do
  set -- $spec; CAND=$C $PY $D/blind.py $1 $2 $3 $N/bl_${T}_$3.jsonl 9500-9519 > /dev/null 2>&1 &
done
wait
echo "$T quick done $(date -u +%H:%M)" >> $N/eval.log
