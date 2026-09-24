import json, glob, sys, collections
IT = ("STRAWBERRY", "MILK", "WOOL", "MELON", "EGG", "TOMATO")
files = sys.argv[1:]
for f in files:
    for g in json.load(open(f)):
        n = g['info']['TeamNames']
        if 'Khantugs Gantulga' not in n: continue
        P = n.index('Khantugs Gantulga'); O = 1 - P
        acts = g['acts']
        def sells(p):
            out = []
            for s in range(648, 720):
                a = acts[s][p] if s < len(acts) else None
                if not isinstance(a, dict): continue
                for o in a.get('market') or []:
                    if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL' and o[1] in IT[:4]:
                        out.append('%d:%s%s' % (s - 1, o[1][:2], o[2]))
            return out
        print('%s %-16s m %+7d' % (g['id'], n[O][:16], g['rewards'][P] - g['rewards'][O]))
        print('    US  ', ' '.join(sells(P)))
        print('    THEM', ' '.join(sells(O)))
