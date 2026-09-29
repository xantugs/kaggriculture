#!/bin/bash
# cgt_queue.sh : CGt identity checks (reacting smoke seeds 8200-8211 x 12 opponents in two batches of 6, vslive 9000-9039),
# then, once the fresh28 tape runs are complete, CGt on fresh28, CGt on goldg + top10g, and c2tr on fresh28. Memory-bounded.
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands/full_CGt.py; P=../pubnb; G=gold/top10/gates
EG="gold/elite/elite_gate.py run"
B1="gold/submit/main_ctl_T8.py gold/top10/cands/full_v29fc_FW.py arena/cand/omw_v15a.py arena/cand/pub_metav4v13.py arena/cand/pub_smallershock.py $P/x_kaggriculture-limit-breaker-agent.py"
B2="$P/x_kaggriculture-x544-nah-i-d-win.py $P/x_kaggriculture-v01-drip.py $P/x_king-v4e-rc4.py $P/x_titan-kaggriculture-frontier-source.py $P/x_kaggriculture-c07-public-v12-tape.py $P/x_notebooke394244546.py"
i=0; for opp in $B1; do i=$((i+1)); NPROC=1 $PY gold/harness/batch4.py $C $opp 8200-8211 $O/cgt/smoke_$i.jsonl 01 > /dev/null 2>&1 & done; wait
for opp in $B2; do i=$((i+1)); NPROC=1 $PY gold/harness/batch4.py $C $opp 8200-8211 $O/cgt/smoke_$i.jsonl 01 > /dev/null 2>&1 & done; wait
echo "smoke done $(date -u +%H:%M)"
for b in v29fc PFcfc; do NPROC=3 $PY gold/harness/batch4.py $C gold/submit/main_ctl_$b.py 9000-9039 $O/cgt/vs_$b.jsonl 01 > /dev/null 2>&1 & done; wait
echo "vslive done $(date -u +%H:%M)"
until [ "$(wc -l < $O/fresh28/FWt.jsonl)" -ge 851 ] && [ "$(wc -l < $O/fresh28/T8fcWt.jsonl)" -ge 851 ]; do sleep 20; done
sleep 20
NPROC=14 $PY $EG $G/fresh28_games.jsonl.gz $G/fresh28_refs.jsonl $C $O/fresh28/CGt.jsonl > $O/fresh28/CGt.log 2>&1
echo "fresh28 CGt done $(date -u +%H:%M)"
NPROC=6 $PY $EG $G/goldg_games.jsonl.gz $G/goldg_refs.jsonl $C $O/cgt/goldg.jsonl > /dev/null 2>&1 &
NPROC=6 $PY $EG $G/top10g_games.jsonl.gz $G/top10g_refs.jsonl $C $O/cgt/top10g.jsonl > /dev/null 2>&1 &
wait
echo "old elite CGt done $(date -u +%H:%M)"
NPROC=14 $PY $EG $G/fresh28_games.jsonl.gz $G/fresh28_refs.jsonl gold/final/c2tr_final.py $O/fresh28/c2tr.jsonl > $O/fresh28/c2tr.log 2>&1
echo "cgt_queue done $(date -u +%H:%M)"
