export PYTHONIOENCODING=utf-8; PY=../../.venv/Scripts/python.exe
VBASE=omw_ad_a4 $PY exp_pin_vars.py pin_gce_train.jsonl 96 vars_gce.json > /dev/null 2>&1
VBASE=omw_ad_a4 GLIST=hold_list.json $PY exp_pin_vars.py pin_gce_hold.jsonl 96 vars_gce.json > /dev/null 2>&1
echo TRAIN; $PY sweepsum.py pin_gce_train.jsonl 131
echo HOLD; GCLASS=holdclass.json $PY sweepsum.py pin_gce_hold.jsonl 81
for s in 504 528 552; do for o in omw_v15b omw_ad_a5; do $PY batch.py ../arena/cand/omw_ad_a5gc$s.py ../arena/cand/$o.py 0-99 cl_gc${s}_$o.jsonl 2>&1 | grep "of 200"; done; done
