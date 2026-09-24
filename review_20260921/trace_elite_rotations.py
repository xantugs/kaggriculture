"""Reproduce recorded games and measure actual crop rotations and resource use."""
import collections
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from harness import make
from kaggle_environments.envs.kaggriculture import kaggriculture as K

OUT = Path(__file__).parent
structure = json.loads((OUT/'elite_structure.json').read_text())
digests = {r['id']:r for r in json.loads(gzip.decompress((ROOT/'replays/kgdigest_top1.json.gz').read_bytes()))}
chosen = []
for name in ('DSM','Majkel1337','THIRD FARM CLUB','Otter Vibe','Vadim Vasilenko','ymg_aq'):
    chosen.append(next(r for r in structure['games'] if r['top']==name and r['clean']))


def trace(record):
    digest = digests[record['id']]
    top = digest['info']['TeamNames'].index(record['top'])
    ids = {}
    crops = {}
    previous = {}
    sales = collections.defaultdict(lambda:collections.defaultdict(lambda:[0,0]))
    waste = [collections.Counter(),collections.Counter()]
    shops = {}
    current = {'step':0}
    original_unit,original_market,original_commit,original_daily = K._apply_unit_action,K._process_market,K._commit_unit,K._daily_refresh_animals

    def unit(farm, private, actor, action, board, day, tpd, shed_capacity=100):
        p = ids.get(id(farm))
        pos = K._farmer_position(farm,actor)
        before = None if pos is None else farm['tiles'][pos[1]][pos[0]]
        tile = dict(before) if isinstance(before,dict) else before
        inv0 = dict(private['inventories'][actor]) if actor<len(private['inventories']) else {}
        result = original_unit(farm,private,actor,action,board,day,tpd,shed_capacity)
        if p is None or pos is None:return result
        x,y=pos
        after = farm['tiles'][y][x]
        inv = private['inventories'][actor] if actor<len(private['inventories']) else {}
        if tile is None and isinstance(after,dict) and after.get('kind')=='PLANT':
            key=(p,x,y,after['planted_day'],after['crop'])
            crops[key]={'seat':p,'x':x,'y':y,'crop':after['crop'],'planted_day':day,
                        'previous_crop':previous.get((p,x,y),'unused'), 'harvests':[], 'fertilizer':0,'waters':0}
            previous[(p,x,y)] = after['crop']
        if isinstance(tile,dict) and tile.get('kind')=='PLANT':
            key=(p,x,y,tile['planted_day'],tile['crop'])
            rec=crops.get(key)
            if rec is not None and action:
                if action[0]=='HARVEST':
                    got=inv.get(tile['crop'],0)-inv0.get(tile['crop'],0)
                    if got>0:rec['harvests'].append({'step':current['step'],'units':got})
                if action[0]=='FERTILIZE':rec['fertilizer']+=max(0,inv0.get('FERTILIZER',0)-inv.get('FERTILIZER',0))
                if action[0]=='WATER' and not tile.get('watered_today') and isinstance(after,dict) and after.get('watered_today'):rec['waters']+=1
        return result

    def market(state,env):
        return original_market(state,env)

    def commit(op,item,price,farm,private,market,shed_capacity=100):
        ok=original_commit(op,item,price,farm,private,market,shed_capacity)
        if ok and op=='SELL':
            row=sales[(ids[id(farm)],current['step']//24)][item]
            row[0]+=1;row[1]+=price
        return ok

    def daily(farm,day):
        p=ids[id(farm)]
        for row in farm['tiles']:
            for t in row:
                if not isinstance(t,dict) or 'animal' not in t:continue
                a=K.ANIMALS[t['animal']]
                age=day+1-t['placed_day']-a['first_yield_day']
                if age>=0 and age%a['interval']==0 and (t['fed_today'] or t['consecutive_unfed']<1):
                    bonus=t.get('pending_care_bonus',0) if t['fed_today'] else 0
                    waste[p][a['product']]+=max(0,t['yield_units']+1+bonus-a['max_held'])
        return original_daily(farm,day)

    def agent(p):
        def act(obs,config=None):
            if p==0 and obs['step']%24==0:shops[obs['step']//24]=list(obs['town']['unlocked_shops'])
            return digest['acts'][min(obs['step']+1,len(digest['acts'])-1)][p]
        return act

    K._apply_unit_action,K._commit_unit,K._daily_refresh_animals=unit,commit,daily
    try:
        env=make('kaggriculture',debug=True,configuration={'seed':digest['info']['seed']})
        base_interpreter=env.interpreter
        def interpret(state, environment):
            obs=state[0].observation
            if getattr(obs,'farms',None):
                ids.clear()
                ids.update({id(f):i for i,f in enumerate(obs.farms)})
                current['step']=obs.get('step',0)
            return base_interpreter(state,environment)
        env.interpreter=interpret
        env.run([agent(0),agent(1)])
    finally:
        K._apply_unit_action,K._process_market,K._commit_unit,K._daily_refresh_animals=original_unit,original_market,original_commit,original_daily
    rewards=[s.reward for s in env.steps[-1]]
    assert rewards==digest['rewards'],(record['id'],rewards,digest['rewards'])
    tomatoes=[v for v in crops.values() if v['seat']==top and v['crop']=='TOMATO']
    units=sum(h['units'] for t in tomatoes for h in t['harvests'])
    result={'id':record['id'],'top':record['top'],'top_seat':top,'rewards':rewards,'exact_reproduction':True,
            'crops':list(crops.values()),'shops':shops,'animal_yield_clipped_by_capacity':list(map(dict,waste)),
            'daily_sales':{str(p)+':'+str(d):dict(v) for (p,d),v in sales.items()}}
    (OUT/('elite_rotation_'+str(record['id'])+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'id':record['id'],'top':record['top'],'tomato_plants':len(tomatoes),
                      'tomato_harvested':units,'tomato_units_per_plant':round(units/max(1,len(tomatoes)),2),
                      'tomato_fertilizer':sum(t['fertilizer'] for t in tomatoes),
                      'tomato_previous':dict(collections.Counter(t['previous_crop'] for t in tomatoes)),
                      'animal_capacity_clipping':[dict(waste[p]) for p in (top,1-top)]}),flush=True)

if __name__=='__main__':
    for record in chosen:trace(record)
