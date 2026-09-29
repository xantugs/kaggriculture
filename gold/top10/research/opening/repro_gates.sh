#!/bin/bash
# repro_gates.sh : the exact upload bytes (gold/submit) on goldg + top10g, to confirm they reproduce the gate counts of the
# cands builds; then c2tr; plus the official kaggle_environments validation episode (self-play) on each exact file.
cd "C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg"
export PYTHONIOENCODING=utf-8
O=gold/top10/research/opening; PY=../.venv/Scripts/python.exe; S=gold/submit; G=gold/top10/gates
EG="gold/elite/elite_gate.py run"
mkdir -p $O/repro
( for f in main_ctl_FWt main_ctl_T8fcWt main_ctl_c2tr; do
    for sd in 6042 8500; do echo "$f seed $sd: $($PY gold/top10/tools/official_selfplay.py $S/$f.py $sd 2>&1 | tail -1)"; done
  done > $O/repro/official_selfplay.txt 2>&1 ) &
for f in main_ctl_FWt main_ctl_T8fcWt; do
  NPROC=4 $PY $EG $G/goldg_games.jsonl.gz $G/goldg_refs.jsonl $S/$f.py $O/repro/${f}_goldg.jsonl > /dev/null 2>&1 &
  NPROC=4 $PY $EG $G/top10g_games.jsonl.gz $G/top10g_refs.jsonl $S/$f.py $O/repro/${f}_top10g.jsonl > /dev/null 2>&1 &
done
wait
echo "stage 1 done $(date -u +%H:%M)"
NPROC=4 $PY $EG $G/goldg_games.jsonl.gz $G/goldg_refs.jsonl $S/main_ctl_c2tr.py $O/repro/main_ctl_c2tr_goldg.jsonl > /dev/null 2>&1 &
NPROC=4 $PY $EG $G/top10g_games.jsonl.gz $G/top10g_refs.jsonl $S/main_ctl_c2tr.py $O/repro/main_ctl_c2tr_top10g.jsonl > /dev/null 2>&1 &
OPPS="gold/submit/main_ctl_T8.py gold/top10/cands/full_v29fc_FW.py arena/cand/omw_v15a.py ../pubnb/x_kaggriculture-x544-nah-i-d-win.py ../pubnb/x_kaggriculture-v01-drip.py ../pubnb/x_notebooke394244546.py"
for f in main_ctl_FWt main_ctl_T8fcWt; do
  i=0; for opp in $OPPS; do i=$((i+1))
    NPROC=1 $PY gold/harness/batch4.py $S/$f.py $opp 8600-8619 $O/preflight/${f}_b$i.jsonl 01 > /dev/null 2>&1 &
  done
done
wait
echo "repro_gates done $(date -u +%H:%M)"
