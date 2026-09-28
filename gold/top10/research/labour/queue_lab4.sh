#!/bin/bash
# labour probes, one run at a time (NPROC=2): after the live hirelog -> keep5 on live191 -> T5 hirelog top10g90 -> keep5 top10g90 -> ovf0 goldg
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
L=gold/top10/research/labour
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=2
until grep -q "^done" $L/live_T5_hl8.log 2>/dev/null; do sleep 15; done
$PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $L/T5_keep5.py $L/live_T5_keep5.jsonl offhand > $L/live_T5_keep5.log 2>&1
$PY $L/hirelog_run.py gold/top10/gates/top10g_games.jsonl.gz $L/t10_90_refs.jsonl $L/T5_hirelog.py $L/t10_T5_hl.jsonl $L/t10_90_sel.txt > $L/t10_T5_hl.log 2>&1
$PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz $L/t10_90_refs.jsonl $L/T5_keep5.py $L/t10_T5_keep5.jsonl > $L/t10_T5_keep5.log 2>&1
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $L/T5_ovf0.py $L/goldg_T5_ovf0.jsonl > $L/goldg_T5_ovf0.log 2>&1
echo alldone > $L/queue_lab4_done.txt
