#!/bin/bash
# labour-lens probes, one run at a time (NPROC=2), after the T5 hirelog run
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
L=gold/top10/research/labour
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 NPROC=2
until [ $(wc -l < $L/goldg_T5_hl.jsonl) -ge 111 ]; do sleep 20; done
sleep 5
for v in keep5 ovf0; do
  $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $L/T5_$v.py $L/goldg_T5_$v.jsonl > $L/goldg_T5_$v.log 2>&1
done
echo alldone > $L/queue_lab_done.txt
