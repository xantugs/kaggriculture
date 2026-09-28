"""Paired comparison of two pinned-gate row files (same gids): n, mean delta +- se, wins before -> after, flips,
split by takeover group (gc_start 288 rich / 384 divergent / 528 copy) and optionally restricted to a gid list.
usage: pcmp.py base.jsonl cand.jsonl [gids_file]"""
import sys, json, math


def load(p):
    out = {}
    for l in open(p, encoding='utf-8'):
        r = json.loads(l)
        if r.get('m') is not None:
            out[r['gid']] = r
    return out


def stat(pairs, label):
    if not pairs:
        print('%-10s n 0' % label); return
    d = [c['m'] - b['m'] for b, c in pairs]
    n = len(d); mu = sum(d) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in d) / max(1, n - 1)); se = sd / math.sqrt(n)
    wb = sum(b['m'] > 0 for b, c in pairs); wc = sum(c['m'] > 0 for b, c in pairs)
    up = sum(b['m'] <= 0 < c['m'] for b, c in pairs); dn = sum(c['m'] <= 0 < b['m'] for b, c in pairs)
    ch = sum(1 for x in d if x != 0)
    print('%-10s n %3d  delta %+7.0f +- %4.0f  wins %d -> %d  flips +%d -%d  changed %d' % (label, n, mu, se, wb, wc, up, dn, ch))


if __name__ == '__main__':
    B, C = load(sys.argv[1]), load(sys.argv[2])
    want = set(int(x) for x in open(sys.argv[3]).read().split()) if len(sys.argv) > 3 else None
    gids = [g for g in C if g in B and (want is None or g in want)]
    pairs = [(B[g], C[g]) for g in gids]
    stat(pairs, 'all')
    for st, nm in ((288, 'rich'), (384, 'div'), (528, 'copy')):
        stat([(b, c) for b, c in pairs if int(b['tel'].get('gc_start', 528)) == st], nm)
