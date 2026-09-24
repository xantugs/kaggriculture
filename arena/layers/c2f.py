# ---------------------------------------------------------------------------
# Local modification (Apache-2.0 notice) by offhand, 2026-09-22.
# C2F: turn CARE actions that cannot pay into COLLECT_FERTILIZER on the same tile.
#  * dup:  the animal was already cared for today (the CARE is a no-op);
#  * late: the care bonus would only land on a production after day 28, whose
#          product can no longer be harvested and sold.
# Only when the tile's fertilizer is still available and no other unit collects it
# this turn.  Units keep their positions, so the parent's schedule is unchanged.
# ---------------------------------------------------------------------------
_C2F_CFG = _C2F_CFG_PLACEHOLDER
_C2F_PARENT = agent
_C2F_REPORT = {"c2f_dup": 0, "c2f_late": 0, "c2f_errors": 0}
_C2F_ANIMALS = {"GOOSE": (4, 1), "COW": (8, 2), "SHEEP": (6, 3)}   # first_yield_day, interval


def _c2f_useful(tile, day, last_day):
    fyd, iv = _C2F_ANIMALS.get(tile.get("animal"), (0, 1))
    placed = int(tile.get("placed_day", 0))
    e = day + 1
    while e <= last_day:
        ds = e + 1 - placed - fyd
        if ds >= 0 and ds % iv == 0:
            return True
        e += 1
    return False


def _c2f_act(obs, action):
    step = int(obs["step"])
    day = step // 24
    if step >= _C2F_CFG.get("to", 696) or step < _C2F_CFG.get("from", 0):
        return action
    farm = obs["farms"][int(obs["player"])]
    pos = [farm["farmer"]] + list(farm.get("hands") or [])
    cmds = [action.get("farmer")] + list(action.get("hands") or [])
    n = min(len(pos), len(cmds))
    claimed = set()
    for i in range(n):
        c = cmds[i]
        if isinstance(c, list) and c and c[0] == "COLLECT_FERTILIZER":
            claimed.add(tuple(pos[i]))
    cared = set()
    changed = False
    for i in range(n):
        c = cmds[i]
        if not (isinstance(c, list) and c and c[0] == "CARE"):
            continue
        p = tuple(pos[i])
        t = farm["tiles"][p[1]][p[0]]
        if not (isinstance(t, dict) and "animal" in t):
            continue
        dup = bool(t.get("cared_today")) or p in cared
        late = (day >= _C2F_CFG.get("late_day", 27)) and not _c2f_useful(t, day, _C2F_CFG.get("last_day", 28))
        if t.get("fertilizer_available") and p not in claimed and ((dup and _C2F_CFG.get("dup", True)) or (late and _C2F_CFG.get("late", True))):
            cmds[i] = ["COLLECT_FERTILIZER"]
            claimed.add(p)
            changed = True
            _C2F_REPORT["c2f_dup" if dup else "c2f_late"] += 1
        else:
            cared.add(p)
    if not changed:
        return action
    out = dict(action)
    out["farmer"] = cmds[0]
    out["hands"] = cmds[1:]
    return out


def agent(observation, configuration=None):
    action = _C2F_PARENT(observation, configuration)
    try:
        if isinstance(action, dict):
            action = _c2f_act(observation, action)
    except Exception:
        _C2F_REPORT["c2f_errors"] += 1
    return action


agent.telemetry = _C2F_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
