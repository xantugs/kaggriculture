"""crawl_sample.py CRAWL_DIR PER_BAND OUT_GAMES : pick a stratified sample of crawled episodes (per 100-rating band of the
rated seat, newest first, at most 6 seats per team per band, one seat per episode) and fetch their replays (8 threads,
resumable) into OUT_GAMES in the compact form with meta.agents. Episodes already in moon/elite/games_2026-09-29.jsonl are
copied from there instead of fetched."""
import sys, os, json, time, collections, random
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'moon'))
import elite_fetch
OUR_SUBS = {56697382, 56697385, 56681632, 56663285, 56663295, 56638568, 56651672, 56661347, 56661351}
crawl, per_band, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
eps = [json.loads(l) for l in open(crawl + '/episodes.jsonl', encoding='utf-8')]
print('episodes listed', len(eps))
cands = collections.defaultdict(list)   # band -> [(end, episode, seat)]
for e in eps:
    ag = sorted(e['agents'], key=lambda a: a.get('index', 0))
    if len(ag) != 2: continue
    for a in ag:
        if a.get('submissionId') in OUR_SUBS or (a.get('team') or '') == 'offhand': continue
        s = a.get('score') or 0
        if s >= 2400: cands[int(s // 100) * 100].append((e['end'] or '', e, a.get('index', 0) or 0, a.get('team')))
chosen = {}
for band, lst in sorted(cands.items()):
    lst.sort(key=lambda x: x[0], reverse=True)
    rnd = random.Random(band); rnd.shuffle(lst)   # random within the band (all are 29-30 Sep)
    per_team = collections.Counter(); n = 0
    for end, e, s, team in lst:
        if e['id'] in chosen or per_team[team] >= 6: continue
        per_team[team] += 1; chosen[e['id']] = e; n += 1
        if n >= per_band: break
    print('band', band, 'candidates', len(lst), 'chosen', n, 'teams', len(per_team))
have = {}
for src in ('moon/elite/games_2026-09-29.jsonl',):
    if os.path.exists(src):
        for l in open(src, encoding='utf-8'):
            try: g = json.loads(l); have[g['id']] = g
            except Exception: pass
done = set()
if os.path.exists(out):
    for l in open(out, encoding='utf-8'):
        try: done.add(json.loads(l)['id'])
        except Exception: pass
todo = [e for e in chosen.values() if e['id'] not in done]
print('to obtain', len(todo), 'of which cached', sum(1 for e in todo if e['id'] in have), flush=True)
t0 = time.time(); n = 0
with open(out, 'a', encoding='utf-8') as fh:
    fetch = [e for e in todo if e['id'] not in have]
    for e in todo:
        if e['id'] in have:
            rec = dict(have[e['id']]); rec['meta'] = dict(end=e['end'], agents=e['agents']); fh.write(json.dumps(rec, ensure_ascii=False) + '\n'); n += 1
    fh.flush()
    with ThreadPoolExecutor(8) as ex:
        for e, rec in zip(fetch, ex.map(lambda e: elite_fetch.get(e['id']), fetch)):
            if not rec: continue
            rec['meta'] = dict(end=e['end'], agents=e['agents'])
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n'); fh.flush(); n += 1
            if n % 100 == 0: print(time.strftime('%H:%M'), 'obtained', n, '/', len(todo), '%.0f s' % (time.time() - t0), flush=True)
print(time.strftime('%H:%M'), 'SAMPLE DONE', n, flush=True)
