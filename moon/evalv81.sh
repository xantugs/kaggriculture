#!/bin/bash
# v81 (other session's main_ctl_rich2_m7.py) grafts + SES hybrids: pinned fresh16/fresh17/train/hold, then closed loops
export PYTHONIOENCODING=utf-8; PY=../../.venv/Scripts/python.exe; C=../arena/cand; n=r81
echo "== fresh16"; VBASE=omw_ad_a4 GLIST=fresh16_list.json $PY exp_pin_vars.py pin_fresh_$n.jsonl 96 vars_$n.json > /dev/null 2>&1
GCLASS=fresh16class.json $PY sweepsum.py pin_fresh_$n.jsonl 46; $PY implied.py pin_fresh_$n.jsonl eps_live16.json
echo "== fresh17"; VBASE=omw_ad_a5gc GLIST=fresh17_list.json $PY exp_pin_vars.py pin_f17_$n.jsonl 96 vars_$n.json > /dev/null 2>&1
GCLASS=fresh17class.json $PY sweepsum.py pin_f17_$n.jsonl 24; $PY implied.py pin_f17_$n.jsonl eps_live17.json
echo "== train"; VBASE=adapt $PY exp_pin_vars.py pin_train_$n.jsonl 96 vars_$n.json > /dev/null 2>&1; $PY sweepsum.py pin_train_$n.jsonl 131
echo "== hold"; VBASE=adapt GLIST=hold_list.json $PY exp_pin_vars.py pin_hold_$n.jsonl 96 vars_$n.json > /dev/null 2>&1; GCLASS=holdclass.json $PY sweepsum.py pin_hold_$n.jsonl 81
echo "== closed loop vs v18 (0-99)"
for f in r81_raw r81 r81t2 r81h r81ht2; do $PY batch.py $C/$f.py $C/adapt.py 0-99 cl_${f}_v18.jsonl 2>&1 | grep "of 200"; done
echo done
