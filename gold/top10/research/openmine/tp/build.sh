#!/bin/bash
# build a tape-plus candidate: build.sh NAME '"tp": {...}, '   (T8 knob set + the given prefix, ctl_tp.py)
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
T8=$(cat gold/top10/research/openmine/tp/T8_knobs.json)
../.venv/Scripts/python.exe gold/top10/tools/mkcand.py $1 "$(echo "$T8" | sed "s/^{/{$2/")" gold/top10/full/ctl_tp.py > /dev/null && echo built $1
