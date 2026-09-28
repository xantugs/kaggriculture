"""gapday_ana tables for a group of teams. usage: group_ana.py rows.jsonl[,rows2] 'TeamA|TeamB|...' [sections]
sections: val (valuation gap by day), cap (farm census), dec (tape decisions), flow (cash flow by window), work"""
import sys, os, json, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gapday_ana as A
paths, teams = sys.argv[1], sys.argv[2].split('|')
secs = sys.argv[3].split(',') if len(sys.argv) > 3 else ['val', 'cap', 'dec', 'flow']
rows = [x for p in paths.split(',') for x in A.load(p) if any(x['team'].startswith(t) for t in teams)]
n = len(rows)
print('group %s: %d seats, final margin %+.0f, wins %d' % (teams, n, st.mean(x['m'] for x in rows), sum(x['m'] > 0 for x in rows)))
if 'val' in secs:
    rate, per_plant = A.pooled_rates(rows)
    for D in (3, 6, 9, 10, 11, 12, 14, 16, 18, 22, 26, 30):
        g = {k: [] for k in 'CLBE'}
        for x in rows:
            P = {p: A.fut_price(x, min(D, 29), p) for p in A.PRODS}
            vu = A.value(x, 'days_us', D, rate, per_plant, P); ve = A.value(x, 'days_elite', D, rate, per_plant, P)
            for k in 'CLBE': g[k].append(vu[k] - ve[k])
        print('  day %2d  cash %+6.0f  liquid %+6.0f  book %+6.0f  econ %+6.0f +-%4.0f' % (
            D, st.mean(g['C']), st.mean(g['L']), st.mean(g['B']), st.mean(g['E']), st.pstdev(g['E']) / math.sqrt(n)))
A.WIN[:] = [(0, 6), (6, 9), (9, 12), (12, 16), (16, 22), (22, 30)]
if 'flow' in secs: A.flows(rows)
if 'cap' in secs: A.capacity(rows, (2, 4, 6, 8, 9, 10, 11, 12, 14, 16, 20, 24))
if 'dec' in secs: A.decisions(rows)
if 'work' in secs: A.work(rows, A.WIN)
