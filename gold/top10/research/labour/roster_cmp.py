"""Roster shape of several probe runs on the same seats (days d0-d1): hands/day, sd, wage paid, flat-roster wage, excess,
days with >=13 hands, margin. usage: roster_cmp.py d0 d1 label=rows.jsonl label=rows.jsonl ...   (first = base for pairing)"""
import sys, json, statistics as st
FIB = [1, 1]
while len(FIB) < 30: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
d0, d1 = int(sys.argv[1]), int(sys.argv[2])
runs = []
for a in sys.argv[3:]:
    lab, p = a.split('=', 1)
    R = {}
    for l in open(p, encoding='utf-8'):
        if l.strip():
            r = json.loads(l); R[(r['gid'], r['seat'])] = r
    runs.append((lab, R))
keys = set(runs[0][1])
for _, R in runs[1:]:
    keys &= set(R)
keys = sorted(keys)
print(len(keys), 'common seats, days', d0, '-', d1)
def shape(days):
    hs = [days.get(str(d), {}).get('hire', 0) for d in range(d0, d1 + 1)]
    paid = sum(days.get(str(d), {}).get('wage', 0) for d in range(d0, d1 + 1))
    tot = sum(hs); n = len(hs); lo = tot // n; k = tot - lo * n
    flat = k * CUM[lo + 1] + (n - k) * CUM[lo]
    return dict(hd=tot, paid=paid, flat=flat, sd=st.pstdev(hs), n13=sum(h >= 13 for h in hs))
def show(lab, side, R):
    S = [shape(R[k][side]) for k in keys]
    m = lambda f: st.mean(x[f] for x in S)
    extra = ''
    if side == 'days_us':
        extra = f" margin {st.mean(R[k]['m'] for k in keys):+7.0f} wins {sum(R[k]['m'] > 0 for k in keys):3d}"
    print(f"{lab:10s} {side[5:]:5s} hand-days {m('hd'):6.1f} paid ${m('paid'):5.0f} flat ${m('flat'):5.0f} excess ${m('paid')-m('flat'):4.0f} sd {m('sd'):.2f} n13 {m('n13'):.2f}{extra}")
for lab, R in runs:
    show(lab, 'days_us', R)
show(runs[0][0], 'days_elite', runs[0][1])
if len(runs) > 1:
    b = runs[0][1]
    for lab, R in runs[1:]:
        d = [R[k]['m'] - b[k]['m'] for k in keys]
        print(f"{lab} - {runs[0][0]}: {st.mean(d):+.0f} +- {st.pstdev(d)/len(d)**0.5:.0f}")
