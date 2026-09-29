#!/bin/bash
# controller-slot tests with the wool forecast (run after the late screen)
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
NPROC=2 $PY gold/harness/batch4.py $C/full_T8fcW.py $C/full_T8fc.py 6700-6719 $O/ct_T8fcW_T8fc_a.jsonl 0 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C/full_T8fcW.py $C/full_T8fc.py 6720-6739 $O/ct_T8fcW_T8fc_b.jsonl 1 > /dev/null 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_PFhW.py $O/ct_PFhW_goldg.jsonl > /dev/null 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_OP_PFhW.py $O/ct_PFhW_top10g.jsonl > /dev/null 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_PFcfcW.py $O/ct_PFcfcW_goldg.jsonl > /dev/null 2>&1 &
wait
echo "ctl tests done $(date -u +%H:%M)"
