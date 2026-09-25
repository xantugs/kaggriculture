"""Run the official kaggle_environments runner: candidate vs itself and vs an opponent file; report statuses, rewards,
max per-step agent time. usage: official_check.py cand.py opp.py"""
import sys, time, importlib.util, statistics as st
from kaggle_environments import make
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.agent if hasattr(m, 'agent') else m.kaggle_submission_agent
def timed(fn, times):
    def f(obs, cfg):
        t = time.perf_counter(); a = fn(obs, cfg); times.append(time.perf_counter() - t); return a
    return f
cand, opp = sys.argv[1], sys.argv[2]
for label, pair in (('self', (cand, cand)), ('vs_opp', (cand, opp)), ('opp_first', (opp, cand))):
    ta, tb = [], []
    A = timed(load(pair[0], 'a_' + label), ta); B = timed(load(pair[1], 'b_' + label), tb)
    env = make('kaggriculture', debug=False)
    t0 = time.time(); steps = env.run([A, B]); last = steps[-1]
    print(label, 'status', [s['status'] for s in last], 'rewards', [s['reward'] for s in last],
          'max step s', round(max(ta), 3), round(max(tb), 3), 'mean ms', round(1000 * st.mean(ta), 1), 'wall', round(time.time() - t0))
