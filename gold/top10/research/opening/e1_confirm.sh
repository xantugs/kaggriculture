#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands; EG="gold/elite/elite_gate.py run"
# fresh towns 7700-7739, both seats: base and e1b vs both tapes
for v in c0tp e1b; do
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_T8fcW.py 7700-7739 $O/ef_${v}_T8W.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_$v.py $C/full_v29fc_FW.py 7700-7739 $O/ef_${v}_FW.jsonl 01 > /dev/null 2>&1 &
done
NPROC=3 $PY $EG gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_e1br.py $O/ef_e1br_goldg.jsonl > /dev/null 2>&1 &
wait
echo "stage 1 done $(date -u +%H:%M)"
NPROC=4 $PY $EG gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_OP_e1br.py $O/ef_e1br_top10g.jsonl > /dev/null 2>&1 &
$PY $O/herd_panel2.py e1b=$C/full_OP_e1b.py > $O/herd_panel_e1b.log 2>&1 &
wait
echo "e1_confirm done $(date -u +%H:%M)"
