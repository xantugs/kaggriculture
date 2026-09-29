#!/bin/bash
# final_gates.sh : tape FWt elite gates; controller with the full forecast (c0tr / c2tr / c0tp). At most ~16 python processes.
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
EG="gold/elite/elite_gate.py run"
NPROC=4 $PY $EG gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_FWt.py $O/fg_FWt_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY $EG gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_FWt.py $O/fg_FWt_top10g.jsonl > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C/full_OP_c0tp.py $C/full_T8fcW.py 7000-7039 $O/fg_c0tp_T8W.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C/full_OP_c0tp.py $C/full_v29fc_FW.py 7000-7039 $O/fg_c0tp_FW.jsonl 01 > /dev/null 2>&1 &
wait
echo "stage A done $(date -u +%H:%M)"
NPROC=4 $PY $EG gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_c2tr.py $O/fg_c2tr_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY $EG gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_OP_c0tr.py $O/fg_c0tr_top10g.jsonl > /dev/null 2>&1 &
NPROC=4 $PY $EG gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_OP_c2tr.py $O/fg_c2tr_top10g.jsonl > /dev/null 2>&1 &
wait
echo "final_gates done $(date -u +%H:%M)"
