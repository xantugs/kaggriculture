#!/bin/bash
# Evaluate a new file from the other session against v18 (adapt).
# usage: bash evalnew.sh their_file.py name        (run from moon/)
# Tests their full file (<name>_raw), their GOLD section grafted onto v16e (<name>) and onto v16e+SES (<name>_ses,
# base omw_ad_a5s; compare with v19 = ses_d):
#   1 official runner timing   2 fresh set (today's field, implied rating)   3 train + holdout pinned   4 closed loop vs v18
set -e
export PYTHONIOENCODING=utf-8; PY=../../.venv/Scripts/python.exe; C=../arena/cand
src=$1; name=$2
cp "$src" $C/${name}_raw.py
$PY graft_gc.py "$src" $name || echo "GRAFT FAILED - testing the raw file only"
$PY graft_gc.py "$src" ${name}_ses omw_ad_a5s > /dev/null || echo "SES GRAFT FAILED"
labs="[\"${name}_raw\", \"${name}_raw\", {}], [\"v18\", \"adapt\", {}], [\"v19\", \"ses_d\", {}]"
[ -f $C/$name.py ] && labs="[\"$name\", \"$name\", {}], $labs"
[ -f $C/${name}_ses.py ] && labs="[\"${name}_ses\", \"${name}_ses\", {}], $labs"
echo "[$labs]" > vars_$name.json
echo "== 1 official runner"
for f in $C/${name}_raw.py $C/$name.py; do [ -f $f ] && timeout 590 $PY official_check.py $f $C/adapt.py 2>&1 | grep -v "Loading environment" | tail -3; done
echo "== 2 fresh sets (fresh16 base v16d, fresh17 base v17)"
VBASE=omw_ad_a4 GLIST=fresh16_list.json $PY exp_pin_vars.py pin_fresh_$name.jsonl 96 vars_$name.json > /dev/null 2>&1
GCLASS=fresh16class.json $PY sweepsum.py pin_fresh_$name.jsonl 46
$PY implied.py pin_fresh_$name.jsonl eps_live16.json
VBASE=omw_ad_a5gc GLIST=fresh17_list.json $PY exp_pin_vars.py pin_f17_$name.jsonl 96 vars_$name.json > /dev/null 2>&1
GCLASS=fresh17class.json $PY sweepsum.py pin_f17_$name.jsonl 24
$PY implied.py pin_f17_$name.jsonl eps_live17.json
echo "== 3 train / holdout pinned (base v18)"
VBASE=adapt $PY exp_pin_vars.py pin_train_$name.jsonl 96 vars_$name.json > /dev/null 2>&1
$PY sweepsum.py pin_train_$name.jsonl 131
VBASE=adapt GLIST=hold_list.json $PY exp_pin_vars.py pin_hold_$name.jsonl 96 vars_$name.json > /dev/null 2>&1
GCLASS=holdclass.json $PY sweepsum.py pin_hold_$name.jsonl 81
echo "== 4 closed loop vs v18"
for f in ${name}_raw $name ${name}_ses; do [ -f $C/$f.py ] && [ "$f" != adapt ] && $PY batch.py $C/$f.py $C/adapt.py 0-99 cl_${f}_v18.jsonl 2>&1 | grep "of 200"; done
echo done
