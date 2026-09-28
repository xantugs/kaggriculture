cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
D=gold/top10/research/phase
SP=C:/Users/khant/AppData/Local/Temp/claude/C--Users-khant-OneDrive-Documents-ChatGPT-2027-kaggriculture-review/875e1517-4223-4d24-a8c6-423a3c7003a6/scratchpad
export PYTHONIOENCODING=utf-8 NPROC=2 HYB_DIR=$SP/gd/hybk
export HYB_KNOBS='{"visit_watered": true, "drop_refill": true, "trim_fix": true, "shed_skip": true, "eh_level": {"margin": 2, "min_units": 5, "last_day": 26, "frac": 0.5}}'
PY=../.venv/Scripts/python.exe
CTL=gold/top10/full/ctl_top.py
for DD in 16 22; do
  $PY $D/gapday_hybrid_k.py gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $CTL $DD $D/gapday_T5hyb${DD}_goldg.jsonl 10
  $PY $D/gapday_hybrid_k.py gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $CTL $DD $D/gapday_T5hyb${DD}_top10g.jsonl 8
done
echo ALLDONE
