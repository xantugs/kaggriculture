"""pubpull.py: pull public Kaggriculture notebooks, extract their agent code into ../pubnb/<slug>.py, fingerprint steps 0-1."""
import sys, os, json, re, subprocess, urllib.request, time
KG = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
OUT = os.path.abspath(os.path.join(KG, '..', 'pubnb')); os.makedirs(OUT, exist_ok=True)
TOK = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
REFS = """ahmedberatozer/kaggriculture-v38-smarter-feed-stronger-margins ahmedberatozer/kaggriculture-v39-ready-before-the-rush
ahmedberatozer/kaggriculture-v34-observed-market-timing ahmedberatozer/kaggriculture-v53-opening-signature
ahmedberatozer/kaggriculture-v55-one-turn-market-race-edge ahmedberatozer/kaggriculture-v41-review-candidate
guruprasaathas111/kaggriculture-master-engine-v53e01d74d8f leoprovorov/kaggricult-man-reverse-engineering
ahmedberatozer/kaggriculture-v31-production-and-sale-priority arsgorynich/kaggriculture-v43-local-confirmed
ravi123a321at/177-180-fresh-top-30-v21-1-conditional-memory aurax7/kaggriculture-shop-router-reactive-v7
nathanjacob/kaggriculture-pipe-5-terminal-boost reyhanksatria/best-market-agent-high-strategy degnonguidi/kaggriculture-cloning-agent
web3cainiao/kaggriculture-v21-tactical-memory nathanjacob/kaggriculture-pipe-7-wheat-microstructure
prvsiyan/kaggriculture-frontier-the-moon-counts-melons guruprasaathas111/game-theoretic-master-discrete-optimization
ahmedberatozer/kaggriculture-v49-funded-sale-timing-and-worker boatlee/v16-rc5-high-score-8c-4s-premium-market-lead
kaitofukami/25-27-strict-future-v27-midgame-meta-reset raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta
boatlee/84-84-base-public-holdout-v14-clone-preemption thomastschinkel/the-2945-farm-96-vs-the-top-10-public-bots
tetsutani/adaptive-farming-strategy-for-kaggriculture kaitofukami/40-40-early-floor-39-46-top-10-v48-fast-routes
yhay81/shop-router-0909 yhay81/six-day-public-state-fieldbook romantamrazov/kaggriculture-hamburger
tetsutani/shape-the-shop-work-the-pasture-kaggriculture yhay81/three-day-shop-router guruprasaathas111/kaggriculture-master-engine-v3
tetsutani/demand-preserving-turn-sale-timing flexonafft/kaggriculture-multi-route-farming-agent
leoprovorov/a-song-of-ice-and-fire-fixed-flexible leoprovorov/god-s-mode-hacked-stores haodou092/kaggriculture-harvest-ledger
haideptry/the-2965-master-hybrid-engine georgymamarin/kaggriculture-what-2600-farms-do-differently
guruprasaathas111/kaggriculture-top-2-master-engine-v4 leoprovorov/2965-master-engine haideptry/the-shepherds-ledger-herd-safe-sovereign
evgendvorkin/kaggriculture-version-31-26-09-bronze-going-up kunaldesale2408/kaggriculture-ttv1 lynnsakurai/farmer-john-and-the-idle-seller""".split()

def pull(ref):
    u, s = ref.split('/')
    f = os.path.join(OUT, s + '.json')
    if not os.path.exists(f):
        req = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/pull?userName=%s&kernelSlug=%s' % (u, s), headers={'Authorization': 'Bearer ' + TOK})
        try:
            data = urllib.request.urlopen(req, timeout=120).read()
        except Exception as e:
            return None, 'pull failed ' + repr(e)[:60]
        open(f, 'wb').write(data)
    d = json.load(open(f, encoding='utf-8'))
    blob = d.get('blob', {}); src = blob.get('source', '')
    if blob.get('kernelType') == 'script' or not src.lstrip().startswith('{'):
        return src, 'script'
    nb = json.loads(src)
    files = {}; loose = []
    for c in nb.get('cells', []):
        if c.get('cell_type') != 'code': continue
        body = c.get('source'); body = ''.join(body) if isinstance(body, list) else (body or '')
        m = re.match(r'\s*%%writefile\s+(-a\s+)?(\S+)\s*\n', body)
        if m:
            name = m.group(2); rest = body[m.end():]
            files[name] = files.get(name, '') + rest if m.group(1) else rest
        else:
            loose.append('\n'.join(l for l in body.split('\n') if not l.lstrip().startswith(('!', '%'))))
    # the agent file: a written .py defining agent(), else the loose cells
    cand = [(n, s_) for n, s_ in files.items() if n.endswith('.py') and 'def agent' in s_]
    if cand:
        cand.sort(key=lambda x: -len(x[1]))
        return cand[0][1], 'writefile:' + cand[0][0] + (' +%d files' % (len(files) - 1) if len(files) > 1 else '')
    joined = '\n'.join(loose)
    if 'def agent' in joined:
        return joined, 'loose cells'
    return None, 'no agent (files: %s)' % list(files)[:4]

SIG = r'''
import sys, contextlib, io, json
sys.path.insert(0, %r)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
A = lean.load(%r)
log = []
def w(obs, cfg=None):
    a = A(obs, cfg)
    st = int(obs['step'])
    if st <= 1 and isinstance(a, dict):
        log.append((st, [o for o in (a.get('market') or []) if isinstance(o, list)]))
    return a
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    r = lean.play(None, None, 7, agent_objs=[w, K.pass_agent], max_steps=3)
print(json.dumps(log))
'''
for ref in REFS:
    src, how = pull(ref)
    slug = ref.split('/')[1]
    if src is None:
        print('%-58s %s' % (slug[:58], how), flush=True); continue
    py = os.path.join(OUT, slug + '.py')
    open(py, 'w', encoding='utf-8').write(src)
    try:
        r = subprocess.run([sys.executable, '-c', SIG % (os.path.join(KG, 'arena'), py)], capture_output=True, text=True, timeout=90, cwd=KG)
        out = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
        sig = json.loads(out) if out.startswith('[') else None
        if sig is None:
            fp = 'ERR ' + (r.stderr.strip().split('\n')[-1][:70] if r.stderr.strip() else 'no output')
        else:
            fp = ' | '.join('s%d %s' % (st, ' '.join('%s:%s%s' % (o[0][:4], (o[1][:3] if len(o) > 1 and isinstance(o[1], str) else ''), ('x%s' % o[2] if len(o) > 2 else '')) for o in m)) for st, m in sig)
    except subprocess.TimeoutExpired:
        fp = 'TIMEOUT'
    print('%-58s %6dB %-22s %s' % (slug[:58], len(src), how[:22], fp[:150]), flush=True)
