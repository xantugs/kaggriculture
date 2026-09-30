"""crawl_rated.py OUT_DIR MIN_SCORE SINCE_ISO [MAX_SUBS] : crawl the ladder outward from our own submissions.
1. ListEpisodes for our submissions -> the opponents' submission ids and ratings.
2. ListEpisodes for every opponent submission whose rating is >= MIN_SCORE (then one more hop over the rated teams met
   in those games), up to MAX_SUBS submissions.
3. Every COMPLETED public episode that ended at or after SINCE_ISO with at least one agent rated >= MIN_SCORE at game time
   is recorded in OUT_DIR/episodes.jsonl (id, endTime, agents: submissionId, teamId, team, index, initialScore, reward).
4. The replays of those episodes are fetched (public replay endpoint, 8 threads, resumable) into OUT_DIR/games.jsonl in the
   compact form the gates use, each with meta.agents.
"""
import sys, os, json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'moon'))
import elite_fetch
URL = 'https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes'
OURS = [56697382, 56697385, 56681632, 56663285, 56663295, 56638568, 56651672, 56661347, 56661351]


def post(body):
    err = None
    for k in range(5):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST')
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            err = e; time.sleep(3 + 4 * k)
    print('ListEpisodes failed', body, repr(err)[:100], flush=True)
    return None


def main():
    out, min_score, since = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    max_subs = int(sys.argv[4]) if len(sys.argv) > 4 else 500
    os.makedirs(out, exist_ok=True)
    ep_path, gm_path, sub_path = out + '/episodes.jsonl', out + '/games.jsonl', out + '/subs.json'
    episodes = {}
    if os.path.exists(ep_path):
        for l in open(ep_path, encoding='utf-8'):
            e = json.loads(l); episodes[e['id']] = e
    seen_subs = set(json.load(open(sub_path))) if os.path.exists(sub_path) else set()
    teams = {}
    # subs to visit: ours first, then rated opponents (rating = the latest score seen for that submission)
    queue = list(OURS); rating = {}
    hops = 0
    while queue and len(seen_subs) < max_subs:
        sub = queue.pop(0)
        if sub in seen_subs: continue
        seen_subs.add(sub)
        d = post({'submissionId': sub})
        time.sleep(0.7)
        if not d: continue
        for t in d.get('teams') or []: teams[t['id']] = t.get('teamName')
        for e in d.get('episodes') or []:
            ag = e.get('agents') or []
            if e.get('state') != 'COMPLETED' or len(ag) != 2: continue
            for a in ag:
                s = a.get('updatedScore') or a.get('initialScore') or 0
                sid = a.get('submissionId')
                if sid and s >= min_score and sid not in seen_subs and sid not in queue:
                    queue.append(sid)
                rating[sid] = max(rating.get(sid, 0), s)
            if (e.get('endTime') or '') < since: continue
            if not any((a.get('initialScore') or 0) >= min_score for a in ag): continue
            episodes[e['id']] = dict(id=e['id'], end=e.get('endTime'), agents=[dict(submissionId=a.get('submissionId'), teamId=a.get('teamId'),
                                      team=teams.get(a.get('teamId')), index=a.get('index', 0) or 0, score=a.get('initialScore'), after=a.get('updatedScore'),
                                      reward=a.get('reward')) for a in ag])
        hops += 1
        if hops % 10 == 0:
            with open(ep_path, 'w', encoding='utf-8') as fh:
                for e in episodes.values(): fh.write(json.dumps(e, ensure_ascii=False) + '\n')
            json.dump(sorted(seen_subs), open(sub_path, 'w'))
            print(time.strftime('%H:%M'), 'subs visited', len(seen_subs), 'queue', len(queue), 'episodes', len(episodes), flush=True)
    with open(ep_path, 'w', encoding='utf-8') as fh:
        for e in episodes.values(): fh.write(json.dumps(e, ensure_ascii=False) + '\n')
    json.dump(sorted(seen_subs), open(sub_path, 'w'))
    print(time.strftime('%H:%M'), 'LIST DONE: subs', len(seen_subs), 'episodes', len(episodes), flush=True)
    # fetch replays (resumable; episodes already in the fresh29 corpus are skipped by the gate builder, not here)
    have = set()
    if os.path.exists(gm_path):
        for l in open(gm_path, encoding='utf-8'):
            try: have.add(json.loads(l)['id'])
            except Exception: pass
    todo = [e for e in sorted(episodes.values(), key=lambda e: e['end'] or '', reverse=True) if e['id'] not in have]
    print('fetching', len(todo), 'replays', flush=True)
    n = 0; t0 = time.time()
    with ThreadPoolExecutor(8) as ex, open(gm_path, 'a', encoding='utf-8') as fh:
        for e, rec in zip(todo, ex.map(lambda e: elite_fetch.get(e['id']), todo)):
            if not rec: continue
            rec['meta'] = dict(end=e['end'], agents=e['agents'])
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n'); fh.flush(); n += 1
            if n % 100 == 0: print(time.strftime('%H:%M'), 'fetched', n, '/', len(todo), '%.0f s' % (time.time() - t0), flush=True)
    print(time.strftime('%H:%M'), 'FETCH DONE', n, flush=True)


if __name__ == '__main__':
    main()
