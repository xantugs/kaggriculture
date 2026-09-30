"""rated_gate_build.py OUTNAME MIN_SCORE CAP_PER_TEAM SOURCE... : a replay gate of RATED rival seats from crawled or live game
files (compact games with meta). Sources: gold/top10/gates/crawl/games.jsonl (meta.agents with score at game time) and our
live_*.jsonl files (meta.opp_before = the opponent's rating; the rival is the opponent's seat). Every seat rated >= MIN_SCORE
at game time that is not one of our own submissions becomes a ref (elite_gate._ref: the repaired recording in its own town),
at most CAP_PER_TEAM seats per team per 100-rating band. Writes gates/OUTNAME_games.jsonl.gz + OUTNAME_refs.jsonl; each ref
carries rating, band, opp_rating, end (UTC time) and src."""
import sys, os, json, gzip, collections, time
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
import elite_gate
OUR_SUBS = {56697382, 56697385, 56681632, 56663285, 56663295, 56638568, 56651672, 56661347, 56661351, 56622850, 56607659, 56603319, 56600788}


def seats(g, min_score):
    """(seat, rating, opp_rating, end, team) for every rated non-offhand seat of a compact game."""
    m = g.get('meta') or {}
    out = []
    if 'agents' in m:   # crawled
        ag = sorted(m['agents'], key=lambda a: a.get('index', 0))
        if len(ag) != 2: return out
        for a in ag:
            s = a.get('index', 0) or 0; o = ag[1 - s]
            if a.get('submissionId') in OUR_SUBS or (g['info']['TeamNames'][s] or '') == 'offhand': continue
            if (a.get('score') or 0) >= min_score:
                out.append((s, a['score'], o.get('score'), m.get('end'), g['info']['TeamNames'][s]))
    elif 'opp_before' in m:   # our live games: the rival is the opponent's seat
        s = 1 - m['seat']
        if (m.get('opp_before') or 0) >= min_score and (m.get('opp') or '') != 'offhand':
            out.append((s, m['opp_before'], m.get('our_before'), m.get('end'), g['info']['TeamNames'][s]))
    return out


if __name__ == '__main__':
    name, min_score, cap = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]); sources = sys.argv[4:]
    cnt = collections.Counter(); jobs = []; keep = {}; extra = {}
    seen = set()
    for src in sources:
        for l in open(src, encoding='utf-8'):
            if not l.startswith('{'): continue
            try: g = json.loads(l)
            except Exception: continue
            if g['id'] in seen: continue
            seen.add(g['id'])
            if len(g.get('acts') or []) != 720 or not g.get('rewards') or None in g['rewards']: continue
            if not all(st == 'DONE' for st in (g.get('statuses') or [])): continue
            for s, rating, opp_rating, end, team in seats(g, min_score):
                band = int(rating // 100) * 100
                if cnt[(team, band)] >= cap: continue
                cnt[(team, band)] += 1
                jobs.append((g, s)); keep[g['id']] = g
                extra[(g['id'], s)] = dict(rating=rating, band=band, opp_rating=opp_rating, end=end, src=os.path.basename(src))
    bands = collections.Counter(e['band'] for e in extra.values())
    print(len(jobs), 'seats from', len(keep), 'games | bands', dict(sorted(bands.items())), '| teams', len({t for t, b in cnt}), flush=True)
    with gzip.open('gold/top10/gates/%s_games.jsonl.gz' % name, 'wt', encoding='utf-8') as fh:
        for g in keep.values():
            g2 = dict(g); g2.pop('meta', None); fh.write(json.dumps(g2, ensure_ascii=False) + '\n')
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '12'))) as ex, open('gold/top10/gates/%s_refs.jsonl' % name, 'w', encoding='utf-8') as fh:
        for (g, s), r in zip(jobs, ex.map(elite_gate._ref, jobs, chunksize=4)):
            r.update(extra[(g['id'], s)])
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush(); n += 1
            if n % 200 == 0: print(n, 'refs', int(time.time() - t0), 's', flush=True)
    print('done', n, 'refs', int(time.time() - t0), 's', flush=True)
