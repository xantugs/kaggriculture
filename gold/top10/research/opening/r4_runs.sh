#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; C=gold/top10/cands
NPROC=4 $PY gold/elite/elite_gate.py run gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/hf60_refs.jsonl $C/full_T8fcWt.py $O/r4_T8fcWt_hf60.jsonl > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C/full_T8fcWt.py arena/cand/omw_v15a.py 6500-6559 $O/r4_T8fcWt_omw.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C/full_T8fcWt.py arena/cand/pub_metav4v13.py 6500-6559 $O/r4_T8fcWt_pub.jsonl 01 > /dev/null 2>&1 &
NPROC=2 $PY gold/harness/batch4.py $C/full_T8fcWt.py arena/cand/pub_smallershock.py 6600-6659 $O/r4_T8fcWt_sms.jsonl 01 > /dev/null 2>&1 &
NPROC=1 $PY gold/harness/batch4.py $C/full_T8fcWt.py ../pubnb/x_kaggriculture-v01-drip.py 7500-7519 $O/r4_T8fcWt_drip.jsonl 01 > /dev/null 2>&1 &
wait
echo "r4 runs done $(date -u +%H:%M)"
