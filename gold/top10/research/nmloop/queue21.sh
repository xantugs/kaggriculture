#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
N=gold/top10/research/nmloop
until grep -q "^NMp53 done" $N/eval.log; do sleep 30; done
for t in NMp58 NMp45 NMp48 NMp49 NMp56; do bash $N/eval.sh gold/top10/cands/full_$t.py $t; done
echo "queue21 done" >> $N/eval.log
