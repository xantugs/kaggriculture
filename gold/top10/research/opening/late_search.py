"""late_search.py BASE.py [max_parallel=6] [names...] : single-change screen of late-game knobs on a tape build.
Each variant edits the base file's GC_P.update config line: top-level keys are appended at the end of the dict literal
(so they win over earlier duplicates), nested override dicts (div_over, rich_over, herd_rich_over) are edited in place
where the knob also lives there. Each candidate plays the base on seeds 6700-6719 (seat 0) and 6720-6739 (seat 1):
40 reacting games. Rows: research/opening/ls/<name>_{a,b}.jsonl; summary appended to ls/late_search_log.jsonl."""
import sys, os, json, re, ast, subprocess, time, statistics as st, collections
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
PY = sys.executable
OUT = os.path.join(HERE, 'ls'); os.makedirs(OUT, exist_ok=True)
BATCH = os.path.join(KG, 'gold', 'harness', 'batch4.py')

def top(**kw):
    return ('top', kw)
def nested(**kw):   # set in the top level and inside every override dict that already holds the key
    return ('nested', kw)

VARIANTS = {
    'arb':        [top(arb_on=True)],
    'arbc':       [top(arb_on=True, arb_chassis=True)],
    'herddeny':   [nested(herd_denial_w=1.0)],
    'herdsheep':  [nested(herd_kinds=['SHEEP', 'COW'], herd_total_max=10)],
    'herdbig':    [nested(herd_max=10, herd_total_max=10)],
    'wfert10':    [top(wheat_fert_gain=10.0, carrot_fert_gain=10.0)],
    'ferth0':     [top(fert_h0=True)],
    'fertidle':   [top(fert_idle=True)],
    'race':       [top(race_harvest=True)],
    'lateplan':   [top(late_plan=True, late_keep=True)],
    'digglut':    [top(dig_glut=True)],
    'dpper9':     [nested(mkt_dp_periods=9)],
    'dpcap30':    [top(mkt_dp_cap=30)],
    'animfwd1':   [nested(anim_fwd_days=1.0)],
    'animfwd2':   [nested(anim_fwd_days=2.0)],
    'tickdefer':  [top(tick_defer=True)],
    'slots1':     [top(sells_first_slots1=True)],
    'dpdue':      [top(sells_first_dp_due=True)],
    'lastplant':  [top(wheat_last_plant=26, carrot_last_plant=27)],
    'strawfc':    [top(straw_fc=True)],
    'strawfc19':  [nested(straw_fc_last=19)],
    'hands17':    [top(max_hands=17, max_hands_final=17)],
    'nofloor':    [top(unit_floor_frac=0.0, chassis_unit_floor=0.0)],
    'wfloor':     [top(sell_floor={'STRAWBERRY': 30, 'MILK': 25, 'WOOL': 60})],
    'start384':   [top(start=384)],
    'start288':   [top(start=288)],
    'lead2':      [top(lead2=True)],
    'start336':   [top(start=336)],
    'start360':   [top(start=360)],
    'start408':   [top(start=408)],
    'start432':   [top(start=432)],
    'start456':   [top(start=456)],
    'fs0_0':      [nested(final_sell0=0)],
    'fs0_6':      [nested(final_sell0=6)],
    'fcap17':     [nested(final_cap=17)],
    'fcap22':     [nested(final_cap=22)],
    'late28':     [top(late_sell0_day=28, late_sell0=3)],
    'fbyval':     [top(final_by_value=True)],
    'd28cap22':   [top(d28_cap=22)],
    'h0first':    [top(tick_defer0=True)],
}

def edit(src, ops):
    lines = src.split('\n')
    idx = [i for i, l in enumerate(lines) if l.startswith('GC_P.update({')]
    assert len(idx) == 1, len(idx)
    i = idx[0]; line = lines[i]
    d = ast.literal_eval(line[len('GC_P.update('):-1])
    for kind, kw in ops:
        for k, v in kw.items():
            if kind == 'nested':
                for sub in ('div_over', 'rich_over', 'herd_rich_over'):
                    if isinstance(d.get(sub), dict) and k in d[sub]:
                        d[sub][k] = v
            d.pop(k, None); d[k] = v        # re-insert last
    lines[i] = 'GC_P.update(' + repr(d) + ')'
    return '\n'.join(lines)

def build(base, name):
    src = open(base, encoding='utf-8').read()
    s = edit(src, VARIANTS[name])
    ast.parse(s)
    p = os.path.join(KG, 'gold', 'top10', 'cands', 'full_LS_%s.py' % name)
    open(p, 'w', encoding='utf-8').write(s)
    return p

def run(cand, base, name):
    outs = []
    procs = []
    for tag, seeds, seat in (('a', '6700-6719', '0'), ('b', '6720-6739', '1')):
        out = os.path.join(OUT, '%s_%s.jsonl' % (name, tag)); outs.append(out)
        if os.path.exists(out): os.remove(out)
        env = dict(os.environ, NPROC='1', PYTHONIOENCODING='utf-8')
        procs.append(subprocess.Popen([PY, BATCH, cand, base, seeds, out, seat], cwd=KG, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    for p in procs: p.wait()
    rows = []
    for out in outs:
        if os.path.exists(out):
            for l in open(out, encoding='utf-8'):
                if l.startswith('{'):
                    r = json.loads(l)
                    if r.get('m') is not None: rows.append(r)
    m = [r['m'] for r in rows]
    res = dict(name=name, n=len(m), wins=sum(x > 0 for x in m), losses=sum(x < 0 for x in m), mean=(st.mean(m) if m else None),
               se=(st.pstdev(m) / len(m) ** 0.5 if len(m) > 1 else None), errs=sum(1 for r in rows if r.get('err') and any(r['err'])),
               ops=repr(VARIANTS[name]), base=os.path.basename(base), t=time.strftime('%H:%M'))
    with open(os.path.join(OUT, 'late_search_log.jsonl'), 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(res) + '\n')
    print('%-10s n %2d  %2d-%2d  mean %+6.0f +- %4.0f  errs %d  (%s)' % (name, res['n'], res['wins'], res['losses'], res['mean'] or 0, res['se'] or 0, res['errs'], res['t']), flush=True)
    return res

if __name__ == '__main__':
    base = os.path.abspath(sys.argv[1]); par = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    names = sys.argv[3:] or list(VARIANTS)
    cands = [(n, build(base, n)) for n in names]
    print('built', len(cands), 'variants on', os.path.basename(base), flush=True)
    with ThreadPoolExecutor(par) as ex:
        list(ex.map(lambda nc: run(nc[1], base, nc[0]), cands))
    print('late search done', time.strftime('%H:%M'), flush=True)
