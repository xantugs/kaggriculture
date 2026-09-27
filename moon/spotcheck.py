import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
from concurrent.futures import ProcessPoolExecutor
if __name__ == '__main__':
    files = json.load(open('hold_list.json'))[:8]
    ref = {}
    for l in open('hold_k.jsonl', encoding='utf-8'):
        r = json.loads(l)
        if r['label'] == 'k_combo_hd': ref[r['gid']] = r['m']
    C = os.path.join(HERE, '..', 'arena', 'cand', 'omw_ad_a2.py')
    with ProcessPoolExecutor(8) as ex:
        for rs in ex.map(pinmulti._job, [(f, 0, 96, [('a2', C, {})], 'offhand') for f in files]):
            r = rs[0]; print(r['gid'], r['m'], ref.get(r['gid']), 'OK' if r['m'] == ref.get(r['gid']) else 'DIFF')
