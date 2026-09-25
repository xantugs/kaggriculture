import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import oracle_fert
from concurrent.futures import ProcessPoolExecutor
if __name__ == '__main__':
    files = json.load(open('g2800_list.json'))[:6]
    path = os.path.join(HERE, '..', 'arena', 'cand', 'omw_ad_a2.py')
    with ProcessPoolExecutor(2) as ex:
        for gid, o in ex.map(oracle_fert.job, [(f, path, 96, 5, 28, {'WHEAT', 'CARROT', 'STRAWBERRY'}, [0, 4], 0, 0, 'best') for f in files]):
            print(gid, o)
