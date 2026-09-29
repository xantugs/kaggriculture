#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
../.venv/Scripts/python.exe -u $O/eval_batch.py $O/cfg_p1e.json $O/batch_q3.json 3 > $O/eval_batch_q3.log 2>&1; echo done >> $O/eval_batch_q3.log
../.venv/Scripts/python.exe -u $O/eval_batch.py $O/cfg_p1e.json $O/batch_q2.json 3 > $O/eval_batch_q2.log 2>&1; echo done >> $O/eval_batch_q2.log
