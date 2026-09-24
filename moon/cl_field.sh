# Closed loop vs non-GLUTH opponents (public chassis, v10): v13f, v14a (GLUTH 8 + SR 14), v14c (SR 14 only).
export PYTHONIOENCODING=utf-8; P=../../.venv/Scripts/python.exe; C=../arena/cand
until grep -q "z=" r51_rest2.log 2>/dev/null; do sleep 20; done
for opp in pub/omw v10; do o=$(basename $opp); OP=../arena/$opp.py; [ $opp = v10 ] && OP=$C/omw_v10.py
  for c in v13f v14a v14c; do $P batch.py $C/omw_$c.py $OP 0-99 clf_${c}_$o.jsonl > clf_${c}_$o.log 2>&1; done; done
for f in clf_*.log; do head -2 $f | sed 's#\.\./arena/[a-z/]*##g'; done
