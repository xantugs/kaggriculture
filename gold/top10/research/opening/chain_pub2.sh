#!/bin/bash
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening
run() {
  NPROC=3 ../.venv/Scripts/python.exe $O/diag.py run /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/pubnb/x_$1.py $2 hf 8 both > $O/run_$2.log 2>&1
  NPROC=3 bash $O/live.sh /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/pubnb/x_$1.py $2 > $O/lpair_$2.log 2>&1
  echo CHAIN_DONE >> $O/run_$2.log
}
run kaggriculture-findings-from-zero-to-top-meta pub_findings
run kaggriculture-hamburger pub_hamburger
run the-2965-master-hybrid-engine pub_2965
run the-shepherds-ledger-herd-safe-sovereign pub_shepherd
run kaggriculture-multi-route-farming-agent pub_multiroute
echo ALL_PUB_DONE >> $O/run_pub_multiroute.log
