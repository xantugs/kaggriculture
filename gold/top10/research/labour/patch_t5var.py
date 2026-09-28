"""Research-only counterfactual builds of a full-build candidate's hire search (measurement probes, not submissions).
usage: patch_t5var.py in.py out.py VARIANT[+VARIANT...]
  capN      max_hands N on non-final controller days (T5: 15)
  ovfV      end-of-day overflow priced at V dollars a unit in the hire search (T5: 100)
  keepK     overflow the night's shed_skip could leave on its tiles (carry after a route's last stop on a tile that keeps
            its units until tomorrow: animals under max_held, ongoing crops under max_yield and not decaying, one-time
            crops before their last window day) is priced at K dollars a unit instead of ovf_value
"""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
upd = "GC_P.update({'start'"
assert src.count(upd) == 1
iu = src.index(upd)
line_end = src.index('\n', iu)
line = src[iu:line_end]
for var in sys.argv[3].split('+'):
    if var.startswith('cap'):
        assert line.count("'max_hands': 15,") == 1
        line = line.replace("'max_hands': 15,", "'max_hands': %d," % int(var[3:]))
    elif var.startswith('ovf'):
        assert line.count("'ovf_value': 100.0,") == 1
        line = line.replace("'ovf_value': 100.0,", "'ovf_value': %.1f," % float(var[3:]))
    elif var.startswith('keep'):
        kk = var[4:]
        cls = ''.join(ch for ch in kk if ch.isalpha())
        k = float(kk.rstrip('AOG'))
        cond = 'self._shed_keeps(_t, day)'
        if cls:
            # restrict the keepable classes: A animals, O ongoing crops, G one-time crops (keepK<classes>, e.g. keep5G)
            parts = []
            if 'A' in cls: parts.append('("animal" in _t)')
            if 'O' in cls: parts.append('(_t.get("kind") == "PLANT" and _GC_CROPS.get(_t.get("crop"), {}).get("on"))')
            if 'G' in cls: parts.append('(_t.get("kind") == "PLANT" and not _GC_CROPS.get(_t.get("crop"), {}).get("on", True))')
            cond = 'self._shed_keeps(_t, day) and (' + ' or '.join(parts) + ')'
        # 1. the day plan stashes its tile grid for the hire search
        a = "        routes, hires, spawns = self._route_and_hire(visits, money - spend, final, day)\n"
        assert src.count(a) == 1
        src = src.replace(a, "        self._kv_tiles = tiles\n" + a)
        # 2. the hire search prices keepable overflow at k
        head = "    def _route_and_hire(self, visits, cash, final, day):\n"
        i0 = src.index(head)
        a2 = '                pen += ovf * GC_P["ovf_value"] + popped\n'
        i2 = src.index(a2, i0)
        rep = ('                _kv_keep = 0\n'
               '                if ovf > 0 and getattr(self, "_kv_tiles", None) is not None:\n'
               '                    for _r in rr:\n'
               '                        _ls = max((i for i, _v in enumerate(_r) if _v.tag == "S"), default=-1)\n'
               '                        for _v in _r[_ls + 1:]:\n'
               '                            if _v.carry > 0:\n'
               '                                _t = self._kv_tiles[_v.pos[1]][_v.pos[0]]\n'
               '                                try:\n'
               '                                    if %s:\n' % cond +
               '                                        _kv_keep += int(_t.get("yield_units", 0) or 0)\n'
               '                                except Exception:\n'
               '                                    pass\n'
               '                _kv_k = min(ovf, _kv_keep)\n'
               '                pen += (ovf - _kv_k) * GC_P["ovf_value"] + _kv_k * %.1f + popped\n' % k)
        src = src[:i2] + rep + src[i2 + len(a2):]
    else:
        raise SystemExit('unknown variant ' + var)
src = src[:iu] + line + src[line_end:]
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('ok', sys.argv[3])
