"""Kaggle's validation episode locally: the official kaggle_environments runner, agent vs a copy of itself.
usage: official_selfplay.py agent.py [seed]"""
import sys, time
from kaggle_environments import make
path = sys.argv[1]; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 6042
env = make('kaggriculture', configuration={'seed': seed}, debug=True)
t = time.time()
env.run([path, path])
last = env.steps[-1]
print('statuses', [s.status for s in last], 'rewards', [s.reward for s in last], 'steps', len(env.steps), 'wall %.0fs' % (time.time() - t))
