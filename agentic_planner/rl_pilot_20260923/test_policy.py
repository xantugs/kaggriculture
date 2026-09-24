"""Exercise the same decoder used by rollout and greedy evaluation."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / 'snapshot'))
import bcm
import policy

grid = np.zeros((38,10,10), np.float32)
glob = np.zeros(114, np.float32)
uv = np.zeros(48, np.float32)
bcm.encode = lambda *args: (grid, glob, [((4,4),uv)])
ua = np.full((1,len(bcm.UA)), -10, np.float32)
ua[0,bcm.UA.index('PICKUP_WHEAT')] = 10
uq = np.full((1,bcm.NQ), -10, np.float32)
uq[0,12] = 10  # preferred amount 13, unavailable
uq[0,0] = 5    # best available amount is 1
mk = {h:np.asarray([10]+[-10]*(s-1),np.float32) for h,s in zip(bcm.MARKET_HEADS,bcm.MARKET_SIZES)}
bcm.forward = lambda *args: (ua,uq,mk)
obs = dict(player=0, farms=[dict(tiles=[[None]*10 for _ in range(10)])],
           private=dict(shed={'WHEAT':3}, seeds={}, inventories=[{}]))
action = policy.policy_act(obs, {}, 1.0, None, True, [])
assert action['farmer'] == ['PICKUP','WHEAT',1], action
for stock in [0,1,2,3,19,20,100]:
    obs['private']['shed']['WHEAT']=stock
    records=[]
    action=policy.policy_act(obs, {}, 1.0, None, True, records)
    if stock:
        assert 1 <= action['farmer'][2] <= stock
        assert records[0]['q'][0] < records[0]['qb'][0]
    else:
        assert action['farmer'][0] != 'PICKUP'
    assert records[0]['grid'].dtype == np.float32
print('decoder boundary checks passed; shared greedy pickup respects its training action support')
