"""Research-only build: a full-build candidate (e.g. cands/full_T5.py) + a log of every controller hire search.
No behaviour change. The log goes to the file named by env LAB_HIRELOG (one JSON line per controller day plan).
Per searched hand count h: (h, cost, pen, n_unserved, n_must_unserved, ovf, {tag: [n, value]} of the unserved visits).
At the chosen h: route turn use per unit ([rcost, cap]).
usage: patch_hirelog_full.py in.py out.py"""
import sys
src = open(sys.argv[1], encoding='utf-8').read()

head = "    def _route_and_hire(self, visits, cash, final, day):\n        best = None\n"
assert src.count(head) == 1
i0 = src.index(head)
src = src[:i0] + head + "        _hl_trace = []\n" + src[i0 + len(head):]

a1 = '            score = -pen - GC_P["hire_cost_w"] * cost\n'
i1 = src.index(a1, i0)
ins = ('            _hl_u = {}\n'
       '            for _v in unserved:\n'
       '                _e = _hl_u.setdefault(_v.tag + ("!" if _v.must else ""), [0, 0.0]); _e[0] += 1; _e[1] += round(_v.value)\n'
       '            _hl_trace.append((h, cost, round(pen), len(unserved), sum(1 for v in unserved if v.must), ovf, _hl_u))\n')
src = src[:i1] + a1 + ins + src[i1 + len(a1):]

a3 = '        _GC_REPORT["gc_unserved"] += int(best[4])\n        return best[2], best[1], best[3]\n'
i3 = src.index(a3, i1)
rep = '''        try:
            import os as _hl_os, json as _hl_json, collections as _hl_c
            _p = _hl_os.environ.get('LAB_HIRELOG')
            if _p:
                tags = _hl_c.Counter(v.tag for v in visits); mtags = _hl_c.Counter(v.tag for v in visits if v.must)
                acts = _hl_c.Counter(a[0] for v in visits for a in v.acts)
                use = []
                for _u, _r in enumerate(best[2]):
                    try:
                        use.append([self._rcost(best[3][_u], _r), self._cap(_u)])
                    except Exception:
                        use.append(None)
                with open(_p, 'a') as _f:
                    _f.write(_hl_json.dumps(dict(day=day, final=final, chosen=best[1], cash=round(cash), n=len(visits),
                        nmust=sum(1 for v in visits if v.must), acts=sum(len(v.acts) for v in visits),
                        val=round(sum(v.value for v in visits)), tags=dict(tags), mtags=dict(mtags), actc=dict(acts),
                        trace=_hl_trace, last=self.last_hires, use=use)) + '\\n')
        except Exception:
            pass
'''
src = src[:i3] + rep + src[i3:]
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('ok')
