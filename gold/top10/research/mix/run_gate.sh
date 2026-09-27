#!/bin/bash
# sf8 vs repaired elites (wheat_diag cand mode) on the gate seats not covered by the earlier diag runs, then resume corpora
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8 NPROC=2
O=gold/top10/research/mix/out
../.venv/Scripts/python.exe gold/top10/tools/wheat_diag.py cand gold/top10/gates/goldg_games.jsonl.gz $O/goldg_rest_refs.jsonl gold/top10/lean_sf8.py $O/gdiag_goldg_rest.jsonl
../.venv/Scripts/python.exe gold/top10/tools/wheat_diag.py cand gold/top10/gates/top10g_games.jsonl.gz $O/top10g_rest_refs.jsonl gold/top10/lean_sf8.py $O/gdiag_top10g_rest.jsonl
for D in 25 26; do
  ../.venv/Scripts/python.exe gold/top10/research/mix/corpus_diag.py ../kaggriculture/moon/elite/games_2026-09-$D.jsonl $O/diag_$D.jsonl
done
echo ALLDONE
