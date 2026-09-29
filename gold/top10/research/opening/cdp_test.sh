#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands; FW=$C/full_v29fc_FW.py
for v in cdp12 cdp8; do
  NPROC=3 $PY gold/harness/batch4.py $C/full_FW$v.py $FW 7200-7239 $O/cd_${v}_h2h.jsonl 01 > /dev/null 2>&1 &
done
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 $C/full_FWcdp12.py,$C/full_FWcdp8.py $O/cd_pin249.jsonl offhand > /dev/null 2>&1 &
NPROC=4 $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $C/full_FWcdp12.py,$C/full_FWcdp8.py $O/cd_live191.jsonl offhand > /dev/null 2>&1 &
wait
echo "stage1 $(date -u +%H:%M)"
for v in cdp12 cdp8; do
  NPROC=2 $PY gold/harness/batch4.py $C/full_FW$v.py arena/cand/omw_v15a.py 6500-6559 $O/cd_${v}_omw.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $C/full_FW$v.py arena/cand/pub_metav4v13.py 6500-6559 $O/cd_${v}_pub.jsonl 01 > /dev/null 2>&1 &
  NPROC=2 $PY gold/harness/batch4.py $C/full_FW$v.py arena/cand/pub_smallershock.py 6600-6659 $O/cd_${v}_sms.jsonl 01 > /dev/null 2>&1 &
done
wait
echo "cdp_test done $(date -u +%H:%M)"
