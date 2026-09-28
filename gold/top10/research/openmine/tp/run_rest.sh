#!/bin/bash
# run_rest.sh CAND [CAND...]: the non-opening-winner seats of goldg and top10g (T8 baseline = Kaggle rows r14c)
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/openmine/tp/out
for c in "$@"; do
  NPROC=${NPROC:-4} ../.venv/Scripts/python.exe gold/top10/research/openmine/tp/tp_diag.py elite goldg gold/top10/cands/full_$c.py $O/goldgR_$c.jsonl "mtmr_s1,Kaggledew Valley 🏆,TheEggman" 2>&1 | grep -v "Loading env" >> $O/smoke.log
  NPROC=${NPROC:-4} ../.venv/Scripts/python.exe gold/top10/research/openmine/tp/tp_diag.py elite top10g gold/top10/cands/full_$c.py $O/top10gR_$c.jsonl "DSM,Vadim Vasilenko,M & M & P & Q,Majkel1337,DECEM,Unknown Mother-Goose,Azat Akhtyamov" 2>&1 | grep -v "Loading env" >> $O/smoke.log
  echo "done rest $c $(date -u +%H:%M)" >> $O/smoke.log
done
