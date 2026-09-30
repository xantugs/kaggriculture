#!/bin/bash
# sentinel.sh : every 45 min fetch new live v33 games and replay them with CGt / c2tr / NMp44Tr (sentinel.py -> sentinel.log)
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
PY=../.venv/Scripts/python.exe; N=gold/top10/research/nmloop
for i in $(seq 1 16); do
  PYTHONPATH=./moon timeout 1500 $PY gold/top10/tools/livefetch.py gold/top10/research/opening/live_v33.jsonl 56681632 v33 > /dev/null 2>&1
  timeout 2400 $PY $N/sentinel.py >> $N/sentinel.out 2>&1
  sleep 2700
done
