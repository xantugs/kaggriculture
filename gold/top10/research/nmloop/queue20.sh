#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
N=gold/top10/research/nmloop
until grep -q "^NMp39s done" $N/eval.log; do sleep 30; done
for t in NMp50 NMp53 NMp45 NMp48 NMp49 NMp51 NMp43; do bash $N/eval.sh gold/top10/cands/full_$t.py $t; done
