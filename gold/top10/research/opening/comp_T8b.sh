#!/bin/bash
# comp_T8b.sh : the two honest candidates (FW = wool tape, T8fcW = T8 + wool forecast) vs plain T8 on identical games
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands; T8=gold/submit/main_ctl_T8.py
FW=$C/full_v29fc_FW.py; T8W=$C/full_T8fcW.py
NPROC=3 $PY gold/harness/batch4.py $FW $T8 6900-6939 $O/cmp_FW_T8.jsonl 01 > /dev/null 2>&1 &
NPROC=3 $PY gold/harness/batch4.py $T8W $T8 6900-6939 $O/cmp_T8W_T8.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $T8W arena/cand/omw_v15a.py 6500-6559 $O/cmp_T8W_omw_v15a.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $T8W arena/cand/pub_metav4v13.py 6500-6559 $O/cmp_T8W_pub_metav4v13.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $T8W arena/cand/pub_smallershock.py 6600-6659 $O/cmp_T8W_sms.jsonl 01 > /dev/null 2>&1 &
wait
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 $T8W $O/cmp_T8W_pin249.jsonl offhand > /dev/null 2>&1 &
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $T8W $O/cmp_T8W_live191.jsonl offhand > /dev/null 2>&1 &
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $T8W $O/cmp_T8W_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $T8W $O/cmp_T8W_top10g.jsonl > /dev/null 2>&1 &
wait
echo "comp_T8b done $(date -u +%H:%M)"
