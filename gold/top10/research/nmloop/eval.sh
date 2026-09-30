#!/bin/bash
# eval.sh CAND TAG : ladder mini-gate (9 real v33 games), blind panels (4 new-meta replays x 20 fresh towns) and fresh960
# (420 new-meta elite seats of the 27-28 Sep datasets) for one candidate; rows in nmloop/, then "TAG done" in nmloop/eval.log
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
C=$1; T=$2; N=gold/top10/research/nmloop; D=gold/top10/research/v33loss; PY=../.venv/Scripts/python.exe; G=gold/top10/gates
$PY $D/ladder_gate.py run $C $N/lg_$T.jsonl > /dev/null 2>&1 &
for spec in "115335380 1 RSTurley" "115338309 1 SiyuanWang" "115333932 1 YandG" "115336805 0 pangzi233"; do
  set -- $spec; CAND=$C $PY $D/blind.py $1 $2 $3 $N/bl_${T}_$3.jsonl 9500-9519 > /dev/null 2>&1 &
done
NPROC=8 $PY gold/elite/elite_gate.py run $G/fresh960_games.jsonl.gz $G/fresh960_refs.jsonl $C $N/f960_$T.jsonl > /dev/null 2>&1 &
wait
echo "$T done $(date -u +%H:%M)" >> $N/eval.log
