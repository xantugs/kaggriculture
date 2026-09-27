cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
D=gold/top10/research/phase
SP=C:/Users/khant/AppData/Local/Temp/claude/C--Users-khant-OneDrive-Documents-ChatGPT-2027-kaggriculture-review/875e1517-4223-4d24-a8c6-423a3c7003a6/scratchpad
export PYTHONIOENCODING=utf-8 NPROC=2 HYB_DIR=$SP/gd/hyb
until [ -f $D/gapday_top10g_sf8.jsonl ] && [ $(wc -l < $D/gapday_top10g_sf8.jsonl) -ge 90 ]; do sleep 30; done
sleep 20
PY=../.venv/Scripts/python.exe
CTL=$SP/gd/ctl_sf8.py
for DD in 16 22; do
  $PY $D/gapday_hybrid.py gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $CTL $DD $D/gapday_hyb${DD}_goldg.jsonl 10
  $PY $D/gapday_hybrid.py gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $CTL $DD $D/gapday_hyb${DD}_top10g.jsonl 8
done
$PY $D/gapday_hybrid.py gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $CTL 30 $D/gapday_hyb30_goldg.jsonl 4
$PY $D/gapday_hybrid.py gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $CTL 30 $D/gapday_hyb30_top10g.jsonl 3
for DD in 12; do
  $PY $D/gapday_hybrid.py gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $CTL $DD $D/gapday_hyb${DD}_goldg.jsonl 10
  $PY $D/gapday_hybrid.py gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $CTL $DD $D/gapday_hyb${DD}_top10g.jsonl 8
done
echo ALLDONE
