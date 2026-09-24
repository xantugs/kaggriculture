# v15 candidates: pinned 188 + closed loop vs public chassis, v10, v12.
export PYTHONIOENCODING=utf-8; P=../../.venv/Scripts/python.exe; C=../arena/cand
until grep -q " vs " clf_v14c_v10.log 2>/dev/null; do sleep 20; done
$P exp_v15.py v15_pin96.jsonl 96 > v15_pin96.log 2>&1
for c in v15a v15b; do
  $P batch.py $C/omw_$c.py ../arena/pub/omw.py 0-99 clf_${c}_omw.jsonl > clf_${c}_omw.log 2>&1
  $P batch.py $C/omw_$c.py $C/omw_v10.py 0-99 clf_${c}_v10.jsonl > clf_${c}_v10.log 2>&1
  $P batch.py $C/omw_$c.py $C/omw_v12.py 0-99 clf_${c}_v12.jsonl > clf_${c}_v12.log 2>&1
done
tail -4 v15_pin96.log; for f in clf_v15*.log; do head -1 $f | sed 's#\.\./arena/[a-z/]*##g'; done
