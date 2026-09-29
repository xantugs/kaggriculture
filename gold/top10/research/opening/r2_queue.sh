#!/bin/bash
# round-2 queue (ChatGPT round-1 reply): c2_E1b gate, F1 fresh panels, F1 herd panel, F1 goldg
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands; EG="gold/elite/elite_gate.py run"
DRIP=../pubnb/x_kaggriculture-v01-drip.py
# wave 1
NPROC=4 $PY $EG gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_OP_e1b2r.py $O/r2_e1b2r_top10g.jsonl > /dev/null 2>&1 &
for v in c0tp e1b; do NPROC=1 $PY gold/harness/batch4.py $C/full_OP_$v.py $DRIP 7500-7519 $O/r2_${v}_drip.jsonl 01 > /dev/null 2>&1 & done
for v in c0tp e1b f1; do NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_T8fcW.py 7900-7939 $O/r2_${v}_T8W.jsonl 01 > /dev/null 2>&1 & done
wait
echo "wave 1 done $(date -u +%H:%M)"
# wave 2
for v in c0tp e1b f1; do NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_v29fc_FW.py 7900-7939 $O/r2_${v}_FW.jsonl 01 > /dev/null 2>&1 & done
$PY $O/herd_panel2.py f1=$C/full_OP_f1.py > $O/herd_panel_f1.log 2>&1 &
wait
echo "wave 2 done $(date -u +%H:%M)"
# wave 3
NPROC=6 $PY $EG gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_f1r.py $O/r2_f1r_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY $EG gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_e1b2r.py $O/r2_e1b2r_goldg.jsonl > /dev/null 2>&1 &
wait
echo "r2 queue done $(date -u +%H:%M)"
