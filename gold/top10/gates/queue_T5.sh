#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
PY=../.venv/Scripts/python.exe; export PYTHONIOENCODING=utf-8
until grep -q "full_T5.py:" gold/top10/gates/pin249_T5.log 2>/dev/null; do sleep 30; done
$PY gold/top10/tools/shed_cpu.py 113676198,113633403,113624741,113772943 gold/top10/cands/full_T5.py,gold/top10/lean_sf8.py > gold/top10/gates/cpu_T5.log 2>&1
NPROC=10 $PY gold/harness/pinned4.py moon/strong2800.json,moon/strong_new.json 144 gold/top10/cands/full_T5.py gold/top10/gates/s2800_T5.jsonl offhand > gold/top10/gates/s2800_T5.log 2>&1
NPROC=10 $PY gold/harness/batch4.py gold/top10/cands/full_T5.py arena/cand/omw_v15a.py 6100-6149 gold/top10/gates/cl_T5_omw_v15a.jsonl 01 > gold/top10/gates/cl_T5_omw_v15a.log 2>&1
echo QT5 DONE
