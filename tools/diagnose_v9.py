"""One-match logistics diagnostics against the unmodified official simulator."""
import collections
import json
from pathlib import Path
import pickle
import copy
from harness import run_match
from kaggle_environments.envs.kaggriculture import kaggriculture as K

ROOT = Path(__file__).resolve().parent.parent
overflow = []
original_drop = K._drop_inventories_to_shed

def log_drop(private, capacity):
    before = collections.Counter(private['shed'])
    for inv in private['inventories']:
        before.update(inv)
    original_drop(private, capacity)
    lost = dict(before - collections.Counter(private['shed']))
    overflow.append({'day':len(overflow)//2, 'seat':len(overflow)%2, 'lost':lost})

K._drop_inventories_to_shed = log_drop
env, rewards, statuses = run_match('versions/main_v8.py', 'versions/main_v8.py', 30000)
K._drop_inventories_to_shed = original_drop
with (ROOT/'logs/diagnosis_v9_match.pkl').open('wb') as f:
    pickle.dump({'steps':env.steps, 'configuration':env.configuration}, f)

report = {'seed':30000, 'rewards':rewards, 'statuses':statuses, 'overflow':overflow, 'seats':[]}
for seat in range(2):
    actions = collections.Counter()
    noops = collections.Counter()
    noops_examples = []
    daily = []
    for s in range(len(env.steps)-1):
        observation = env.steps[s][seat].observation
        action = env.steps[s+1][seat].action or {}
        farm = copy.deepcopy(observation.farms[seat])
        private = copy.deepcopy(observation.private)
        day, hour = observation.day, observation.hour
        for i, a in enumerate([action.get('farmer')]+list(action.get('hands',[]))):
            if not a:
                continue
            op = a[0]
            actions[op] += 1
            if i >= len(private['inventories']):
                noops['MISSING_UNIT:'+op] += 1
                continue
            pos = farm['farmer'] if i==0 else farm['hands'][i-1]
            tile = farm['tiles'][pos[1]][pos[0]]
            before = repr((pos, tile, private))
            K._apply_unit_action(farm, private, i, a, 10, day, 24, 100)
            after_pos = farm['farmer'] if i==0 else farm['hands'][i-1]
            after_tile = farm['tiles'][pos[1]][pos[0]]
            after = repr((after_pos, after_tile, private))
            if before == after and op != 'PASS':
                noops[op] += 1
                if len(noops_examples)<25:
                    noops_examples.append({'step':s,'unit':i,'action':a,'pos':pos,'tile':tile,'inventory':private['inventories'][i]})
        if hour == 23 or s==len(env.steps)-2:
            tiles = [t for row in farm['tiles'] for t in row if isinstance(t,dict)]
            animals = [t for t in tiles if t.get('animal')]
            plants = [t for t in tiles if t.get('kind')=='PLANT']
            escaping = [t for t in animals if not t['fed_today'] and t['consecutive_unfed']>=1]
            dying = [t for t in plants if not t['watered_today'] and t['consecutive_unwatered']>=1]
            daily.append({'day':day,'money':farm['money'],'animals':len(animals),'unfed':sum(not t['fed_today'] for t in animals),'uncared':sum(not t['cared_today'] for t in animals),'escapes':dict(collections.Counter(t['animal'] for t in escaping)),'plants':len(plants),'unwatered':sum(not t['watered_today'] for t in plants),'dying_plants':dict(collections.Counter(t['crop'] for t in dying)),'fertilizer_uncollected':sum(t['fertilizer_available'] for t in animals),'unharvested_units':dict(sum((collections.Counter({t['crop'] if t.get('kind')=='PLANT' else K.ANIMALS[t['animal']]['product']:t.get('yield_units',0)}) for t in plants+animals),collections.Counter())),'carried':dict(sum((collections.Counter(inv) for inv in private['inventories']),collections.Counter())),'shed':private['shed']})
    report['seats'].append({'seat':seat,'actions':dict(actions),'noops':dict(noops),'noop_examples':noops_examples,'daily':daily})
(ROOT/'logs/diagnosis_v9.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
