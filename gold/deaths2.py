"""Count plant deaths by drought (PLANT->WEED while not yet decaying) and animal escapes, both seats (decoupled)."""
import sys, collections, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
prev = [None, None]; cnt = [collections.Counter(), collections.Counter()]
def wrap(ag, seat):
    def f(obs, cfg=None):
        if seat == 0 and obs['hour'] == 0:
            for i in (0, 1):
                cur = obs['farms'][i]['tiles']
                if prev[i] is not None:
                    for y in range(10):
                        for x in range(10):
                            p = prev[i][y][x]; t = cur[y][x]
                            if isinstance(p, dict) and p.get('kind') == 'PLANT' and isinstance(t, dict) and t.get('kind') == 'WEED':
                                cnt[i][('drought_' if p['max_lifespan_step'] < 0 or p['yield_units'] > 0 and p['consecutive_unwatered'] >= 1 else 'done_') + p['crop'][:5]] += 1
                            if isinstance(p, dict) and p.get('animal') and not (isinstance(t, dict) and t.get('animal')):
                                cnt[i]['escape_' + p['animal']] += 1
                prev[i] = json.loads(json.dumps(cur))
        return ag(obs, cfg)
    return f
r = lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
print('result', r['r'])
for i in (0, 1): print('seat', i, dict(cnt[i]))
