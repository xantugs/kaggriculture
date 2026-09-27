"""Trace the controller's crop choices per day in a pinned game.
usage: plant_trace.py cand.py gid [S] [day_from]"""
import sys, os, json, collections, io, contextlib
sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/arena')
import pinned4, lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K

def load_module(path):
    g = {"__name__": "traced_agent", "__file__": path}
    sys.path.append(os.path.dirname(os.path.abspath(path)))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), g)
    return g, [v for v in g.values() if callable(v)][-1]

def main():
    cand, gid = sys.argv[1], int(sys.argv[2]); S = int(sys.argv[3]) if len(sys.argv) > 3 else 288; d0 = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    for path in ['moon/strong2800.json', 'moon/strong_new.json']:
        games = json.load(open(path)); d = next((g for g in games if g['id'] == gid), None)
        if d: break
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, rref = pinned4.reference(d)
    orig = pinned4.install_pinned(S // 24, O, spawns, shops)
    g, A = load_module(cand); cls = g['GoldCtl']; log = []
    oc = cls._choose_crops
    def traced(self, obs, day, free, replant, shops_, val, counts):
        out = oc(self, obs, day, free, replant, shops_, val, counts)
        fert = self.pnow.get("FERTILIZER", 50)
        vw = (6 * val["WHEAT"] - 10 - fert) / 4.0; vc = (4 * val["CARROT"] - 20 - fert) / 3.0
        ci = None
        try: ci = self._carrot_book_at_harvest(obs, day, shops_)
        except Exception as e: ci = repr(e)[:40]
        log.append((day, len(free), len(replant), dict(collections.Counter(out.values())), round(vw), round(vc), val.get("WHEAT"), val.get("CARROT"), round(fert), ci, int(obs["market"]["inventory"]["CARROT"]), dict(counts)))
        return out
    cls._choose_crops = traced
    oh = cls.plan_day; hl = []
    def pd(self, obs):
        r = oh(self, obs)
        hl.append((int(obs["day"]), len(obs["farms"][self.me]["hands"]), getattr(self, "n_hires", None), int(obs["farms"][self.me]["money"])))
        return r
    cls.plan_day = pd
    try:
        ag = [None, None]; ag[P] = pinned4._prefixed(A, d['acts'], P, S); ag[O] = pinned4._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    print('gid', gid, 'opp', names[O], 'result us %.0f them %.0f margin %+.0f' % (r['r'][P], r['r'][O], r['r'][P] - r['r'][O]))
    print('day free replant  planted                         v_wheat v_carrot pxW pxC fert  carrot_book_at_harvest  carrot_inv  counts')
    for row in log:
        if row[0] >= d0: print('%3d %4d %6d   %-32s %5s %6s %4s %4s %4s  %s  %s  %s' % row)
    print('plan_day: (day, hands at plan, n_hires, money)', [h for h in hl if h[0] >= d0])
if __name__ == '__main__':
    main()
