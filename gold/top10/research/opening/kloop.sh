#!/bin/bash
# kloop.sh : keep my Kaggle queue alive (kqueue exits after each finished kernel)
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
O=gold/top10/research/opening
while true; do
  ../.venv/Scripts/python.exe gold/top10/kaggle/kqueue.py $O/kstate.json 120 >> $O/kq.log 2>&1
  if ! grep -q '"running": \[\]' $O/kstate.json || [ -s $O/kinbox.txt ]; then sleep 60; else sleep 120; fi
done
