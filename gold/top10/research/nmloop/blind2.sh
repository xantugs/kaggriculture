#!/bin/bash
# blind2.sh CAND TAG : the four new-meta blind replays on fresh seeds 9510-9519 (both seats), sequential per replay
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
C=$1; T=$2; N=gold/top10/research/nmloop; D=gold/top10/research/v33loss; PY=../.venv/Scripts/python.exe
for spec in "115335380 1 RSTurley" "115338309 1 SiyuanWang" "115333932 1 YandG" "115336805 0 pangzi233"; do
  set -- $spec; CAND=$C $PY $D/blind.py $1 $2 $3 $N/b2_${T}_$3.jsonl 9510-9519 > /dev/null 2>&1 &
done
wait
echo "$T blind2 done $(date -u +%H:%M)" >> $N/eval.log
