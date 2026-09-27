#!/bin/bash
# replay the 23-26 Sep daily corpora (NPROC=2), one after the other
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
for D in 23 24 25 26; do
  PYTHONIOENCODING=utf-8 NPROC=2 ../.venv/Scripts/python.exe gold/top10/research/mix/corpus_diag.py \
    ../kaggriculture/moon/elite/games_2026-09-$D.jsonl gold/top10/research/mix/out/diag_$D.jsonl
done
echo ALLDONE
