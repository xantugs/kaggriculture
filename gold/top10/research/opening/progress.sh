#!/bin/bash
# progress.sh: one-line-per-run progress bars for the current background runs
cd /c/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg
O=gold/top10/research/opening
bar() { n=$1; t=$2; w=30; f=$(( n * w / (t>0?t:1) )); [ $f -gt $w ] && f=$w; printf "%-18s [%s%s] %3d/%d\n" "$3" "$(printf '%*s' $f '' | tr ' ' '#')" "$(printf '%*s' $((w-f)) '')" "$n" "$t"; }
for r in p1; do f=$O/sp_${r}_vs_T8.jsonl; n=$(grep -c '"seed"' $f 2>/dev/null); w=$(grep -c '"m": [0-9]' $f 2>/dev/null); bar ${n:-0} 40 "$r vs T8 (w$w)"; done
bar $(grep -c '"gid"' $O/pin249_FK.jsonl 2>/dev/null) 498 "fert-input pin249"
s=$(grep -c '^s[0-9]' $O/search_open7.log 2>/dev/null); a=$(grep -c ACCEPT $O/search_open7.log 2>/dev/null); bar ${s:-0} 60 "search (acc $a)"
date -u +"%H:%M UTC"
