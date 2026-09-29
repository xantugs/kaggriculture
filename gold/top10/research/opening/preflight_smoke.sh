#!/bin/bash
# preflight smoke: each final file vs a wide opponent mix, 12 seeds x both seats per opponent (crashes, errors, max step time)
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; S=gold/submit; P=../pubnb
OPPS="gold/submit/main_ctl_T8.py gold/top10/cands/full_v29fc_FW.py arena/cand/omw_v15a.py arena/cand/pub_metav4v13.py arena/cand/pub_smallershock.py $P/x_kaggriculture-limit-breaker-agent.py $P/x_kaggriculture-x544-nah-i-d-win.py $P/x_kaggriculture-v01-drip.py $P/x_king-v4e-rc4.py $P/x_titan-kaggriculture-frontier-source.py $P/x_kaggriculture-c07-public-v12-tape.py $P/x_notebooke394244546.py"
mkdir -p $O/preflight
for f in main_ctl_FWt main_ctl_T8fcWt main_ctl_c2tr; do
  i=0
  for opp in $OPPS; do
    i=$((i+1))
    NPROC=1 $PY gold/harness/batch4.py $S/$f.py $opp 8200-8211 $O/preflight/${f}_$i.jsonl 01 > /dev/null 2>&1 &
  done
  wait
  echo "$f smoke done $(date -u +%H:%M)"
done
echo "preflight smoke done"
