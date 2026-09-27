cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8 NPROC=2
D=gold/top10/research/phase
../.venv/Scripts/python.exe $D/gapday_play.py gold/top10/gates/goldg_games.jsonl.gz gold/top10/gates/goldg_refs.jsonl gold/top10/lean_sf8.py $D/gapday_goldg_sf8.jsonl 30
../.venv/Scripts/python.exe $D/gapday_play.py gold/top10/gates/top10g_games.jsonl.gz gold/top10/gates/top10g_refs.jsonl gold/top10/lean_sf8.py $D/gapday_top10g_sf8.jsonl 10
