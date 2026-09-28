"""Hire-search logs on pinned live games: pinned4.job with the hirelog research build, one log per game.
usage: live_hl.py corpus.json S cand.py out.jsonl gid,gid,...     (env NPROC; team offhand)"""
import sys, os, json, tempfile
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from concurrent.futures import ProcessPoolExecutor


def job(t):
    import pinned4
    fd, p = tempfile.mkstemp(suffix='.jsonl'); os.close(fd)
    os.environ['LAB_HIRELOG'] = p
    try:
        row = pinned4.job(t)
        row['hirelog'] = [json.loads(l) for l in open(p)]
    finally:
        os.remove(p)
    return row


if __name__ == '__main__':
    corpus, S, cand, out, gids = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
    want = set(int(x) for x in gids.split(','))
    split = corpus + '.d'
    jobs = []
    for i, d in enumerate(json.load(open(corpus, encoding='utf-8'))):
        if d['id'] in want:
            one = os.path.join(split, '%d.json' % i)
            if not os.path.exists(one):
                os.makedirs(split, exist_ok=True); json.dump([d], open(one, 'w', encoding='utf-8'))
            jobs.append((one, 0, 'offhand', cand, S))
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
    print('done', len(jobs))
