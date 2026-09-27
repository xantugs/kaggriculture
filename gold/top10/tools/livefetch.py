"""Incrementally fetch our own ladder games (compact form) for a fresh live gate.
usage: livefetch.py out.jsonl sub1,sub2,... [label1,label2,...] [loop_minutes]
Each line: the compact game (id, info{TeamNames, seed, EpisodeId}, rewards, statuses, acts) plus meta{sub, label, seat,
opp, opp_team_id, our_before, our_after, opp_before, opp_after, end}. Only COMPLETED episodes; already-fetched ids are
skipped. With loop_minutes the tool repeats forever (run it in the background)."""
import sys, os, json, time, urllib.request
sys.path.insert(0, '/home/user/kaggriculture/moon')
URL = 'https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes'


def post(body):
    for k in range(6):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST')
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            err = e; time.sleep(5 + 5 * k)
    raise err


def once(out, subs, labels):
    import elite_fetch
    have = set()
    if os.path.exists(out):
        for line in open(out, encoding='utf-8'):
            try: have.add(json.loads(line)['id'])
            except Exception: pass
    todo = []
    for sub, lab in zip(subs, labels):
        d = post({'submissionId': sub})
        teams = {t['id']: t.get('teamName') for t in d.get('teams') or []}
        for e in d.get('episodes') or []:
            ag = e.get('agents') or []
            if e.get('state') != 'COMPLETED' or len(ag) != 2 or e['id'] in have:
                continue
            me = [a for a in ag if a.get('submissionId') == sub]
            if not me:
                continue
            me = me[0]; op = [a for a in ag if a is not me][0]
            todo.append((e['id'], dict(sub=sub, label=lab, seat=me.get('index', 0) or 0, opp=teams.get(op.get('teamId')),
                                       opp_team_id=op.get('teamId'), our_before=me.get('initialScore'), our_after=me.get('updatedScore'),
                                       opp_before=op.get('initialScore'), opp_after=op.get('updatedScore'), end=e.get('endTime'))))
    n = 0
    with open(out, 'a', encoding='utf-8') as fh:
        for eid, meta in todo:
            rec = elite_fetch.get(eid)
            if not rec:
                continue
            rec['meta'] = meta
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n'); fh.flush(); n += 1
    print(time.strftime('%H:%M:%S'), 'fetched', n, 'new of', len(todo), 'total', len(have) + n, flush=True)


if __name__ == '__main__':
    out, subs = sys.argv[1], [int(x) for x in sys.argv[2].split(',')]
    labels = sys.argv[3].split(',') if len(sys.argv) > 3 else [str(s) for s in subs]
    loop = float(sys.argv[4]) if len(sys.argv) > 4 else 0
    while True:
        try:
            once(out, subs, labels)
        except Exception as e:
            print('error', repr(e)[:200], flush=True)
        if not loop:
            break
        time.sleep(loop * 60)
