"""Stream the openmine day files into a compact per-seat herd table (herd/compact.jsonl).
One row per seat: meta + days[30] with the herd-relevant fields only. Low memory (line streaming).
usage: python herd/compact.py   (from openmine/)"""
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
SRC = [('elite_days.jsonl', 'elite_seats.jsonl'), ('ours_T7_days.jsonl', 'ours_T7_seats.jsonl'),
       ('ours_T7_opp_days.jsonl', 'ours_T7_opp_seats.jsonl')]
AN = ('GOOSE', 'COW', 'SHEEP')
PR = ('EGG', 'MILK', 'WOOL', 'FERTILIZER', 'WHEAT')
SIGN = {'S': 1, 'BP': -1, 'BS': -1, 'BA': -1, 'H': -1, 'L': -1}


def day_row(r):
    ops = r.get('ops', {})
    o = collections.Counter()
    placed_q = collections.Counter()
    built_q = collections.Counter()
    for k, n in ops.items():
        v, _, q = k.partition('@')
        o[v] += n
        if v.startswith('PLACE:') and v.split(':')[1] in AN:
            placed_q[v.split(':')[1] + '@' + q] += n
        if v in ('BUILD_COOP', 'BUILD_PASTURE'):
            built_q[v + '@' + q] += n
    x = dict(d=r['d'], m0=r['m0'], mend=r['mend'], hands=r.get('hands', 0), hires=r.get('hires', 0),
             wage=r.get('wage', 0), quads=r.get('quads'), shops=r.get('shops') or [],
             herd=r.get('herd', {}), struct=r.get('struct', {}), crops=r.get('crops', {}),
             ba={k: v for k, v in r.get('buy_animal', {}).items()},
             sell={k: v for k, v in r.get('sell', {}).items() if k in PR},
             bp={k: v for k, v in r.get('buy_prod', {}).items()},
             bs_wheat=r.get('buy_seed', {}).get('WHEAT'),
             placed={a: o.get('PLACE:' + a, 0) for a in AN}, placed_q=dict(placed_q), built_q=dict(built_q),
             build_coop=o.get('BUILD_COOP', 0), build_past=o.get('BUILD_PASTURE', 0),
             dig_coop=o.get('DIG:COOP', 0), dig_past=o.get('DIG:PASTURE', 0),
             feed={a: o.get('FEED:' + a, 0) for a in AN}, care={a: o.get('CARE:' + a, 0) for a in AN},
             coll={a: o.get('COLLECT_FERTILIZER:' + a, 0) for a in AN},
             harv={p: o.get('HARVEST:' + p, 0) for p in ('EGG', 'MILK', 'WOOL')},
             hv={k: v for k, v in r.get('hv', {}).items() if k in PR},
             plant_wheat=o.get('PLANT:WHEAT', 0), fert_ops=sum(n for k, n in o.items() if k.startswith('FERTILIZE:')),
             land=[(l['q'], l['h'], l['cash_before']) for l in r.get('land', [])],
             riv_herd=(r.get('riv') or {}).get('herd', {}), riv_quads=(r.get('riv') or {}).get('quads'))
    if r.get('detail'):
        x['shed'] = {k: v for k, v in (r.get('shed') or {}).items() if v}
        px = r.get('px') or {}
        x['px'] = {k: px.get(k) for k in PR}
        # cash at the observation of each animal buy / land buy (hour granularity)
        flows = collections.defaultdict(float)
        for h, op, item, n, usd in r.get('fills', []):
            flows[h] += SIGN[op] * usd
        cash_at = {}
        c = r['m0']
        for h in range(24):
            cash_at[h] = c
            c += flows.get(h, 0.0)
        x['ba_fills'] = [[h, item, n, usd, round(cash_at[h], 1)] for h, op, item, n, usd in r.get('fills', []) if op == 'BA']
        x['sell_fills'] = [[h, item, n, usd] for h, op, item, n, usd in r.get('fills', []) if op == 'S' and item in PR]
        x['bpw_fills'] = [[h, item, n, usd] for h, op, item, n, usd in r.get('fills', []) if op == 'BP']
    return x


def main():
    out = open(os.path.join(HERE, 'compact.jsonl'), 'w', encoding='utf-8', newline='\n')
    for dfile, sfile in SRC:
        seats = {}
        with open(os.path.join(OM, sfile), encoding='utf-8') as f:
            for l in f:
                s = json.loads(l)
                seats[(s['gid'], s['seat'], s['role'])] = s
        cur_key, cur = None, None

        def flush():
            if cur is None:
                return
            s = seats.get(cur_key, {})
            meta = dict(gid=cur_key[0], seat=cur_key[1], role=cur_key[2], team=cur['team'], opp=cur['opp'],
                        date=cur['date'], shops_all=s.get('shops'), rew=s.get('rew'), rec_ok=s.get('rec_ok'),
                        final=s.get('final'), elite_seat=s.get('elite_seat'), m=s.get('m'), cand=cur.get('cand'))
            days = sorted(cur['days'], key=lambda z: z['d'])
            meta['days'] = days
            out.write(json.dumps(meta, ensure_ascii=False) + '\n')
        n = 0
        with open(os.path.join(OM, dfile), encoding='utf-8') as f:
            for l in f:
                r = json.loads(l)
                key = (r['gid'], r['seat'], r['role'])
                if key != cur_key:
                    flush()
                    cur_key, cur = key, dict(team=r['team'], opp=r['opp'], date=r['date'], cand=r.get('cand'), days=[])
                cur['days'].append(day_row(r))
                n += 1
        flush()
        print(dfile, n, 'rows', len(seats), 'seats', flush=True)
    out.close()


if __name__ == '__main__':
    main()
