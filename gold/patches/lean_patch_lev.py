"""Add harvest-wave leveling (eh_level, g_wheat track) to a lean build: lean_patch_lev.py in.py out.py [all|div] [json]
all (default): eh_level at the top level of GC_P (every controller day, copies from day 24 too);
div: eh_level only in div_over and rich_over (ADAPT-flagged rivals and rich-town takeovers).
json: the eh_level dict (default {"margin": 2, "min_units": 5, "last_day": 26, "frac": 0.5}).
Same logic as gold/top10/full/ctl_wheat.py: when the one-time crops due tomorrow (wheat age 3, carrots age 2) outnumber
those due today by more than margin, frac of the excess is harvested today among the fertilized age-3 wheat that holds
min_units after today's water (nearest the shed first); those tiles are replanted today like any harvested tile."""
import sys, json
src = open(sys.argv[1], encoding='utf-8').read()
mode = sys.argv[3] if len(sys.argv) > 3 else 'all'
cfg = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {"margin": 2, "min_units": 5, "last_day": 26, "frac": 0.5}
nl = '\r\n' if '\r\n' in src else '\n'
src = src.replace('\r\n', '\n')

def rep(a, b):
    global src
    assert src.count(a) == 1, (a[:80], src.count(a))
    src = src.replace(a, b)

rep("""        visits = []
        replant = []
        for pos, t in plants:
            v = self._plant_visit(pos, t, day, val, final)
""", """        visits = []
        replant = []
        self._eh_set = set()
        ehl = GC_P.get('eh_level')
        if ehl and (not final) and day <= int(ehl.get('last_day', 26)):
            try:
                due_t = 0
                due_n = 0
                cand_w = []
                mu = int(ehl.get('min_units', 5))
                for pos_, t_ in plants:
                    c_ = t_['crop']
                    if c_ not in ('WHEAT', 'CARROT'):
                        continue
                    my_ = _GC_CROPS[c_]['my']
                    a_ = day - int(t_['planted_day'])
                    if a_ >= my_:
                        due_t += 1
                    elif a_ == my_ - 1:
                        due_n += 1
                        if c_ == 'WHEAT':
                            fa_ = int(t_.get('fertilized_until_day', -1)) >= day
                            yu_ = int(t_['yield_units']) + (2 if fa_ else 1)
                            if yu_ >= mu and (not t_.get('watered_today')):
                                cand_w.append(pos_)
                ex = due_n - due_t - int(ehl.get('margin', 2))
                if ex > 0 and cand_w:
                    k = min(len(cand_w), int(ex * float(ehl.get('frac', 0.5)) + 0.5))
                    self._eh_set = set(sorted(cand_w, key=lambda q: _gc_dist(q, (4.5, 4.5)))[:k])
                    _GC_REPORT['gc_eh_level'] = _GC_REPORT.get('gc_eh_level', 0) + len(self._eh_set)
            except Exception as e:
                _GC_REPORT['gc_eh_level_err'] = repr(e)[:120]
        for pos, t in plants:
            v = self._plant_visit(pos, t, day, val, final)
""")
rep("""            harvest_now = ready and yu2 > 0 and (age >= cd['my'] or yu2 >= cd['mx'])
""", """            harvest_now = ready and yu2 > 0 and (age >= cd['my'] or yu2 >= cd['mx'])
            if not harvest_now and ready and (yu2 > 0) and (pos in getattr(self, '_eh_set', ())) and (yu2 >= int((GC_P.get('eh_level') or {}).get('min_units', 5))):
                harvest_now = True
""")
anchor = "GC_P.update({'mkt_dp_d29': False, 'final_sell0': 3, 'final_cap': 19})\n"
if mode == 'all':
    rep(anchor, anchor + "GC_P.update({'eh_level': %r})\n" % (cfg,))
else:
    rep(anchor, anchor + "GC_P['div_over'] = dict(GC_P['div_over'], eh_level=%r)\nGC_P['rich_over'] = dict(GC_P['rich_over'], eh_level=%r)\n" % (cfg, cfg))
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(src.replace('\n', nl))
print('patched', sys.argv[2], mode, cfg)
