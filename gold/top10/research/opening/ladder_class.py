"""ladder_class.py FILE.jsonl LABEL : router class of the rival in each fetched ladder game of LABEL (replays the two recorded
first steps to read the rival's money and hands at step 1; thresholds of ctl_op._opr_class with fine=True, chassis_min 2550),
then wins and margins by class."""
import sys, os, json, collections, statistics as st
sys.path.insert(0, os.path.join(os.getcwd(), 'arena'))
import lean
fn, label = sys.argv[1], sys.argv[2]
def cls_of(m, h):
    if h == 0 and m >= 2550: return 'chassis'
    if h == 0 and (540 <= m <= 720 or 940 <= m <= 980 or 2440 <= m <= 2480): return 'C2S3'
    if h >= 4 and m < 300: return 'herdpoor'
    if (h == 5 and 2200 <= m <= 2500) or (3 <= h <= 5 and 300 <= m <= 1700): return 'herdfirst'
    if h == 5 and 1700 < m < 2200: return 'majkel'
    return 'other'
seen = {}
for l in open(fn, encoding='utf-8'):
    if not l.startswith('{'): continue
    r = json.loads(l)
    if r.get('meta', {}).get('label') == label and r['meta'].get('opp') != 'offhand':
        seen[r['id']] = r
out = []
for gid, r in sorted(seen.items()):
    s = r['meta']['seat']; acts = r['acts']; sig = {}
    def mk(seat):
        def a(obs, cfg=None):
            st_ = int(obs['step'])
            if st_ == 1 and seat == s:
                f = obs['farms'][1 - s]; sig['m'] = float(f['money']); sig['h'] = len(f['hands'])
            x = acts[st_ + 1][seat] if st_ + 1 < len(acts) and isinstance(acts[st_ + 1], list) and len(acts[st_ + 1]) > seat else None
            return x if isinstance(x, dict) else {'farmer': ['PASS'], 'hands': [], 'market': []}
        return a
    try:
        lean.play(None, None, int(r['info']['seed']), agent_objs=[mk(0), mk(1)], max_steps=2)
    except Exception as e:
        sig['err'] = repr(e)[:80]
    rw = r['rewards']; mg = rw[s] - rw[1 - s]
    c = cls_of(sig.get('m', -1), sig.get('h', -1)) if 'm' in sig else '?'
    out.append((gid, c, mg, r['meta'].get('opp_before') or 0, str(r['meta'].get('opp'))[:18], sig))
by = collections.defaultdict(list)
for gid, c, mg, ob, opp, sig in out: by[c].append((mg, ob, opp))
print('%s: %d ladder games' % (label, len(out)))
for c, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
    print('  %-9s n %3d  wins %3d  mean margin %+7.0f  mean opp rating %5.0f  losses: %s' % (c, len(v), sum(x[0] > 0 for x in v), st.mean(x[0] for x in v), st.mean(x[1] for x in v), ', '.join('%s(%.0f) %+.0f' % (x[2], x[1], x[0]) for x in v if x[0] < 0)))
