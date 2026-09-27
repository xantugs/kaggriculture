"""Hybrid mirror: our seat plays the ELITE's own repaired opening (the same recording the elite side replays) to day D,
then the sf8 controller (divergent-path settings at the top level, no chassis layers) owns the farm from day D.
The elite side is the gate's repaired recording, as in elite_gate._play. Both farms are identical up to day D (weeds
aside), so the final margin measures the controller against the elite's own continuation from equal footing.

usage: gapday_hybrid.py games.jsonl.gz refs.jsonl ctl.py D out.jsonl [per_team] [teams|ALL]
  D = takeover day (the controller owns the farm from hour 0 of day D); D = 30 means the mirror all game (noise check).
Rows are gapday_play rows (per-day snapshots and flows of both farms) plus 'D'.
"""
import sys, os, json, time, collections, base64, zlib
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.path.insert(0, '/home/user/kaggriculture/gold/elite'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HYB = os.environ.get('HYB_DIR', os.path.join(os.environ.get('TEMP', '.'), 'gd_hyb'))


def hybrid_cfg(D):
    cfg = json.load(open('/home/user/kaggriculture/gold/top10/full/cfg_m5.json'))
    sf8 = {"sells_first": True, "sells_first_chassis": True, "sells_first_slots": True, "sells_first_sort": True,
           "cash_guard_min": 5, "v233_wool_first": True,
           "div_over": {"mkt_dp_d29": True, "final_sell0": 0, "final_cap": 21, "mkt_dp_cap": 30}}
    for k, v in sf8.items():
        if k == 'div_over': cfg['div_over'].update(v)
        else: cfg[k] = v
    cfg.update(cfg.pop('div_over'))  # the rival is an elite: divergent-path settings apply
    cfg.update(dict(start=24 * D, start_div=None, start_div2=None, div_over={}, rich_start=None, rich_steps=[],
                    herd_rich_margin=None, rich_tom_min=0, rich_tom_dem=0, rich_car_min=0,
                    sells_first_chassis=False, chassis_unit_floor=0.0, cash_guard_min=0, s2t_days=[], v219x=False,
                    v233_wool_first=False))
    return cfg


def build_hybrid(d, ref, ctl_path, D, slack_min=20):
    from build_elite import RUNTIME
    s = ref['seat']
    os.makedirs(HYB, exist_ok=True)
    out = os.path.join(HYB, 'hyb_%d_%d_d%d.py' % (ref['gid'], s, D))
    acts = d['acts']; units = []
    for t in range(720):
        a = acts[t + 1][s] if t + 1 < len(acts) else None
        units.append([a.get('farmer') or ['PASS'], a.get('hands') or []] if isinstance(a, dict) else [['PASS'], []])
    orders = {str(t): [[op, item, q] for op, item, q in lst] for t, lst in ref['outcomes'].items()}
    blob = base64.b64encode(zlib.compress(json.dumps(dict(units=units, orders=orders, hands=ref['hands'], money=ref['money'],
                                                          slack_min=slack_min), separators=(',', ':')).encode('utf-8'), 9)).decode('ascii')
    src = '"""hybrid mirror %s %s seat %d, controller from day %d"""\n_BLOB = "%s"\n' % (ref['team'], ref['gid'], s, D, blob) + RUNTIME
    if D < 30:
        ctl = open(ctl_path, encoding='utf-8').read()
        ctl = ctl.replace('_GC_CROPS = {', 'GC_P.update(%r)\n_GC_CROPS = {' % (hybrid_cfg(D),), 1)
        src = src.rstrip('\n') + '\n\n' + ctl
    open(out, 'w', encoding='utf-8').write(src)
    return out


def _job(t):
    import gapday_play
    d, ref, ctl_path, D = t
    hyb = build_hybrid(d, ref, ctl_path, D)
    x = gapday_play._play((d, ref, hyb))
    x['D'] = D
    try: os.remove(hyb)
    except OSError: pass
    return x


if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, ctl_path, D, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
    per = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
    teams = sys.argv[7] if len(sys.argv) > 7 else 'ALL'
    R = [json.loads(l) for l in open(refs, encoding='utf-8')]
    cnt = collections.Counter(); sel = []
    for r in R:
        if teams != 'ALL' and r['team'] not in teams.split(','): continue
        if cnt[r['team']] >= per: continue
        cnt[r['team']] += 1; sel.append(r)
    del R
    want = {r['gid'] for r in sel}
    games = {g['id']: g for g in load_games(path) if g['id'] in want}
    jobs = [(games[r['gid']], r, ctl_path, D) for r in sel]
    print(len(jobs), 'seats', dict(cnt), 'D', D, flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for i, x in enumerate(ex.map(_job, jobs)):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
            print(i, x['team'], x['gid'], x['seat'], 'm', x['m'], 'wall', x['wall'], 'T', round(time.time() - t0), flush=True)
