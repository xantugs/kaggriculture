"""search_open.py base_cfg.json hours [parallel=2] : local search over the opening-controller knobs, scored by REACTING
self-play (batch4.py, both seats): 40 games vs T8 (seeds 6200-6219), 40 vs omw_v15a and 40 vs pub_metav4v13 (6100-6119).
Score = mean margin over the three opponents; a proposal (1-2 knob changes on the champion) is accepted when its score beats the
champion's by more than 100 and it does not lose more than 2 wins of 120. Everything is logged to search_log.jsonl; the champion
config is copied to cfg_best.json after every acceptance. Candidates are built with mk.py as full_OP_s###.py."""
import sys, os, json, time, random, subprocess, shutil, statistics as st
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
PY = sys.executable
MK = os.path.join(HERE, 'mk.py')
BATCH = os.path.join(KG, 'gold', 'harness', 'batch4.py')
OPPS = [('T8', os.path.join(KG, 'gold', 'submit', 'main_ctl_T8.py'), '6200-6259'),
        ('omw', os.path.join(KG, 'arena', 'cand', 'omw_v15a.py'), '6100-6119'),
        ('pub', os.path.join(KG, 'arena', 'cand', 'pub_metav4v13.py'), '6100-6119')]
LOG = os.path.join(HERE, 'search_log.jsonl')
OUT = os.path.join(HERE, 'search_out')
os.makedirs(OUT, exist_ok=True)

C3S2 = {"COW": ["milk", {"0": 3, "3": [4, 4.6], "4": [4, 5.6], "5": [4, 6.5], "6": [5, 6.5, 9], "7": [6, 7, 10], "8": [6.5, 7.5, 10.5]}],
        "SHEEP": ["yarn", {"0": 2, "3": [2, 3], "4": [2.4, 4], "5": [2.4, 5], "6": [2.4, 6.5, 8.5], "7": [2.9, 7.5, 9.5], "8": [4, 10, 12], "9": [5.5, 10, 14]}],
        "GOOSE": ["egg", {"2": 2, "4": [2.2, 2.8], "6": [3, 4, 6.5], "7": [3.3, 4.4, 7], "9": [5, 6, 8]}]}
C2S2 = json.loads(json.dumps(C3S2)); C2S2["COW"][1]["0"] = 2
C2S3 = json.loads(json.dumps(C2S2)); C2S3["SHEEP"][1] = {"0": 3, "3": [3, 3], "4": [3, 4], "5": [3, 5], "6": [3, 6.5, 8.5], "7": [3, 7.5, 9.5], "8": [4, 10, 12], "9": [5.5, 10, 14]}
C3S2G = json.loads(json.dumps(C3S2)); C3S2G["GOOSE"][1] = {"1": 1, "2": 2, "4": [3, 3.5], "6": [4, 5, 7], "7": [4.5, 5.5, 8], "9": [6, 7, 9]}
OVER = {"plant_must": False, "max_hands": 11, "hire_cost_w": 1.0, "prem_drop": True, "prem_drop_max": 6, "deliver_prem": 800.0, "hire_compact": False, "max_sell0": 10, "fert_keep": 0}
def over(**kw):
    d = dict(OVER); d.update(kw); return d
CREW = {"a": 3.3, "tiles": 0.045, "anim": 0.18, "shed": 0.38, "plant": 0.13, "lo": 4, "hi": 11, "below": 0, "cap": 0}
def crew(**kw):
    d = dict(CREW); d.update(kw); return d

