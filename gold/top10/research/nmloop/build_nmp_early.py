"""build_nmp_early.py OUT OVER REVERT THR CAP FROM_DAY MINB EK SELL_THR: NMp44 (build_nmp_d15.py) plus, in towns with exactly 1
strawberry buyer visible on days 3-6, EK strawberry plots moved from the NE batch into days 4-5 (straw_hf early +EK/2 on day 4,
+EK from day 5; ne[0] - EK: the total target is unchanged); and, with SELL_THR > 0, on days 14-18 while at most 1 strawberry buyer
is visible, the shed's strawberries are sold at once while the marginal quote stays >= SELL_THR (first market order).
From build_nmp_d15.py: NMp37 (cap gate) plus a late strawberry top-up: from FROM_DAY through day 15,
once at least 3 of the unlocked shops buy strawberries, the opening plants strawberries up to CAP standing plots on its free and
replant tiles (straw_last 15, straw_max CAP, straw_hf late +30: the target becomes the cap; strawberries take the free tiles ahead
of melons and wheat). Derived from build_nmp_cap.py (capital gate: revert when our MELON plants at step 144 >= DAIRY_MIN, i.e. the day-10/11 payout is already funded); derived from build_nmp_guard.py OUT OVERRIDES_JSON REVERT_JSON DAIRY_MIN : like build_nmp.py (960 band -> p1e controller with OVERRIDES),
plus a day-6 dairy guard: at step 144, if at least DAIRY_MIN of the first two town shops buy milk (PIZZA_SHOP, ICE_CREAM_SHOP,
SMOOTHIE_SHOP), the opening profile is updated with REVERT (back to NMp1's values) for the rest of the opening."""
import sys, json
out, over, revert, dmin, cap, d0 = sys.argv[1], json.loads(sys.argv[2]), json.loads(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
minb = int(sys.argv[7])
ek, sthr = int(sys.argv[8]), float(sys.argv[9])
base = open('gold/final/c2tr_final.py', encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in base else '\n'
section = '''
# =====================================================================================================================
# >>> NMP + day-6 dairy guard (student): 960 band -> p1e controller with the overrides; a milk town at day 6 reverts them
# =====================================================================================================================
_NMP_OVER = %(over)r
_NMP_REVERT = %(revert)r
_NMP_DAIRY_MIN = %(dmin)d
_NMP_SCAP = %(cap)d
_NMP_SD0 = %(d0)d
_NMP_SMINB = %(minb)d
_NMP_EK = %(ek)d
_NMP_STHR = %(sthr)r
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


_NMPG_PARENT = agent


def agent(observation, configuration=None):
    try:
        if int(observation["step"]) == 144 and _OPR.get("cls") == "C2S3nm" and _GC.open is not None:
            me_ = int(observation["player"])
            n_d = sum(1 for row in observation["farms"][me_]["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
            _GC_REPORT["nmp_melons6"] = n_d
            if n_d >= _NMP_DAIRY_MIN:
                _GC.open.update(json.loads(json.dumps(_NMP_REVERT)))
                _GC_REPORT["nmp_revert"] = 1
        st_ = int(observation["step"])
        if 24 * _NMP_SD0 <= st_ < 384 and _OPR.get("cls") == "C2S3nm" and _GC.open is not None and not _GC_REPORT.get("nmp_straw_top"):
            shops_ = list(_gc_get(observation["town"], "unlocked_shops", []) or [])
            nb_ = sum(1 for s_ in shops_ if s_ in _OPEN_BUYERS["straw"])
            if nb_ >= _NMP_SMINB:
                sh_ = dict(_GC.open.get("straw_hf") or {})
                sh_["late"] = [30, 0, st_ // 24]
                _GC.open.update({"straw_hf": sh_, "straw_last": 15, "straw_max": _NMP_SCAP})
                _GC_REPORT["nmp_straw_top"] = st_
        if _NMP_EK > 0 and 72 <= st_ < 168 and _OPR.get("cls") == "C2S3nm" and _GC.open is not None and not _GC_REPORT.get("nmp_early"):
            shops_ = list(_gc_get(observation["town"], "unlocked_shops", []) or [])
            if sum(1 for s_ in shops_ if s_ in _OPEN_BUYERS["straw"]) == 1:
                sh_ = json.loads(json.dumps(_GC.open.get("straw_hf") or {}))
                e_ = {int(k): v for k, v in (sh_.get("early") or {}).items()}
                sh_["early"] = {"4": e_.get(4, 0) + _NMP_EK // 2, "5": e_.get(5, 0) + _NMP_EK}
                ne_ = list(sh_.get("ne") or [7, 7]); ne_[0] = ne_[0] - _NMP_EK; sh_["ne"] = ne_
                _GC.open["straw_hf"] = sh_
                _GC_REPORT["nmp_early"] = st_
    except Exception as e:
        _GC_REPORT["nmp_guard_err"] = repr(e)[:80]
    act = _NMPG_PARENT(observation, configuration)
    try:
        st_ = int(observation["step"])
        if _NMP_STHR > 0 and 336 <= st_ < 456 and _OPR.get("cls") == "C2S3nm" and isinstance(act, dict):
            shops_ = list(_gc_get(observation["town"], "unlocked_shops", []) or [])
            if sum(1 for s_ in shops_ if s_ in _OPEN_BUYERS["straw"]) <= 1:
                have = int((observation["private"]["shed"] or {}).get("STRAWBERRY", 0))
                inv0 = int(observation["market"]["inventory"]["STRAWBERRY"])
                k = 0
                while k < have and _gc_price("STRAWBERRY", inv0 + k) >= _NMP_STHR:
                    k += 1
                if k > 0:
                    mk = [o for o in (act.get("market") or []) if not (isinstance(o, list) and len(o) >= 2 and o[0] == "SELL" and o[1] == "STRAWBERRY")]
                    act = dict(act, market=([["SELL", "STRAWBERRY", k]] + mk)[:10])
                    _GC_REPORT["nmp_sell_early"] = _GC_REPORT.get("nmp_sell_early", 0) + k
    except Exception as e:
        _GC_REPORT["nmp_sell_err"] = repr(e)[:80]
    return act


_nmpe_submission_agent = agent   # the loader and Kaggle take the last callable defined in the module
''' % dict(over=over, revert=revert, dmin=dmin, cap=cap, d0=d0, minb=minb, ek=ek, sthr=sthr)
open(out, 'w', encoding='utf-8', newline='').write(base + section.replace('\n', nl))
print('wrote', out)
