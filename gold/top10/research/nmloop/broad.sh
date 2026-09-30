#!/bin/bash
# broad.sh CAND TAG : old elite gates goldg (111) + top10g (270) for a candidate -> nmloop/og_TAG_{goldg,top10g}.jsonl
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
C=$1; T=$2; N=gold/top10/research/nmloop; G=gold/top10/gates; PY=../.venv/Scripts/python.exe
NPROC=6 $PY gold/elite/elite_gate.py run $G/goldg_games.jsonl.gz $G/goldg_refs.jsonl $C $N/og_${T}_goldg.jsonl > /dev/null 2>&1 &
NPROC=6 $PY gold/elite/elite_gate.py run $G/top10g_games.jsonl.gz $G/top10g_refs.jsonl $C $N/og_${T}_top10g.jsonl > /dev/null 2>&1 &
wait
echo "$T broad done $(date -u +%H:%M)" >> $N/eval.log
