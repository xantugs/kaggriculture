#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands; FW=$C/full_v29fc_FW.py; T=$C/full_FWt.py
NPROC=4 $PY gold/harness/batch4.py $T $FW 7200-7239 $O/ft_h2h.jsonl 01 > /dev/null 2>&1 &
NPROC=5 $PY gold/harness/pinned4.py gold/top10/gates/pin249.json 288 $T $O/ft_pin249.jsonl offhand > /dev/null 2>&1 &
NPROC=5 $PY gold/harness/pinned4.py gold/top10/gates/live191.json 288 $T $O/ft_live191.jsonl offhand > /dev/null 2>&1 &
wait
NPROC=4 $PY gold/harness/batch4.py $T arena/cand/omw_v15a.py 6500-6559 $O/ft_omw.jsonl 01 > /dev/null 2>&1 &
NPROC=4 $PY gold/harness/batch4.py $T arena/cand/pub_metav4v13.py 6500-6559 $O/ft_pub.jsonl 01 > /dev/null 2>&1 &
NPROC=4 $PY gold/harness/batch4.py $T arena/cand/pub_smallershock.py 6600-6659 $O/ft_sms.jsonl 01 > /dev/null 2>&1 &
wait
echo "fwt_test done $(date -u +%H:%M)"
