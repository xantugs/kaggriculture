#!/bin/bash
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
N=gold/top10/research/nmloop
for t in NMp38 NMp39s NMp43; do bash $N/eval.sh gold/top10/cands/full_$t.py $t; done
