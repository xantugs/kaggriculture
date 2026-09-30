#!/bin/bash
# livewatch.sh : every 30 min fetch v34 (CGt) and v35 (NMp44Tr) ladder games -> opening/live_v3435.jsonl; livewatch.py summarises
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
PY=../.venv/Scripts/python.exe; N=gold/top10/research/nmloop
for i in $(seq 1 40); do
  PYTHONPATH=./moon timeout 1500 $PY gold/top10/tools/livefetch.py gold/top10/research/opening/live_v3435.jsonl 56697382,56697385 v34,v35 > /dev/null 2>&1
  $PY $N/livewatch.py >> $N/livewatch.log 2>&1
  sleep 1800
done
