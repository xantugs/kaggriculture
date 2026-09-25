"""Split gate with global-override variants. base = v16 (omw_ad_a1). usage: exp_pin_vars.py out.jsonl S variants.json
variants.json = [[label, cand_name, {global: value}], ...]"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pinmulti
if __name__ == '__main__':
    out, S = sys.argv[1], int(sys.argv[2]); C = os.path.join(HERE, '..', 'arena', 'cand')
    base = os.environ.get('VBASE', 'omw_ad_a1')
    vs = [('base', os.path.join(C, base + '.py'), {})]
    for lab, cand, glb in json.load(open(sys.argv[3])):
        if '_AD_CFG' in glb:
            glb['_AD_CFG']['thresh'] = {int(k): v for k, v in glb['_AD_CFG']['thresh'].items()}
        vs.append((lab, os.path.join(C, cand + '.py'), glb))
    files = json.load(open(os.path.join(HERE, os.environ.get('GLIST', 'g2800_list.json'))))
    if os.environ.get('VCLASS'):
        cls = json.load(open(os.path.join(HERE, os.environ.get('GCLASS', 'gameclass.json'))))
        files = [f for f in files if (cls.get(os.path.basename(f)[:-5], 0) >= 0.8) == (os.environ['VCLASS'] == 'MIRROR')]
    pinmulti.run([(f, 0) for f in files], S, vs, out, chunk=int(os.environ.get('VCHUNK', '0')) or len(vs))
