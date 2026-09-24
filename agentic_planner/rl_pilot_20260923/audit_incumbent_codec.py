"""Describe late-game v13 actions changed by the current BC codec."""
from pathlib import Path
from collections import Counter
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'snapshot'))
import lean
spec = importlib.util.spec_from_file_location('codec', HERE.parents[1] / 'moon' / 'bc_codec.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


def summarize_market(action):
    return tuple(tuple(x) for x in (action.get('market') or []))


counts = Counter()
examples = {}
for seed in range(850000001, 850000005):
    agents = [lean.load(str(HERE/'snapshot'/'v12.py')) for _ in range(2)]
    def wrap(p, inner):
        def f(obs, cfg):
            action = inner(obs, cfg)
            if obs['step'] >= 672:
                decoded = codec.roundtrip(action, obs['private']['inventories'])
                original_market, decoded_market = summarize_market(action), summarize_market(decoded)
                if original_market != decoded_market:
                    counts['market_turns_changed'] += 1
                    if sorted(original_market) == sorted(decoded_market):
                        kind = 'market_order_only'
                    elif any(o and o[0] == 'SELL' and len(o) > 2 and o[2] > 30 for o in original_market):
                        kind = 'large_sell_quantity'
                    else:
                        kind = 'other_market_content'
                    counts[kind] += 1
                    examples.setdefault(kind, dict(seed=seed, step=obs['step'], original=original_market, decoded=decoded_market))
                original_units = [action.get('farmer')] + list(action.get('hands') or [])
                decoded_units = [decoded.get('farmer')] + list(decoded.get('hands') or [])
                for a,b in zip(original_units,decoded_units):
                    if a != b:
                        counts['unit_commands_changed'] += 1
                        kind = 'unit_' + str(a[0] if a else None)
                        counts[kind] += 1
                        examples.setdefault(kind, dict(seed=seed, step=obs['step'], original=a, decoded=b))
            return action
        return f
    result=lean.play(None,None,seed,agent_objs=[wrap(0,agents[0]),wrap(1,agents[1])])
    assert result['err']==[None,None],result
out=dict(seeds=4,farm_seasons=8,turns_per_season=47,counts=dict(counts),examples=examples)
(HERE/'incumbent_codec_audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
