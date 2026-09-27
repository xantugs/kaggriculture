"""Research-only build: lean sf8 + a log of every controller hire search (no behaviour change).
usage: patch_hirelog.py in.py out.py     The log goes to the file named by env LAB_HIRELOG (one JSON line per day)."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()

a1 = "            score = -pen - 0.6 * cost\n"
assert src.count(a1) == 1
src = src.replace(a1, a1 + "            _hl_trace.append((h, cost, round(pen), len(unserved), sum(1 for v in unserved if v.must), ovf))\n")

a2 = "    def _route_and_hire(self, visits, cash, final, day):\n        best = None\n"
assert src.count(a2) == 1
src = src.replace(a2, a2 + "        _hl_trace = []\n")

a3 = "        return (best[2], best[1], best[3])\n\n    def _compile(self, routes, spawns, hour0=True):"
assert src.count(a3) == 1
src = src.replace(a3, """        try:
            import os as _hl_os, json as _hl_json, collections as _hl_c
            _p = _hl_os.environ.get('LAB_HIRELOG')
            if _p:
                tags = _hl_c.Counter(v.tag for v in visits); mtags = _hl_c.Counter(v.tag for v in visits if v.must)
                acts = _hl_c.Counter(a[0] for v in visits for a in v.acts)
                macts = sum(len(v.acts) for v in visits if v.must)
                with open(_p, 'a') as _f:
                    _f.write(_hl_json.dumps(dict(day=day, final=final, chosen=best[1], cash=round(cash), n=len(visits),
                        nmust=sum(1 for v in visits if v.must), acts=sum(len(v.acts) for v in visits), macts=macts,
                        val=round(sum(v.value for v in visits)), tags=dict(tags), mtags=dict(mtags), actc=dict(acts),
                        trace=_hl_trace, last=self.last_hires)) + '\\n')
        except Exception:
            pass
        return (best[2], best[1], best[3])

    def _compile(self, routes, spawns, hour0=True):""")
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('ok')
