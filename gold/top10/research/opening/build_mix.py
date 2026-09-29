"""build_mix.py TAPE.py CTL.py OUT.py : one submission file that plays TAPE against every rival class the CTL build routes to its
own tape, and CTL otherwise. Both sources are embedded as string literals and executed in separate namespaces; step 0 is
TAPE's move (identical in all our builds); at step 1 the CTL build runs its router (_OPR['cls']) and the file keeps TAPE or CTL."""
import sys, ast
tape_src = open(sys.argv[1], encoding='utf-8').read().replace('\r\n', '\n')
ctl_src = open(sys.argv[2], encoding='utf-8').read().replace('\r\n', '\n')
out = '''# offhand mixed agent: %s against the rival classes the controller routes to its tape, the %s controller otherwise.
# Both agents are embedded below and executed in separate namespaces (pure Python, no I/O).
_SRC_TAPE = %r
_SRC_CTL = %r


def _mix_load(src, name):
    g = {"__name__": name}
    exec(compile(src, name, "exec"), g)
    return g, [v for v in g.values() if callable(v)][-1]


_TAPE_NS, _TAPE = _mix_load(_SRC_TAPE, "offhand_tape")
_CTL_NS, _CTL = _mix_load(_SRC_CTL, "offhand_ctl")
try:
    _MIX_ROUTE_TAPE = set(_CTL_NS["GC_P"]["open"]["route"]["tape"])
except Exception:
    _MIX_ROUTE_TAPE = None
_MIX = {"who": None}


def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _MIX["who"] = None
        a = _TAPE(observation, configuration)
        try:
            _CTL(observation, configuration)
        except Exception:
            pass
        return a
    if _MIX["who"] is None:
        a_ctl = None
        try:
            a_ctl = _CTL(observation, configuration)
            cls = _CTL_NS.get("_OPR", {}).get("cls")
            _MIX["who"] = "ctl" if (_MIX_ROUTE_TAPE is not None and cls is not None and cls not in _MIX_ROUTE_TAPE) else "tape"
        except Exception:
            _MIX["who"] = "tape"
        if _MIX["who"] == "ctl" and isinstance(a_ctl, dict):
            return a_ctl
        _MIX["who"] = "tape"
        return _TAPE(observation, configuration)
    if _MIX["who"] == "ctl":
        return _CTL(observation, configuration)
    return _TAPE(observation, configuration)


agent.telemetry = _MIX
''' % (sys.argv[1].split('/')[-1], sys.argv[2].split('/')[-1], tape_src, ctl_src)
ast.parse(out)
open(sys.argv[3], 'w', encoding='utf-8').write(out)
print('built', sys.argv[3], len(out), 'bytes')
