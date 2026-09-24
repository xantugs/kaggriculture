"""Classify each player's wheat round-trip style across all downloaded replays."""
import json, glob, collections, sys
def orders(a):
    if not isinstance(a, dict): return []
    return [o for o in (a.get('market') or []) if isinstance(o, list) and len(o) >= 3]
def style(acts, pl):
    same = split = 0; lead0 = 0
    for s in range(3, len(acts)):
        m = orders(acts[s][pl])
        b = [o for o in m if o[0] == 'BUY_PRODUCT' and o[1] == 'WHEAT']
        se = [o for o in m if o[0] == 'SELL' and o[1] == 'WHEAT']
        if b and se:
            same += 1
            if m and m[0][0] == 'BUY_PRODUCT' and m[0][1] == 'WHEAT': lead0 += 1
        elif b and s + 1 < len(acts):
            q = int(b[0][2])
            m2 = orders(acts[s + 1][pl])
            if any(o[0] == 'SELL' and o[1] == 'WHEAT' and int(o[2]) == q for o in m2): split += 1
    return same, split, lead0
def main():
  rows = collections.defaultdict(list)
  for f in sorted(glob.glob('cf/*/*.json')):
      try: D = json.load(open(f))
      except Exception: continue
      if isinstance(D, dict): D = [D]
      for d in D:
          if not isinstance(d, dict) or 'acts' not in d: continue
          names = d['info']['TeamNames']
          for pl in (0, 1):
              rows[names[pl]].append(style(d['acts'], pl) + (f.split('/')[1],))
  tot = collections.Counter()
  for n, r in sorted(rows.items(), key=lambda kv: -len(kv[1])):
      same = sum(x[0] for x in r) / len(r); split = sum(x[1] for x in r) / len(r); lead = sum(x[2] for x in r) / len(r)
      cls = 'R1-same' if same >= 10 else ('R0-split' if split >= 10 else 'other')
      tot[cls] += 1
      print('%-28s games %3d  same %5.1f (lead0 %5.1f) split %5.1f  %s' % (n[:28], len(r), same, lead, split, cls))
  print(tot)

if __name__ == '__main__': main()