import json, os, urllib.request, zipfile, io, csv, collections
tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
req = urllib.request.Request('https://www.kaggle.com/api/v1/competitions/kaggriculture/leaderboard/download', headers={'Authorization': 'Bearer ' + tok})
z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=120).read()))
rows = list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8')))
rank = {r['TeamName']: (i + 1, float(r['Score'])) for i, r in enumerate(rows)}
cls = json.load(open('gameclass.json'))
by = collections.defaultdict(lambda: [0, 0, 0, 0])  # games, wins, mirror, mirror wins
for f in json.load(open('g2800_list.json')):
    d = json.load(open(f, encoding='utf-8'))[0]
    n = d['info']['TeamNames']; P = n.index('offhand'); opp = n[1 - P]
    win = d['rewards'][P] > d['rewards'][1 - P]; mir = cls.get(str(d['id']), 0) >= 0.8
    b = by[opp]; b[0] += 1; b[1] += win; b[2] += mir; b[3] += win and mir
tiers = collections.defaultdict(lambda: [0, 0, 0, 0])
for opp, b in by.items():
    r = rank.get(opp, (999, 0))[0]
    t = 'top10' if r <= 10 else 'top30' if r <= 30 else 'top60' if r <= 60 else 'top120' if r <= 120 else 'rest'
    for i in range(4): tiers[t][i] += b[i]
for t in ('top10', 'top30', 'top60', 'top120', 'rest'):
    g, w, m, mw = tiers[t]
    print(f'{t:7s} games {g:3d} wins {w:3d}  mirror {m:3d} (wins {mw})  divergent {g - m:3d} (wins {w - mw})')
print('top-30 teams we met:', sorted(((rank.get(o, (999,))[0], o, by[o][:2]) for o in by if rank.get(o, (999,))[0] <= 30)))
