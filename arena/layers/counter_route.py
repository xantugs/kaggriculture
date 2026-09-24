

# =====================================================================================
# Counter-routing against the public route-0 chassis family.
# Through day 5 every agent of this family plays the same opening (route 0), so its farm
# layout matches ours tile for tile. If the rival's layout (weeds ignored) and hand count
# have matched ours at every checkpoint up to step 143, the rival is taken to be a
# route-0 chassis that will pick the family's default tape for the day-6 shop pair; in
# that case we switch to the tape measured to beat that default for this pair.
# Against anything else the inherited router is untouched.
# =====================================================================================
_CR_TABLE = __TABLE__
_CR_CHECKS = (48, 96, 120, 143)
_CR_STATE = {}
_CR_REPORT = dict(mirror=0, switched=0, errors=0)


def _cr_sig(farm):
    out = []
    for row in farm.get("tiles") or []:
        for t in row:
            if t is None or (isinstance(t, dict) and t.get("kind") == "WEED"):
                out.append(".")
            elif t == "LOCKED":
                out.append("#")
            elif isinstance(t, dict):
                out.append(str(t.get("crop") or t.get("animal") or t.get("kind")))
            else:
                out.append("?")
    return tuple(out)


_CR_ORIG_ROUTER = _IMPL.chassis.router


def _cr_router(observation, step, state):
    route = _CR_ORIG_ROUTER(observation, step, state)
    try:
        seat = int(observation["player"])
        st = _CR_STATE.get(seat)
        if st is None or step < st.get("last", -1):
            st = {"mirror": True, "last": -1, "choice": None}
            _CR_STATE[seat] = st
        st["last"] = step
        if step in _CR_CHECKS and step < 144:
            me = observation["farms"][seat]
            op = observation["farms"][1 - seat]
            same = _cr_sig(me) == _cr_sig(op) and len(me.get("hands") or []) == len(op.get("hands") or [])
            st["mirror"] = st["mirror"] and same
        if 144 <= step < 648:
            if st["choice"] is None:
                st["choice"] = -1
                if st["mirror"]:
                    _CR_REPORT["mirror"] += 1
                    shops = tuple((observation["town"]["unlocked_shops"] or [])[:2])
                    pick = _CR_TABLE.get("|".join(shops))
                    if pick is not None:
                        st["choice"] = int(pick)
                        _CR_REPORT["switched"] += 1
            if st["choice"] >= 0:
                state["route"] = st["choice"]
                return st["choice"]
    except Exception:
        _CR_REPORT["errors"] += 1
    return route


_IMPL.chassis.router = _cr_router
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
