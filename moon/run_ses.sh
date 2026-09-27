export PYTHONIOENCODING=utf-8; PY=../../.venv/Scripts/python.exe; V=${1:-vars_ses.json}; T=${2:-ses}
VBASE=adapt $PY exp_pin_vars.py pin_${T}_train.jsonl 96 $V > /dev/null 2>&1; echo "== train"; $PY sweepsum.py pin_${T}_train.jsonl 131
VBASE=adapt GLIST=hold_list.json $PY exp_pin_vars.py pin_${T}_hold.jsonl 96 $V > /dev/null 2>&1; echo "== hold"; GCLASS=holdclass.json $PY sweepsum.py pin_${T}_hold.jsonl 81
VBASE=adapt GLIST=fresh16_list.json $PY exp_pin_vars.py pin_${T}_f16.jsonl 96 $V > /dev/null 2>&1; echo "== fresh16"; GCLASS=fresh16class.json $PY sweepsum.py pin_${T}_f16.jsonl 46; $PY implied.py pin_${T}_f16.jsonl eps_live16.json
VBASE=adapt GLIST=fresh17_list.json $PY exp_pin_vars.py pin_${T}_f17.jsonl 96 $V > /dev/null 2>&1; echo "== fresh17"; GCLASS=fresh17class.json $PY sweepsum.py pin_${T}_f17.jsonl 24; $PY implied.py pin_${T}_f17.jsonl eps_live17.json
