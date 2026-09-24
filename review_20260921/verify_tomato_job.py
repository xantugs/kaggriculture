"""Isolated engine check: eight tomatoes with two harvests; excludes travel and labor costs."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import harness
from kaggle_environments.envs.kaggriculture import kaggriculture as K

farm=K._new_farm(10,3000)
private=K._new_private()
private['seeds']['TOMATO']=1
private['inventories'][0]['FERTILIZER']=2
schedule={0:[['PLANT','TOMATO'],['WATER']],2:[['WATER']],4:[['WATER']],6:[['WATER']],
          7:[['FERTILIZE'],['WATER']],8:[['WATER']],9:[['HARVEST'],['WATER']],
          10:[['FERTILIZE'],['WATER']],11:[['HARVEST']]}
log=[]
for day in range(12):
    acts=schedule.get(day,[])
    before=private['inventories'][0].get('TOMATO',0)
    for hour,action in enumerate(acts):
        K._apply_unit_action(farm,private,0,action,10,day,24)
        K._decay_plants(farm,day*24+hour)
    assert isinstance(farm['tiles'][4][4],dict) and farm['tiles'][4][4].get('crop')=='TOMATO'
    log.append({'age':day,'actions':acts,'harvested':private['inventories'][0].get('TOMATO',0)-before})
    K._daily_refresh_plants(farm,day,24)
harvested=private['inventories'][0].get('TOMATO',0)
assert harvested==8
result={'harvested':harvested,'fertilizer_used':2,'harvest_actions':2,
        'watering_actions':sum(a[0]=='WATER' for acts in schedule.values() for a in acts),
        'tile_actions_excluding_clearance':sum(map(len,schedule.values())),
        'schedule':log,'limits':'Single stationary worker; inputs prepositioned; no travel, transport, hire cost, price impact or competition modeled. This proves yield feasibility, not profit or full-farm feasibility.'}
Path(__file__).with_name('tomato_job_verified.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
