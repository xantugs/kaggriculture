"""eval_batch.py base_cfg.json batch.json [parallel=2] : evaluate hand-designed override sets on the search's reacting panel
(120 games vs T8 on seeds 6200-6259, 40 vs omw_v15a, 40 vs pub_metav4v13). batch.json = {"name": {overrides}, ...}."""
import sys, os, json, statistics as st
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import search_open as S
base = json.load(open(sys.argv[1], encoding='utf-8'))
batch = json.load(open(sys.argv[2], encoding='utf-8'))
par = int(sys.argv[3]) if len(sys.argv) > 3 else 2
def one(item):
    name, over = item
    cfg = json.loads(json.dumps(base))
    for k, v in over.items():
        cfg = S.apply(cfg, k, v)
    path = S.build('b_' + name, cfg)
    score, wins, n, per = S.evaluate(path, 'b_' + name)
    return name, score, wins, n, per, over
with ThreadPoolExecutor(par) as ex:
    for name, score, wins, n, per, over in ex.map(one, list(batch.items())):
        line = dict(name=name, score=score, wins=wins, n=n, per=per, over=over)
        open(os.path.join(HERE, 'eval_batch_log.jsonl'), 'a', encoding='utf-8').write(json.dumps(line) + '\n')
        print('%-6s score %+6.0f wins %3d/%d  T8 %s  omw %s  pub %s' % (name, score, wins, n, (per['T8']['wins'], round(per['T8']['margin'])), (per['omw']['wins'], round(per['omw']['margin'])), (per['pub']['wins'], round(per['pub']['margin']))), flush=True)
