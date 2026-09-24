# ---------------------------------------------------------------------------
# Local modification (Apache-2.0 notice) by offhand, 2026-09-22.
# WFEED: a unit that picks up wheat at the shed takes enough for the FEEDs the
# tape gives it before its next wheat pickup.  The tape counts on wheat from its
# own harvests on the way; a tile the carrot swap turned into carrots yields none,
# the FEED fails, and an animal unfed two days running escapes.
# ---------------------------------------------------------------------------
_WF_CFG = _WF_CFG_PLACEHOLDER
_WF_PARENT = agent
_WF_REPORT = {"wf_changes": 0, "wf_units": 0, "wf_errors": 0}
_WF_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def _wf_act(obs, action):
    step = int(obs["step"]); player = int(obs["player"]); day = step // 24
    if not _WF_CFG.get("from", 144) <= step < _WF_CFG.get("to", 696):
        return action
    native = _IMPL.chassis.players[player]
    farm = obs["farms"][player]; private = obs["private"]
    pos = [farm["farmer"]] + list(farm.get("hands") or [])
    cmds = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    shed_wheat = int(private["shed"].get("WHEAT", 0))
    taken = sum(max(0, int(c[2]) if len(c) > 2 else 1) for c in cmds if isinstance(c, list) and c[:2] == ["PICKUP", "WHEAT"])
    spare = shed_wheat - taken
    changed = False
    for i in range(min(len(pos), len(cmds))):
        c = cmds[i]
        if not (isinstance(c, list) and c[:2] == ["PICKUP", "WHEAT"]):
            continue
        q = max(0, int(c[2]) if len(c) > 2 else 1)
        inv = private["inventories"][i] if i < len(private["inventories"]) else {}
        have = int(inv.get("WHEAT", 0)) + q
        x, y = pos[i]; feeds = 0; income = 0
        for t in range(step + 1, (day + 1) * 24):
            tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
            if t >= len(tape):
                break
            u = [tape[t].get("farmer") or ["PASS"]] + list(tape[t].get("hands") or [])
            if i >= len(u):
                break
            cc = u[i] or ["PASS"]
            if cc[0] in _WF_MOVES:
                dx, dy = _WF_MOVES[cc[0]]; x = min(9, max(0, x + dx)); y = min(9, max(0, y + dy))
            elif cc[:2] == ["PICKUP", "WHEAT"] or cc[0] == "DROP" or cc[:2] == ["PLACE", "WHEAT"]:
                break
            elif cc[0] == "FEED":
                feeds += 1
            elif cc[0] == "HARVEST":
                tl = farm["tiles"][y][x]
                if isinstance(tl, dict) and tl.get("kind") == "PLANT" and tl.get("crop") == "WHEAT":
                    income += max(1, int(tl.get("yield_units", 0)))
        deficit = feeds - (have + income)
        add = min(deficit, spare, _WF_CFG.get("max_add", 3))
        if add > 0:
            cmds[i] = ["PICKUP", "WHEAT", q + add]
            spare -= add; changed = True
            _WF_REPORT["wf_changes"] += 1; _WF_REPORT["wf_units"] += add
    if not changed:
        return action
    out = dict(action); out["farmer"] = cmds[0]; out["hands"] = cmds[1:]
    return out


def agent(observation, configuration=None):
    action = _WF_PARENT(observation, configuration)
    try:
        if isinstance(action, dict):
            action = _wf_act(observation, action)
    except Exception:
        _WF_REPORT["wf_errors"] += 1
    return action


agent.telemetry = _WF_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
