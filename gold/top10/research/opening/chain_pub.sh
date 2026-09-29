#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
for N in the-2945-farm-96-vs-the-top-10-public-bots kaggriculture-v41-review-candidate the-2965-master-hybrid-engine kaggriculture-v38-smarter-feed-stronger-margins the-shepherds-ledger-herd-safe-sovereign kaggriculture-findings-from-zero-to-top-meta kaggriculture-multi-route-farming-agent kaggriculture-hamburger; do
  T=pub_${N:0:14}
  NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/pubnb/x_$N.py $T hf 8 both > $O/run_$T.log 2>&1
  NPROC=3 bash $O/live.sh /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/pubnb/x_$N.py $T > $O/lpair_$T.log 2>&1
  echo CHAIN_DONE >> $O/run_$T.log
done
echo ALL_PUB_DONE >> $O/run_pub_the-2945-farm.log
