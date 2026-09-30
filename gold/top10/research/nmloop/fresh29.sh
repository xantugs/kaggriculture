#!/bin/bash
# fresh29.sh : wait for Kaggle's 2026-09-29 top-team dataset, fetch it, build the fresh29 elite gate (top-45 teams, cap 80),
# then run the tape (CGt) and the frozen NMp13 on it (held-out validation of the new-meta branch). Progress in nmloop/fresh29.log
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
PY=../.venv/Scripts/python.exe; N=gold/top10/research/nmloop; G=gold/top10/gates
for i in $(seq 1 60); do
  $PY moon/elite_fetch.py list 2026-09-29 2026-09-29 > $N/fresh29_list.out 2>&1
  n=$(cat moon/elite/ids_2026-09-29.txt 2>/dev/null | wc -w)
  echo "$(date -u +%H:%M) list try $i: $n ids" >> $N/fresh29.log
  [ "$n" -gt 100 ] && break
  sleep 600
done
$PY moon/elite_fetch.py fetch 2026-09-29 6 >> $N/fresh29.log 2>&1
echo "$(date -u +%H:%M) fetched $(wc -l < moon/elite/games_2026-09-29.jsonl) games" >> $N/fresh29.log
NPROC=10 $PY gold/top10/tools/fresh_gate_build.py fresh29 2026-09-29 45 80 >> $N/fresh29.log 2>&1
echo "$(date -u +%H:%M) gate built" >> $N/fresh29.log
NPROC=12 $PY gold/elite/elite_gate.py run $G/fresh29_games.jsonl.gz $G/fresh29_refs.jsonl gold/final/CGt_final.py $N/f29_TAPE.jsonl > /dev/null 2>&1
echo "$(date -u +%H:%M) tape done" >> $N/fresh29.log
NPROC=12 $PY gold/elite/elite_gate.py run $G/fresh29_games.jsonl.gz $G/fresh29_refs.jsonl gold/top10/cands/full_NMp13.py $N/f29_NMp13.jsonl > /dev/null 2>&1
echo "$(date -u +%H:%M) NMp13 done" >> $N/fresh29.log
