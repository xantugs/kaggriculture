#!/bin/bash
# night-drop track: lean_sf8_shed on the live191 gate, fired games first, then the rest (resume)
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
export PYTHONIOENCODING=utf-8 NPROC=3
PIN_GIDS=gold/top10/gates/shed_ids_fired.txt ../.venv/Scripts/python.exe gold/top10/tools/shed_gate.py gold/top10/gates/live191.json 288 gold/top10/cands/lean_sf8_shed.py gold/top10/gates/shed_live191.jsonl
../.venv/Scripts/python.exe gold/top10/tools/shed_gate.py gold/top10/gates/live191.json 288 gold/top10/cands/lean_sf8_shed.py gold/top10/gates/shed_live191.jsonl
echo ALLDONE
