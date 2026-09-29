"""build_nmp.py OUT OVERRIDES_JSON : the "student" = c2tr_final.py, where a 960-band rival (step-1 money 940-980, no hands:
the top teams' new-meta C2S3 lineage) goes to the p1e opening controller (not the tape) with c2tr's opening profile updated
by OVERRIDES (new-meta targets); every other rival is routed exactly as in c2tr."""
import sys, json
out, over = sys.argv[1], json.loads(sys.argv[2])
base = open('gold/final/c2tr_final.py', encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in base else '\n'
section = '''
# =====================================================================================================================
# >>> NMP (new-meta student): vs a 960-band rival the p1e opening controller plays with a new-meta profile (overrides below)
# =====================================================================================================================
_NMP_OVER = %(over)r
_NMP_BAND = (940.0, 980.0)
_NMP_ORIG_OPR_ROUTE = _opr_route


def _opr_route(obs):
    op = GC_P.get("open")
    if isinstance(op, dict) and op.get("route") and "cls" not in _OPR:
        try:
            rf = obs["farms"][1 - int(obs["player"])]
            m = float(rf["money"]); h = len(rf["hands"])
        except Exception:
            m, h = -1.0, -1
        if h == 0 and _NMP_BAND[0] <= m <= _NMP_BAND[1] and _GC.open is not None:
            _OPR["cls"] = "C2S3nm"
            _GC_REPORT["gc_route"] = "C2S3nm"
            _GC_REPORT["gc_route_obs"] = "%%d/%%d" %% (int(m), h)
            _GC.open.update(json.loads(json.dumps(_NMP_OVER)))
            GC_P["start"] = 1
            return
    return _NMP_ORIG_OPR_ROUTE(obs)


_nmp_submission_agent = agent   # the loader and Kaggle take the last callable defined in the module
''' % dict(over=over)
open(out, 'w', encoding='utf-8', newline='').write(base + section.replace('\n', nl))
print('wrote', out)
