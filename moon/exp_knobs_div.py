"""Knob sweep on the DIVERGENT subset of the split gate (games vs 2800+ non-copy teams) for a base agent.
usage: exp_knobs_div.py out.jsonl S base_file"""
import sys, os, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti, tune
if __name__ == '__main__':
    out, S, base = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    src = open(base, encoding='utf-8').read()
    knobs = dict(tune.KNOBS); knobs.update(tune.KNOBS2)
    knobs.update({'_PE_STEP': [680, 686, 692], '_R51_INPUT_CROPS': [{'WHEAT': (2, 4, 6), 'CARROT': (2, 3, 4)}]})
    vs = [('base', base, {})]
    for k, vals in knobs.items():
        if re.search(r'^%s\s*=' % re.escape(k), src, flags=re.M):
            for v in vals:
                vs.append((tune.label(k, v), base, {k: v}))
    cls = json.load(open(os.path.join(HERE, 'gameclass.json')))
    games = [(f, 0) for f in json.load(open(os.path.join(HERE, 'g2800_list.json')))
             if cls.get(os.path.basename(f)[:-5], 1.0) < 0.8]
    print('games', len(games), 'variants', len(vs), flush=True)
    pinmulti.run(games, S, vs, out, chunk=12)
