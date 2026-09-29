#!/bin/bash
# confirm.sh CAND TAG BASE : confirmation gates for a tape candidate against its base (both seats, new seeds), the public
# agents, the day-12 pinned gates (base and cand paired in one run) and both elite gates. Rows: research/opening/cf_<TAG>_*.
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
C=$1; T=$2; B=$3; O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe
NPROC=4 $PY gold/harness/batch4.py $C $B 6800-6839 $O/cf_${T}_h2h.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C arena/cand/omw_v15a.py 6500-6559 $O/cf_${T}_omw.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C arena/cand/pub_metav4v13.py 6500-6559 $O/cf_${T}_pub.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C arena/cand/pub_smallershock.py 6600-6659 $O/cf_${T}_sms.jsonl 01 > /dev/null 2>&1 &
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 $B,$C $O/cf_${T}_pin249.jsonl offhand > /dev/null 2>&1 &
wait
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $B,$C $O/cf_${T}_live191.jsonl offhand > /dev/null 2>&1 &
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C $O/cf_${T}_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C $O/cf_${T}_top10g.jsonl > /dev/null 2>&1 &
wait
echo "confirm $T done $(date -u +%H:%M)"
