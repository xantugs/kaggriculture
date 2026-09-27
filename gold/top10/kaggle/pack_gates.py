"""Pack every gate's games into one zlib'd JSON blob for a private Kaggle dataset (gates.bin).
usage: pack_gates.py out_dir
Gates: live191, pin249 (pinned, our seat = offhand, S=288), s2800 (pinned, S=144), top10g / goldg / eg0920 (repaired elite
seats in their towns: games + refs)."""
import sys, os, json, gzip, zlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
G = os.path.join(ROOT, 'gold', 'top10', 'gates')


def jl(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as fh:
        return [json.loads(l) for l in fh if l.strip()]


out = sys.argv[1]
os.makedirs(out, exist_ok=True)
data = {'pinned': {}, 'elite': {}}
data['pinned']['live191'] = dict(S=288, games=json.load(open(os.path.join(G, 'live191.json'), encoding='utf-8')))
data['pinned']['pin249'] = dict(S=288, games=json.load(open(os.path.join(G, 'pin249.json'), encoding='utf-8')))
s2800 = []
for f in ('strong2800.json', 'strong_new.json'):
    s2800 += json.load(open(os.path.join(ROOT, 'moon', f), encoding='utf-8'))
data['pinned']['s2800'] = dict(S=144, games=[d for d in s2800 if 'offhand' in d['info']['TeamNames']])
for g in ('top10g', 'goldg'):
    data['elite'][g] = dict(games=jl(os.path.join(G, g + '_games.jsonl.gz')), refs=jl(os.path.join(G, g + '_refs.jsonl')))
refs = jl(os.path.join(ROOT, 'gold', 'elite', 'elite_gate_refs.jsonl'))
want = {r['gid'] for r in refs}
games = [d for d in jl(os.path.join(ROOT, 'moon', 'elite', 'games_2026-09-20.jsonl.gz')) if d['id'] in want]
data['elite']['eg0920'] = dict(games=games, refs=refs)
for k, v in data['pinned'].items():
    print('pinned', k, len(v['games']), 'S', v['S'])
for k, v in data['elite'].items():
    print('elite', k, len(v['games']), 'games', len(v['refs']), 'seats')
raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
blob = zlib.compress(raw, 9)
open(os.path.join(out, 'gates.bin'), 'wb').write(blob)
print('raw', len(raw), 'packed', len(blob))
