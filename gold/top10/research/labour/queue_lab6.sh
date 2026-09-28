#!/bin/bash
# after the live keep5 run: keep5G goldg -> keep5G live191 -> T5 hirelog top10g90 -> keep5G top10g90 -> keep5 top10g90
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
L=gold/top10/research/labour
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=2
until grep -q "T5_keep5.py:" $L/live_T5_keep5.log 2>/dev/null; do sleep 15; done
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $L/T5_keep5G.py $L/goldg_T5_keep5G.jsonl > $L/goldg_T5_keep5G.log 2>&1
$PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $L/T5_keep5G.py $L/live_T5_keep5G.jsonl offhand > $L/live_T5_keep5G.log 2>&1
$PY $L/hirelog_run.py gold/top10/gates/top10g_games.jsonl.gz $L/t10_90_refs.jsonl $L/T5_hirelog.py $L/t10_T5_hl.jsonl $L/t10_90_sel.txt > $L/t10_T5_hl.log 2>&1
$PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz $L/t10_90_refs.jsonl $L/T5_keep5G.py $L/t10_T5_keep5G.jsonl > $L/t10_T5_keep5G.log 2>&1
$PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz $L/t10_90_refs.jsonl $L/T5_keep5.py $L/t10_T5_keep5.jsonl > $L/t10_T5_keep5.log 2>&1
echo alldone > $L/queue_lab6_done.txt
