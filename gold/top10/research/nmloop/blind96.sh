#!/bin/bash
# blind96.sh CAND TAG : the 4 new-meta blind replays on NEW seeds 9600-9619 (both seats) -> nmloop/b96_TAG_LABEL.jsonl
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
C=$1; T=$2; N=gold/top10/research/nmloop; D=gold/top10/research/v33loss; PY=../.venv/Scripts/python.exe
for spec in "115335380 1 RSTurley" "115338309 1 SiyuanWang" "115333932 1 YandG" "115336805 0 pangzi233"; do
  set -- $spec; CAND=$C $PY $D/blind.py $1 $2 $3 $N/b96_${T}_$3.jsonl 9600-9619 > /dev/null 2>&1 &
done
wait
echo "$T b96 done $(date -u +%H:%M)" >> $N/eval.log
