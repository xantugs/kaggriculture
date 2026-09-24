"""Track each strawberry plant alive at day 12 (both seats): the day it vanishes, whether it had finished (mls>=0), and what replaced it."""
import sys, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
track = [{}, {}]
def wrap(ag, seat):
    def f(obs, cfg=None):
        if seat == 0 and obs['day'] >= 12:
            for i in (0, 1):
                tiles = obs['farms'][i]['tiles']
                for y in range(10):
                    for x in range(10):
                        t = tiles[y][x]; key = (x, y)
                        if obs['step'] == 288:
                            if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                                track[i][key] = dict(pd=t['planted_day'], gone=None, last=None)
                        elif key in track[i] and track[i][key]['gone'] is None:
                            e = track[i][key]
                            if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY' and t['planted_day'] == e['pd']:
                                e['last'] = dict(mls=t['max_lifespan_step'], cu=t['consecutive_unwatered'], yu=t['yield_units'], fu=t['fertilized_until_day'])
                            else:
                                e['gone'] = (obs['day'], obs['hour'], 'WEED' if isinstance(t, dict) and t.get('kind') == 'WEED' else (t.get('crop') if isinstance(t, dict) else str(t)))
        return ag(obs, cfg)
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
for i in (0, 1):
    early = [(k, e) for k, e in track[i].items() if e['gone'] and e['last'] and e['last']['mls'] < 0]
    fin = [(k, e) for k, e in track[i].items() if e['gone'] and e['last'] and e['last']['mls'] >= 0]
    print('seat %d plants %d  vanished-unfinished %d  vanished-finished %d  alive-at-end %d' % (i, len(track[i]), len(early), len(fin), sum(1 for e in track[i].values() if not e['gone'])))
    for k, e in early[:8]:
        print('    unfinished', k, 'planted', e['pd'], 'gone', e['gone'], 'last', e['last'])
