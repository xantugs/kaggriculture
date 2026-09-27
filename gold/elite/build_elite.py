"""Build a self-contained base agent from one recorded elite seat: the repaired open-loop replay (outcome orders,
hand alignment, day-0 hire reservation, plant trim) embedded as compressed JSON. The result is a normal single-file
agent, so gold/build.py can append the takeover controller to it.
usage: build_elite.py games.jsonl.gz gid seat out.py [slack_min]"""
import sys, json, base64, zlib
sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

RUNTIME = r'''
import json as _j, base64 as _b, zlib as _z, collections as _c
_D = _j.loads(_z.decompress(_b.b64decode(_BLOB)).decode("utf-8"))
_UNITS, _ORDERS, _HANDS, _MONEY, _SLACK_MIN = _D["units"], {int(k): v for k, v in _D["orders"].items()}, _D["hands"], _D["money"], _D["slack_min"]
_SEED_PRICE = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
_PREF = {"MELON": 0, "TOMATO": 1, "CARROT": 2, "STRAWBERRY": 3, "WHEAT": 4}
def _fib(n):
    a, b = 1, 1
    for _ in range(n): a, b = b, a + b
    return a
_NEED_D1 = sum(_fib(i) for i in range(_HANDS[25] if len(_HANDS) > 25 else 0))
_R1 = {"armed": _NEED_D1 > 0 and (_MONEY[23] - _NEED_D1) < _SLACK_MIN, "done": False, "slack": _MONEY[23] - _NEED_D1}
_ORD = {t: [list(o) for o in v] for t, v in _ORDERS.items()}
def _reset():
    _R1["done"] = False
    for t, v in _ORDERS.items(): _ORD[t] = [list(o) for o in v]
def _r1_check(t, live):
    if not _R1["armed"] or _R1["done"] or t > 23: return
    if _MONEY[t] - live <= max(0.0, _R1["slack"]): return
    best = None
    for t2 in range(23, t, -1):
        for j, o in enumerate(_ORD.get(t2, [])):
            if o[0] == "BUY_SEED" and o[2] > 0:
                key = (_PREF.get(o[1], 9), -t2)
                if best is None or key < best[0]: best = (key, t2, j)
    if best is None: return
    _, t2, j = best
    o = _ORD[t2][j]; o[2] -= 1
    if o[2] <= 0: _ORD[t2].pop(j)
    _R1["done"] = True
def _elite_agent(obs, cfg=None):
    t = int(obs["step"])
    if t == 0: _reset()
    farm = obs["farms"][int(obs["player"])]
    priv = obs["private"]
    _r1_check(t, float(farm["money"]))
    u = _UNITS[t] if t < len(_UNITS) else None
    farmer = list(u[0]) if u and u[0] else ["PASS"]
    hands = [list(h) for h in (u[1] if u else [])]
    live = farm.get("hands") or []
    hands = (hands + [["PASS"]] * len(live))[:len(live)]
    seeds = priv.get("seeds") or {}
    units = [farmer] + hands
    demand = _c.Counter(x[1] for x in units if isinstance(x, list) and len(x) >= 2 and x[0] == "PLANT")
    for crop, n in demand.items():
        have = int(seeds.get(crop, 0))
        if n > have:
            surplus = n - have
            for i in range(len(units) - 1, -1, -1):
                x = units[i]
                if surplus and isinstance(x, list) and len(x) >= 2 and x[0] == "PLANT" and x[1] == crop:
                    units[i] = ["PASS"]; surplus -= 1
            farmer, hands = units[0], units[1:]
    market = []
    for o in _ORD.get(t, []):
        if o[0] in ("HIRE", "BUY_LAND"): market.extend([[o[0]]] * int(o[2]))
        else: market.append([o[0], o[1], int(o[2])])
    return {"farmer": farmer, "hands": hands, "market": market[:10]}
def agent(observation, configuration=None):
    try:
        return _elite_agent(observation, configuration)
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}
# stubs for optional chassis hooks the takeover controller looks up
_AD_STATE = None
_AD_CFG = None
_V219_N = None
_ARB_STATE = {}
'''

def build(d, seat, out, slack_min=8):
    from transplant import reference_log
    ref = reference_log(d, seat)
    acts = d['acts']
    units = []
    for t in range(720):
        a = acts[t + 1][seat] if t + 1 < len(acts) else None
        if isinstance(a, dict):
            units.append([a.get('farmer') or ['PASS'], a.get('hands') or []])
        else:
            units.append([['PASS'], []])
    orders = {str(t): [[op, item, q] for op, item, q in lst] for t, lst in ref['outcomes'].items()}
    blob = base64.b64encode(zlib.compress(json.dumps(dict(units=units, orders=orders, hands=ref['hands'], money=ref['money'],
                                                          slack_min=slack_min), separators=(',', ':')).encode('utf-8'), 9)).decode('ascii')
    src = ('"""Elite route transplant: %s, episode %s, seat %d, recorded %s (rival %s). Built from a public replay."""\n'
           % (d['info']['TeamNames'][seat], d['id'], seat, d['rewards'][seat], d['info']['TeamNames'][1 - seat]))
    src += '_BLOB = "%s"\n' % blob + RUNTIME
    open(out, 'w', encoding='utf-8').write(src)
    return ref

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, gid, seat, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    slack_min = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    d = next(g for g in load_games(path) if g['id'] == gid)
    ref = build(d, seat, out, slack_min)
    import os
    print('built', out, os.path.getsize(out), 'bytes; recorded reproduces:', ref['ok'], 'shops', ref['shops'])
