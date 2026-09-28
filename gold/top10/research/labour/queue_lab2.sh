#!/bin/bash
# labour-lens probes, one run at a time (NPROC=2): wait for keep5 on goldg, then live hirelog on the high-wage games, then ovf0
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
L=gold/top10/research/labour
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=2
until grep -q "T5_keep5.py:" $L/goldg_T5_keep5.log 2>/dev/null; do sleep 20; done
$PY $L/live_hl.py gold/top10/gates/live191.json 288 $L/T5_hirelog.py $L/live_T5_hl8.jsonl 113620813,113633403,113752335,113696377,113662619,113676198,113702310,113624741 > $L/live_T5_hl8.log 2>&1
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $L/T5_ovf0.py $L/goldg_T5_ovf0.jsonl > $L/goldg_T5_ovf0.log 2>&1
echo alldone > $L/queue_lab2_done.txt
