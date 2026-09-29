#!/bin/bash
# g_test.sh : Codex's three immediate candidates (A mid_melon, B straw_gate, C access_free_last 3/6) vs the base
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
for v in gA gB gC3 gC6; do
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_${v}p.py $C/full_T8fcW.py 7000-7039 $O/g_${v}_T8W.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_${v}p.py $C/full_v29fc_FW.py 7000-7039 $O/g_${v}_FW.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "reacting done $(date -u +%H:%M)"
for v in gA gB gC6; do
  NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_${v}r.py $O/g_${v}_goldg.jsonl > /dev/null 2>&1 &
done
wait
for v in gA gB gC6; do
  NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_OP_${v}r.py $O/g_${v}_top10g.jsonl > /dev/null 2>&1 &
done
wait
echo "g_test done $(date -u +%H:%M)"
