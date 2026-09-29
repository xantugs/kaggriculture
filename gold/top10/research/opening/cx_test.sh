#!/bin/bash
# cx_test.sh : Codex's recovered controller leads vs our base, reacting then elite
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
for v in c0p CX_courier1p CX_fund1p CX_alloc1p; do
  f=$C/full_OP_$v.py; [ -f $f ] || f=$C/full_$v.py
  NPROC=2 $PY gold/harness/batch4.py $f $C/full_T8fcW.py 7000-7039 $O/cx_${v}_T8W.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $f $C/full_v29fc_FW.py 7000-7039 $O/cx_${v}_FW.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "reacting done $(date -u +%H:%M)"
for v in CX_courier1r CX_fund1r CX_alloc1r; do
  NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_$v.py $O/cx_${v}_goldg.jsonl > /dev/null 2>&1 &
done
wait
for v in CX_courier1r CX_fund1r CX_alloc1r; do
  NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_$v.py $O/cx_${v}_top10g.jsonl > /dev/null 2>&1 &
done
wait
echo "cx_test done $(date -u +%H:%M)"
