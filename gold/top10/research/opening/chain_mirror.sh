#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
../.venv/Scripts/python.exe $O/mirror_test.py whole $O/mirror_whole.jsonl 3 > $O/mirror_whole.log 2>&1
../.venv/Scripts/python.exe $O/mirror_test.py d16 $O/mirror_d16.jsonl 3 > $O/mirror_d16.log 2>&1
echo CHAIN_DONE >> $O/mirror_d16.log
