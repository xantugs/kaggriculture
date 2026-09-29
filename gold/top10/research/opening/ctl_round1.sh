#!/bin/bash
# ctl_round1.sh : tape pick (FW vs T8fcW head to head) + controller strawberry variants
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
NPROC=3 $PY gold/harness/batch4.py $C/full_v29fc_FW.py $C/full_T8fcW.py 6900-6939 $O/pick_FW_T8W.jsonl 01 > /dev/null 2>&1 &
# pure controller vs the tape (reacting): base and the 8 strawberry variants, 40 seeds both seats
for v in c0 cL1 cL2 cS1 cS2 cS3 cS4; do
  NPROC=2 $PY gold/harness/batch4.py $C/full_OP_${v}p.py $C/full_T8fcW.py 7000-7039 $O/r1_${v}p.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "round1 self-play done $(date -u +%H:%M)"
# elite gates for the routed versions (the controller plays herd-type elites there)
for v in c0 cS1 cS2 cS3 cS4; do
  NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C/full_OP_${v}r.py $O/r1_${v}r_goldg.jsonl > /dev/null 2>&1 &
done
wait
for v in c0 cS1 cS2 cS3 cS4; do
  NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C/full_OP_${v}r.py $O/r1_${v}r_top10g.jsonl > /dev/null 2>&1 &
done
wait
echo "round1 done $(date -u +%H:%M)"
