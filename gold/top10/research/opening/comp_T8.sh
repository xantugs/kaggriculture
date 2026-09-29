#!/bin/bash
# comp_T8.sh : both final tapes vs plain T8 on identical games
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands; T8=gold/submit/main_ctl_T8.py
FWS=$C/full_FWS.py; T8S=$C/full_T8fcWS.py
# head to head, both seats, fresh seeds 6900-6939
NPROC=3 $PY gold/harness/batch4.py $FWS $T8 6900-6939 $O/cmp_FWS_T8.jsonl 01 > /dev/null 2>&1 &
NPROC=3 $PY gold/harness/batch4.py $T8S $T8 6900-6939 $O/cmp_T8S_T8.jsonl 01 > /dev/null 2>&1 &
# T8 and T8fcWS vs the public agents on the towns the other candidates already played
for opp in omw_v15a pub_metav4v13; do
  NPROC=2 $PY gold/harness/batch4.py $T8 arena/cand/$opp.py 6500-6559 $O/cmp_T8_$opp.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $T8S arena/cand/$opp.py 6500-6559 $O/cmp_T8S_$opp.jsonl 01 > /dev/null 2>&1 &
done
wait
NPROC=2 $PY gold/harness/batch4.py $T8 arena/cand/pub_smallershock.py 6600-6659 $O/cmp_T8_sms.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $T8S arena/cand/pub_smallershock.py 6600-6659 $O/cmp_T8S_sms.jsonl 01 > /dev/null 2>&1 &
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 $T8S $O/cmp_T8S_pin249.jsonl offhand > /dev/null 2>&1 &
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $T8S $O/cmp_T8S_live191.jsonl offhand > /dev/null 2>&1 &
wait
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $T8 $O/cmp_T8_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $T8 $O/cmp_T8_top10g.jsonl > /dev/null 2>&1 &
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $T8S $O/cmp_T8S_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $T8S $O/cmp_T8S_top10g.jsonl > /dev/null 2>&1 &
wait
echo "comp_T8 done $(date -u +%H:%M)"
