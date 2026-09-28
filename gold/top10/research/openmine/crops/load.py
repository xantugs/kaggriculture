"""Compact loader: stream openmine/*_days.jsonl, keep days 0..16 and the crop-relevant fields, pickle to crops/days.pkl.
usage: load.py            (builds crops/days.pkl)
       from load import days  -> dict (role, gid, seat) -> list of 17 day rows"""
import os, json, pickle, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
PKL = os.path.join(HERE, 'days.pkl')
KEEP = ('d', 'm0', 'mend', 'mmin', 'shops', 'crops', 'q', 'hv', 'buy_seed', 'sell', 'buy_prod', 'px', 'quads', 'land',
        'hires', 'seeds', 'units', 'free', 'weeds', 'herd')
CROPS = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON')


def _slim(r):
    o = {k: r.get(k) for k in KEEP}
    o['ops'] = {k: v for k, v in (r.get('ops') or {}).items()
                if k.split(':')[0] in ('PLANT', 'WATER', 'FERTILIZE', 'DIG') or
                (k.startswith('HARVEST:') and k.split(':')[1].split('@')[0] in CROPS)}
    o['riv_crops'] = (r.get('riv') or {}).get('crops')
    o['riv_quads'] = (r.get('riv') or {}).get('quads')
    return o


def build():
    out = {}
    meta = {}
    for fn in ('elite_days.jsonl', 'ours_T7_days.jsonl', 'ours_T7_opp_days.jsonl'):
        with open(os.path.join(OM, fn), encoding='utf-8') as fh:
            for line in fh:
                r = json.loads(line)
                if r['d'] > 16:
                    continue
                key = (r['role'], r['gid'], r['seat'])
                out.setdefault(key, [None] * 17)[r['d']] = _slim(r)
                meta[key] = dict(team=r['team'], opp=r['opp'], date=r['date'])
    seats = {}
    for fn in ('elite_seats.jsonl', 'ours_T7_seats.jsonl', 'ours_T7_opp_seats.jsonl'):
        with open(os.path.join(OM, fn), encoding='utf-8') as fh:
            for line in fh:
                s = json.loads(line)
                seats[(s['role'], s['gid'], s['seat'])] = dict(rew=s['rew'], shops=s['shops'], land=s['land'],
                                                              m=s.get('m'), elite_seat=s.get('elite_seat'))
    with open(PKL, 'wb') as fh:
        pickle.dump(dict(days=out, meta=meta, seats=seats), fh, protocol=4)
    print('rows', len(out))


def days():
    with open(PKL, 'rb') as fh:
        return pickle.load(fh)


if __name__ == '__main__':
    build()
