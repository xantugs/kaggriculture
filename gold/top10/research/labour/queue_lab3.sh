#!/bin/bash
# after queue_lab2: T5 hirelog baseline on the 90 top10g seats (g_wheat's t10_90 set)
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
L=gold/top10/research/labour
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=2
until [ -f $L/queue_lab2_done.txt ]; do sleep 20; done
$PY $L/hirelog_run.py gold/top10/gates/top10g_games.jsonl.gz $L/t10_90_refs.jsonl $L/T5_hirelog.py $L/t10_T5_hl.jsonl $L/t10_90_sel.txt > $L/t10_T5_hl.log 2>&1
echo alldone > $L/queue_lab3_done.txt
