"""v12 + counter-tomato gate. usage: build_ct.py out.py min_rival_tomatoes min_tomato_shops"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
base = open(os.path.join(here, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
layer = open(os.path.join(here, 'ct_layer.py'), encoding='utf-8').read().replace('__CT_MIN__', sys.argv[2]).replace('__CT_SHOPS__', sys.argv[3])
open(sys.argv[1], 'w', encoding='utf-8').write(base.rstrip() + '\n' + layer)
print('built', sys.argv[1])