# knob -> alternatives (the first is the cfg_e value where it matters)
SPACE = {
    "portfolio": [{"melon": 10, "melon0": 7, "wheat0": 13}, {"melon": 12, "melon0": 9, "wheat0": 4}, {"melon": 12, "melon0": 12, "wheat0": 8},
                  {"melon": 8, "melon0": 8, "wheat0": 10}, {"melon": 10, "melon0": 10, "wheat0": 6}],
    "anim_cond": [C3S2, C2S2, C2S3, C3S2G],
    "abs_last": [3, 5, 8],
    "crew": [CREW, crew(a=2.5, hi=10), crew(hi=9), crew(cap=2), crew(a=3.8, hi=11), crew(lo=3)],
    "land": [{"NE": 6, "SW": 8}, {"NE": 6, "SW": 9}, {"NE": 5, "SW": 8}, {"NE": 7, "SW": 11}, {"NE": 6, "SW": 8, "SE": 12}],
    "straw_hf": [{"early": {"4": 3, "5": 5}, "ne": [8, 7], "sw": [9, 6, -0.25]},
                 {"early": {"3": 2, "4": 4, "5": 6}, "ne": [8, 7], "sw": [9, 6, -0.25]},
                 {"early": {"4": 3, "5": 5}, "ne": [6, 5], "sw": [6, 5, -0.25]},
                 {"early": {"4": 3, "5": 5}, "ne": [10, 8], "sw": [9, 6, -0.25], "late": [0, 5, 9]},
                 {"early": {"5": 2}, "ne": [8, 7], "sw": [9, 6, -0.25]}],
    "straw_max": [36, 30, 42],
    "liq_days": [[6, 8, 9], [6, 7, 8, 9, 10, 11], []],
    "mid_wheat_from": [8, 1, 99],
    "anim_order": [["SHEEP", "COW", "GOOSE"], ["COW", "SHEEP", "GOOSE"], ["GOOSE", "SHEEP", "COW"]],
    "anim_day_max": [3, 2, 5],
    "hires0": [5, 4, 6],
    "cash_keep": [20, 60, 140],
    "feed_buy_hour": [14, 10, 18],
    "anim_split": [{"budget": 8, "last": 5}, {"budget": 8, "last": 8}, None],
    "melon_fert": [None, [6, 7]],
    "sell_on_drop": [False, True],
    "over": [OVER, over(max_hands=10), over(max_hands=12), over(deliver_prem=400.0), over(prem_drop=False)],
    "herd_cap": [20, 16, 24],
    "land_wheat": [15, 8, 20],
    "eh_all": [True, False],
    "access_free": [False, True],
    "anim_place_order": [None, ["SHEEP", "COW", "GOOSE"], ["COW", "SHEEP", "GOOSE"]],
}
FLAT = {"portfolio"}   # keys whose alternative is a dict of several top-level knobs


def apply(cfg, knob, alt):
    c = json.loads(json.dumps(cfg))
    if knob in FLAT:
        c.update(alt)
    elif alt is None:
        c.pop(knob, None)
    else:
        c[knob] = alt
    return c


def build(name, cfg):
    r = subprocess.run([PY, MK, name, os.path.join(HERE, 'cfg_e.json'), json.dumps(cfg), json.dumps({"care_eve_fix": True})],
                       capture_output=True, text=True, cwd=KG)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-400:])
    return os.path.join(KG, 'gold', 'top10', 'cands', 'full_OP_%s.py' % name)


def run_opp(cand, tag, opp_path, seeds, name):
    out = os.path.join(OUT, '%s_%s.jsonl' % (name, tag))
    env = dict(os.environ, NPROC=('4' if tag == 'T8' else '1'), PYTHONIOENCODING='utf-8')
    subprocess.run([PY, BATCH, cand, opp_path, seeds, out, '01'], capture_output=True, text=True, cwd=KG, env=env, timeout=3600)
    rows = []
    if os.path.exists(out):
        for l in open(out, encoding='utf-8'):
            if l.startswith('{'):
                try:
                    r = json.loads(l)
                    if r.get('m') is not None: rows.append(r)
                except Exception:
                    pass
    return tag, rows


def evaluate(cand, name):
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(lambda o: run_opp(cand, o[0], o[1], o[2], name), OPPS))
    per = {}
    for tag, rows in res:
        if not rows:
            per[tag] = dict(n=0, wins=0, margin=-99999.0)
            continue
        per[tag] = dict(n=len(rows), wins=sum(r['m'] > 0 for r in rows), margin=st.mean(r['m'] for r in rows),
                        errs=sum(1 for r in rows if r.get('err') and any(r['err'])))
    score = st.mean(per[t]['margin'] for t in per)
    wins = sum(per[t]['wins'] for t in per)
    n = sum(per[t]['n'] for t in per)
    return score, wins, n, per


