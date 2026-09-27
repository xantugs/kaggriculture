#!/bin/bash
# endgame probes, one run at a time (NPROC=2), after the top10g day ledger run
SP=/c/Users/khant/AppData/Local/Temp/claude/C--Users-khant-OneDrive-Documents-ChatGPT-2027-kaggriculture-review/875e1517-4223-4d24-a8c6-423a3c7003a6/scratchpad
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
until [ $(grep -c '^done' $SP/dl.log) -ge 2 ]; do sleep 30; done
C=gold/top10/research/endgame/cands
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=2
$PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $SP/goldg_refs_five.jsonl $C/eg_base.py $SP/pr_base5.jsonl > $SP/pr_base5.log 2>&1
for v in h12 a2 a1 h13 fbv; do
  $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $SP/goldg_refs_third.jsonl $C/eg_$v.py $SP/pr_$v.jsonl > $SP/pr_$v.log 2>&1
done
$PY gold/top10/research/endgame/replay_days.py $SP/rd_live.jsonl offhand $(cat $SP/rd_files.txt) > $SP/rd.log 2>&1
echo alldone > $SP/queue_done.txt
