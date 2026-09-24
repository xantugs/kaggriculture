"""List a team's episodes via EpisodeService and fetch the ones against given opponents in compact form.
usage: ourgames.py list sub1,sub2 out_eps.json | fetch ids.json out.json opp1|opp2..."""
import sys, os, json, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
def post(body):
    for k in range(6):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST')
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except urllib.error.HTTPError:
            raise
        except Exception as e:
            print('retry', k, repr(e)[:80], flush=True); time.sleep(5 + 5 * k)
    raise RuntimeError('ListEpisodes failed')
if __name__ == '__main__':
    if sys.argv[1] == 'list':
        subs, out = [int(x) for x in sys.argv[2].split(',')], sys.argv[3]
        eps = {}
        for sub in subs:
            d = post({'submissionId': sub})
            names = {t['id']: t.get('teamName') for t in d.get('teams') or []}
            for e in d.get('episodes') or []:
                ag = e.get('agents') or []
                if len(ag) != 2: continue
                eps[e['id']] = dict(id=e['id'], t=e.get('endTime'), teams=[names.get(a.get('teamId')) for a in ag],
                                    sub=[a.get('submissionId') for a in ag], r=[a.get('reward') for a in ag],
                                    score=[a.get('initialScore') for a in ag])
            print('sub', sub, 'episodes', len(d.get('episodes') or []), flush=True)
        json.dump(list(eps.values()), open(out, 'w', encoding='utf-8'), ensure_ascii=False)
        print('total', len(eps))
    elif sys.argv[1] == 'fetch':
        import elite_fetch
        eps = json.load(open(sys.argv[2], encoding='utf-8')); opps = sys.argv[4].split('|')
        def strong(e):
            if 'offhand' not in e['teams']: return False
            o = 1 - e['teams'].index('offhand')
            return e['teams'][o] in opps or (opps[0].startswith('>=') and (e['score'][o] or 0) >= float(opps[0][2:]))
        want = [e for e in eps if strong(e)]
        print('fetching', len(want), flush=True)
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(4) as ex:
            games = [g for g in ex.map(elite_fetch.get, [e['id'] for e in want]) if g]
        json.dump(games, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False)
        print('saved', len(games))
