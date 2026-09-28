#!/bin/bash
# endgame probes on T5 (resumed session): wait for the top10g90 T5 day ledger, then late_keep and day-27 wheat on the
# 52 close goldg seats (|m| < 5000 under T5), one run at a time, NPROC=2
SP=/c/Users/khant/AppData/Local/Temp/claude/C--Users-khant-OneDrive-Documents-ChatGPT-2027-kaggriculture-review/875e1517-4223-4d24-a8c6-423a3c7003a6/scratchpad
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
until grep -q '^done' $SP/eg_dl_t10_T5.log; do sleep 30; done
C=gold/top10/research/endgame/cands
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=2
for v in lk w27; do
  $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz $SP/eg_goldg_close_refs.jsonl $C/eg_T5_$v.py $SP/eg_pr_$v.jsonl > $SP/eg_pr_$v.log 2>&1
done
echo alldone > $SP/eg_queue2_done.txt
