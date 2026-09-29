"""preflight_state.py FILE : determinism (two fresh loads, same game, identical action traces), state reset (one loaded agent
plays game A then game B; B must equal a fresh-load B), memory growth over 6 games in one process (tracemalloc), stdout output."""
import sys, os, io, json, contextlib, tracemalloc
sys.path.insert(0, os.path.join(os.getcwd(), 'arena'))
import lean
f = sys.argv[1]
OPP = 'gold/submit/main_ctl_T8.py'
def trace(agent, seed):
    acts = []
    def w(obs, cfg=None):
        a = agent(obs, cfg); acts.append(json.dumps(a, sort_keys=True)); return a
    r = lean.play(None, None, seed, agent_objs=[w, lean.load(OPP)])
    return acts, (r['r'][0], r['r'][1])
lean._SRC.clear() if hasattr(lean, '_SRC') else None
a1, r1 = trace(lean.load(f), 8301)
a2, r2 = trace(lean.load(f), 8301)
print('determinism: same actions %s (%d steps), same result %s %s' % (a1 == a2, len(a1), r1 == r2, r1))
A = lean.load(f)
_, rA = trace(A, 8302)
bufB = io.StringIO()
with contextlib.redirect_stdout(bufB):
    aB_same, rB_same = trace(A, 8303)
aB_fresh, rB_fresh = trace(lean.load(f), 8303)
print('state reset: game B after game A in the same agent == fresh game B: actions %s result %s (%s vs %s)' % (aB_same == aB_fresh, rB_same == rB_fresh, rB_same, rB_fresh))
print('stdout during a game: %d chars' % len(bufB.getvalue()))
tracemalloc.start()
A = lean.load(f); mem = []
for s in range(8310, 8316):
    trace(A, s)
    cur, peak = tracemalloc.get_traced_memory(); mem.append(cur // 1024)
print('memory over 6 games in one process (KiB after each game):', mem)
