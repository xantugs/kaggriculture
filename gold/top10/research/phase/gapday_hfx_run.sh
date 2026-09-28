cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
D=gold/top10/research/phase
export PYTHONIOENCODING=utf-8 NPROC=2
PY=../.venv/Scripts/python.exe
$PY $D/gapday_play.py gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl $D/cand_T5_hfx13.py $D/gapday_goldg_T5hfx13.jsonl 10
$PY $D/gapday_play.py gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl $D/cand_T5_hfx13.py $D/gapday_top10g_T5hfx13.jsonl 8
echo ALLDONE
