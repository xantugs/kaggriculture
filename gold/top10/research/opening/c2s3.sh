#!/bin/bash
# c2s3.sh CAND TAG : the 24-seat C2S3 elite subset (goldg + top10g refs) through the elite gate runner
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
NPROC=${NPROC:-3} ../.venv/Scripts/python.exe gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $O/refs_c2s3_goldg.jsonl "$1" $O/eg_$2_c2s3g.jsonl 2>&1 | grep -v Loading | tail -5
NPROC=${NPROC:-3} ../.venv/Scripts/python.exe gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz $O/refs_c2s3_top10g.jsonl "$1" $O/eg_$2_c2s3t.jsonl 2>&1 | grep -v Loading | tail -5
