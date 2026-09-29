#!/bin/bash
# cgt_ident.sh : CGt on the exact seeds of the FWt/T8fcWt preflight smoke (8200-8211, 12 opponents) and vslive (9000-9039)
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands/full_CGt.py; P=../pubnb
OPPS="gold/submit/main_ctl_T8.py gold/top10/cands/full_v29fc_FW.py arena/cand/omw_v15a.py arena/cand/pub_metav4v13.py arena/cand/pub_smallershock.py $P/x_kaggriculture-limit-breaker-agent.py $P/x_kaggriculture-x544-nah-i-d-win.py $P/x_kaggriculture-v01-drip.py $P/x_king-v4e-rc4.py $P/x_titan-kaggriculture-frontier-source.py $P/x_kaggriculture-c07-public-v12-tape.py $P/x_notebooke394244546.py"
i=0
for opp in $OPPS; do
  i=$((i+1))
  NPROC=1 $PY gold/harness/batch4.py $C $opp 8200-8211 $O/cgt/smoke_$i.jsonl 01 > /dev/null 2>&1 &
done
for b in v29fc PFcfc; do
  NPROC=2 $PY gold/harness/batch4.py $C gold/submit/main_ctl_$b.py 9000-9039 $O/cgt/vs_$b.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "cgt ident done $(date -u +%H:%M)"