def main():
    base_cfg = json.load(open(sys.argv[1], encoding='utf-8'))
    hours = float(sys.argv[2]); par = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    t_end = time.time() + hours * 3600
    rnd = random.Random(int(time.time()) % 100000)
    champ = base_cfg
    log = open(LOG, 'a', encoding='utf-8')
    k = int(sys.argv[4]) if len(sys.argv) > 4 else 0   # continue the candidate numbering
    cand = build('s000', champ)
    score, wins, n, per = evaluate(cand, 's000')
    best = dict(name='s000', score=score, wins=wins, n=n, per=per)
    log.write(json.dumps(dict(name='s000', cfg=champ, score=score, wins=wins, n=n, per=per, accepted=True, base=True)) + '\n'); log.flush()
    print('base s000 score %+.0f wins %d/%d %s' % (score, wins, n, {t: (v['wins'], round(v['margin'])) for t, v in per.items()}), flush=True)
    json.dump(champ, open(os.path.join(HERE, 'cfg_best.json'), 'w', encoding='utf-8'))
    while time.time() < t_end:
        props = []
        for _ in range(par):
            k += 1
            knobs = rnd.sample(sorted(SPACE), rnd.choice([1, 1, 2]))
            cfg = champ; desc = []
            for kn in knobs:
                alts = SPACE[kn]
                alt = rnd.choice(alts)
                cfg = apply(cfg, kn, alt); desc.append('%s=%s' % (kn, json.dumps(alt)[:60]))
            name = 's%03d' % k
            if json.dumps(cfg, sort_keys=True) == json.dumps(champ, sort_keys=True):
                continue   # a no-op proposal (the alternative equals the champion's value)
            try:
                path = build(name, cfg)
            except Exception as e:
                log.write(json.dumps(dict(name=name, error=str(e)[:200], desc=desc)) + '\n'); log.flush(); continue
            props.append((name, cfg, path, desc))
        with ThreadPoolExecutor(len(props) or 1) as ex:
            results = list(ex.map(lambda p: (p, evaluate(p[2], p[0])), props))
        for (name, cfg, path, desc), (score, wins, n, per) in results:
            # acceptance: the reacting T8 margin is the objective (the public agents are already won ~100%); the public
            # blocks may not lose wins
            t8_new = per.get('T8', {}).get('margin', -99999.0); t8_best = best['per'].get('T8', {}).get('margin', -99999.0)
            pub_new = per.get('omw', {}).get('wins', 0) + per.get('pub', {}).get('wins', 0)
            pub_best = best['per'].get('omw', {}).get('wins', 0) + best['per'].get('pub', {}).get('wins', 0)
            acc = n >= 180 and t8_new > t8_best + 400 and pub_new >= pub_best - 1 and per.get('T8', {}).get('wins', 0) >= best['per'].get('T8', {}).get('wins', 0) - 2
            log.write(json.dumps(dict(name=name, cfg=cfg, desc=desc, score=score, wins=wins, n=n, per=per, accepted=acc, champ=best['name'])) + '\n'); log.flush()
            print('%s %s score %+.0f wins %d/%d %s %s' % (name, ' '.join(desc), score, wins, n, {t: (v['wins'], round(v['margin'])) for t, v in per.items()}, 'ACCEPT' if acc else ''), flush=True)
            if acc:
                champ = cfg; best = dict(name=name, score=score, wins=wins, n=n, per=per)
                json.dump(champ, open(os.path.join(HERE, 'cfg_best.json'), 'w', encoding='utf-8'))
                shutil.copy(path, os.path.join(KG, 'gold', 'top10', 'cands', 'full_OP_best.py'))
    print('done; champion %s score %+.0f wins %d' % (best['name'], best['score'], best['wins']), flush=True)


if __name__ == '__main__':
    main()
