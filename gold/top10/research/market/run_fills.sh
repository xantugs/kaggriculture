#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
D=gold/top10/research/market
export PYTHONIOENCODING=utf-8 NPROC=2
../.venv/Scripts/python.exe $D/fills_gate.py gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl gold/top10/lean_sf8.py $D/goldg_fills.jsonl > $D/goldg_fills.log 2>&1
../.venv/Scripts/python.exe $D/fills_gate.py gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl gold/top10/lean_sf8.py $D/top10g_fills.jsonl > $D/top10g_fills.log 2>&1
