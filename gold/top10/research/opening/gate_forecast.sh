#!/bin/bash
# gate_forecast.sh CAND TAG : out-of-sample gate for Codex's forecast patch (seeds 6500-6539, disjoint from every panel
# used so far), both seats, reacting: vs v29 TP_A31g, vs T8, vs PF, plus the two public agents on 6500-6559; then goldg
# and top10g. Rows land in research/opening/fc_<TAG>_*.jsonl; pair with clpair.py / the elite pairing snippet.
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
C=$1; T=$2; O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe
NPROC=4 $PY gold/harness/batch4.py $C gold/top10/cands/full_TP_A31g.py 6500-6539 $O/fc_${T}_v29.jsonl 01 > $O/fc_${T}_v29.log 2>&1 &
NPROC=4 $PY gold/harness/batch4.py $C gold/submit/main_ctl_T8.py 6500-6539 $O/fc_${T}_T8.jsonl 01 > $O/fc_${T}_T8.log 2>&1 &
NPROC=3 $PY gold/harness/batch4.py $C gold/submit/main_ctl_PF.py 6500-6539 $O/fc_${T}_PF.jsonl 01 > $O/fc_${T}_PF.log 2>&1 &
wait
NPROC=3 $PY gold/harness/batch4.py $C arena/cand/omw_v15a.py 6500-6559 $O/fc_${T}_omw.jsonl 01 > $O/fc_${T}_omw.log 2>&1 &
NPROC=3 $PY gold/harness/batch4.py $C arena/cand/pub_metav4v13.py 6500-6559 $O/fc_${T}_pub.jsonl 01 > $O/fc_${T}_pub.log 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $C $O/fc_${T}_goldg.jsonl > $O/fc_${T}_goldg.log 2>&1 &
NPROC=3 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $C $O/fc_${T}_top10g.jsonl > $O/fc_${T}_top10g.log 2>&1 &
wait
echo "gate $T done"
