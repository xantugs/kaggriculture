"""Summaries of labour_probe output.
usage: lab_ana.py gate out.jsonl [out2.jsonl ...]     # sf8 (us) vs repaired elite, per phase
       lab_ana.py rec  rec.jsonl team1,team2,...     # recorded games, per team
"""
import sys, json, collections, statistics as st

PHASES = [('d0-5', range(0, 6)), ('d6-11', range(6, 12)), ('d12-15', range(12, 16)), ('d16-23', range(16, 24)),
          ('d24-28', range(24, 29)), ('d29', range(29, 30))]
FIB = [1, 1]
while len(FIB) < 40:
    FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(40)]


def dayrow(c):
    g = lambda k: c.get(k, 0)
    eff = g('eff_f') + g('eff_h')
    noop = sum(v for k, v in c.items() if k.startswith('n:'))
    plants = sum(v for k, v in c.items() if k.startswith('c:P:'))
    anim = sum(v for k, v in c.items() if k.startswith('c:A:'))
    hv = {k[3:]: v for k, v in c.items() if k.startswith('hv:')}
    return dict(hire=g('hire'), wage=g('wage'), ut=g('ut'), eff=eff, mv=g('mv'), pas=g('pass') + g('noact'), noop=noop + g('mvx'),
                tact=g('tile_acts'), dist=g('dist'), plant=g('e:PLANT'), water=g('e:WATER'), wy=g('wy'), wm=g('wm'),
                harv=g('e:HARVEST'), feed=g('e:FEED'), care=g('e:CARE'), coll=g('e:COLLECT_FERTILIZER'), fert=g('e:FERTILIZE'),
                drop=g('e:DROP'), pick=g('e:PICKUP'), dig=g('e:DIG'), plots=plants, anim=anim, owned=g('c:owned'),
                empty=g('c:empty'), weed=g('c:weed'), hv=sum(hv.values()), hvw=hv.get('WHEAT', 0), hvc=hv.get('CARROT', 0),
                hvt=hv.get('TOMATO', 0), hvs=hv.get('STRAWBERRY', 0), hve=hv.get('EGG', 0), hvm=hv.get('MILK', 0),
                hvwo=hv.get('WOOL', 0), geese=g('c:A:GOOSE'), cows=g('c:A:COW'), sheep=g('c:A:SHEEP'),
                pw=g('c:P:WHEAT'), pc=g('c:P:CARROT'), pt=g('c:P:TOMATO'), ps=g('c:P:STRAWBERRY'), pm=g('c:P:MELON'))


COLS = ['hire', 'wage', 'ut', 'eff', 'mv', 'pas', 'noop', 'plots', 'anim', 'owned', 'empty', 'plant', 'water', 'wy', 'wm', 'harv',
        'feed', 'care', 'coll', 'fert', 'drop', 'pick', 'hv', 'hvw', 'hvc', 'hvt', 'hvs', 'hve', 'hvm', 'hvwo',
        'pw', 'pc', 'pt', 'ps', 'pm', 'geese', 'cows', 'sheep']


def phase_table(label_rows):
    """label_rows: {label: [days_dict, ...]} -> printed per-phase averages (per day)."""
    for pname, rng in PHASES:
        print(f'--- {pname} (per day, mean over seats)')
        hdr = f"{'':10s}" + ''.join(f'{c:>7s}' for c in COLS) + f"{'dist':>6s}{'eff/ut':>7s}{'mv/ut':>7s}{'tl/u':>6s}"
        print(hdr)
        for lab, seats in label_rows.items():
            acc = collections.defaultdict(float); nd = 0
            for days in seats:
                for d in rng:
                    c = days.get(str(d))
                    if not c:
                        continue
                    r = dayrow(c); nd += 1
                    for k in COLS + ['tact', 'dist']:
                        acc[k] += r[k]
            if not nd:
                continue
            m = {k: v / nd for k, v in acc.items()}
            units = m['ut'] / 23.5 if m['ut'] else 1
            line = f'{lab[:10]:10s}' + ''.join(f'{m[c]:7.1f}' for c in COLS)
            line += f"{m['dist'] / max(1, m['tact']):6.2f}{m['eff'] / max(1, m['ut']):7.2f}{m['mv'] / max(1, m['ut']):7.2f}{(m['plots'] + m['anim']) / max(1, units):6.1f}"
            print(line)


def hire_shape(seats, d0=16, d1=29):
    """Per seat: hand-days, actual wage, the wage at a flat roster with the same hand-days, and the day-to-day spread."""
    out = []
    for days in seats:
        hs = [days.get(str(d), {}).get('hire', 0) for d in range(d0, d1)]
        ws = [days.get(str(d), {}).get('wage', 0) for d in range(d0, d1)]
        tot = sum(hs); n = len(hs)
        lo = tot // n; k = tot - lo * n
        flat = k * CUM[lo + 1] + (n - k) * CUM[lo]
        out.append(dict(hd=tot, wage=sum(ws), flat=flat, sd=st.pstdev(hs), mx=max(hs), mn=min(hs)))
    return out


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'gate':
        rows = [json.loads(l) for p in sys.argv[2:] for l in open(p, encoding='utf-8')]
        groups = collections.OrderedDict()
        groups['us(sf8)'] = [r['days_us'] for r in rows]
        groups['elite'] = [r['days_elite'] for r in rows]
        wins = [r for r in rows if r['m'] > 0]; loss = [r for r in rows if r['m'] <= 0]
        groups['us-win'] = [r['days_us'] for r in wins]; groups['el-win'] = [r['days_elite'] for r in wins]
        groups['us-loss'] = [r['days_us'] for r in loss]; groups['el-loss'] = [r['days_elite'] for r in loss]
        print(len(rows), 'seats, wins', len(wins))
        phase_table(groups)
        for lab in ('us(sf8)', 'elite'):
            for (a, b) in ((0, 16), (16, 29)):
                hs = hire_shape(groups[lab], a, b)
                n = len(hs)
                print(f"{lab:8s} days {a}-{b-1}: hand-days {sum(h['hd'] for h in hs)/n:6.1f}  wage {sum(h['wage'] for h in hs)/n:7.0f}"
                      f"  flat-roster wage {sum(h['flat'] for h in hs)/n:7.0f}  sd {sum(h['sd'] for h in hs)/n:4.2f}"
                      f"  max {sum(h['mx'] for h in hs)/n:4.1f} min {sum(h['mn'] for h in hs)/n:4.1f}")
    else:
        rows = [json.loads(l) for l in open(sys.argv[2], encoding='utf-8')]
        teams = sys.argv[3].split(',')
        groups = collections.OrderedDict((t, []) for t in teams)
        groups['others'] = []
        for r in rows:
            for s in (0, 1):
                t = r['teams'][s]
                (groups[t] if t in groups else groups['others']).append(r['days'][s])
        print({k: len(v) for k, v in groups.items()})
        phase_table(groups)
        for lab, seats in groups.items():
            if not seats:
                continue
            for (a, b) in ((0, 16), (16, 29)):
                hs = hire_shape(seats, a, b)
                n = len(hs)
                print(f"{lab[:10]:10s} days {a}-{b-1}: hand-days {sum(h['hd'] for h in hs)/n:6.1f}  wage {sum(h['wage'] for h in hs)/n:7.0f}"
                      f"  flat {sum(h['flat'] for h in hs)/n:7.0f}  sd {sum(h['sd'] for h in hs)/n:4.2f}")
