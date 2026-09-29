#!/bin/bash
# gate_final.sh : full gates for the two finalists T8fc (T8 + forecast) and PFcfc (PFc + forecast)
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
T8FC=$C/full_T8fc.py; PFCFC=$C/full_OP_PFcfc.py
NPROC=3 $PY gold/harness/batch4.py $T8FC $C/full_FC_phase.py 6500-6539 $O/fin_T8fc_FC.jsonl 01 > $O/fin_T8fc_FC.log 2>&1 &
NPROC=3 $PY gold/harness/batch4.py $PFCFC $T8FC 6500-6539 $O/fin_PFcfc_T8fc.jsonl 01 > $O/fin_PFcfc_T8fc.log 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $T8FC arena/cand/omw_v15a.py 6500-6559 $O/fin_T8fc_omw.jsonl 01 > $O/fin_T8fc_omw.log 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $T8FC arena/cand/pub_metav4v13.py 6500-6559 $O/fin_T8fc_pub.jsonl 01 > $O/fin_T8fc_pub.log 2>&1 &
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 gold/submit/main_ctl_T8.py,$T8FC $O/fin_pin249_T8_T8fc.jsonl offhand > $O/fin_pin249.log 2>&1 &
wait
echo "stage 1 done $(date -u +%H:%M)"
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $T8FC $O/fin_T8fc_goldg.jsonl > $O/fin_T8fc_goldg.log 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $T8FC $O/fin_T8fc_top10g.jsonl > $O/fin_T8fc_top10g.log 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $PFCFC $O/fin_PFcfc_goldg.jsonl > $O/fin_PFcfc_goldg.log 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $PFCFC $O/fin_PFcfc_top10g.jsonl > $O/fin_PFcfc_top10g.log 2>&1 &
NPROC=3 $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 gold/submit/main_ctl_T8.py,$T8FC $O/fin_live191_T8_T8fc.jsonl offhand > $O/fin_live191.log 2>&1 &
wait
echo "gate_final done $(date -u +%H:%M)"
