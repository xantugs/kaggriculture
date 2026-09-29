"""build_nm1.py SRC_GAME SRC_SEAT OUT [UNTIL] : the NM1 "teacher" candidate = c2tr_final.py + a new-meta opening specialist.

Against a rival that shows the new-meta step-1 fingerprint (money 940-980, no hands: the 960 band of the top teams' C2S3
lineage), our seat replays a recorded top-team new-meta opening (steps 1..UNTIL-1 of SRC_SEAT in SRC_GAME, from the temporal
corpus) through the chassis repair layers, and c2tr's own controller (GoldCtl) takes over at its start step, forced to
UNTIL (day 16) through GC_P['start_div2'] (the step-2 cash rule, which only reads the rival). c2tr keeps running underneath
every step so its trackers and forecast history see the whole game; its actions are used from the takeover on. Every other
rival: c2tr unchanged.

Step alignment: both lineages PASS the farmer at step 0, so our units stand where the source's did. Our step 0 is still
c2tr's (the rival is unknown then); the source's step-0 market (cow, 3 sheep, 5 wheat) is merged into step 1 and the
source's step-1 cow moves to step 2, which leaves the shed at step 2 exactly as in the source (only the farmer's step-1
cow pickup is lost)."""
import sys, os, json, gzip, zlib, base64
src_game, src_seat, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
until = int(sys.argv[4]) if len(sys.argv) > 4 else 384
g = json.load(gzip.open(src_game, 'rt', encoding='utf-8'))
acts = g['acts']
PASS = {"farmer": ["PASS"], "hands": [], "market": []}
tape = []
for t in range(until):
    a = acts[t + 1][src_seat] if t + 1 < len(acts) and isinstance(acts[t + 1], list) and len(acts[t + 1]) > src_seat else None
    tape.append(a if isinstance(a, dict) else dict(PASS))
m0 = [list(o) for o in tape[0].get('market', [])]
m1 = [list(o) for o in tape[1].get('market', [])]
cows0 = sum(int(o[2]) for o in m0 if o[:2] == ['BUY_ANIMAL', 'COW'])
sheep0 = sum(int(o[2]) for o in m0 if o[:2] == ['BUY_ANIMAL', 'SHEEP'])
other0 = [o for o in m0 if o[0] != 'BUY_ANIMAL']
cows1 = sum(int(o[2]) for o in m1 if o[:2] == ['BUY_ANIMAL', 'COW'])
rest1 = [o for o in m1 if o[:2] != ['BUY_ANIMAL', 'COW']]
merged1 = ([['BUY_ANIMAL', 'COW', cows0]] if cows0 else []) + ([['BUY_ANIMAL', 'SHEEP', sheep0]] if sheep0 else []) + other0 + rest1
assert len(merged1) <= 10, merged1
tape[1] = dict(tape[1], market=merged1)
tape[2] = dict(tape[2], market=[list(o) for o in tape[2].get('market', [])] + ([['BUY_ANIMAL', 'COW', cows1]] if cows1 else []))
assert len(tape[2]['market']) <= 10, tape[2]['market']
tape[0] = dict(PASS)
blob = base64.b85encode(zlib.compress(json.dumps(tape, separators=(',', ':')).encode(), 9)).decode()

base = open('gold/final/c2tr_final.py', encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in base else '\n'
section = '''
# =====================================================================================================================
# >>> NM1 (new-meta opening specialist, teacher): vs a 960-band rival (step-1 money 940-980, no hands), replay a recorded
# top-team new-meta opening (source: %(src)s seat %(seat)d, steps 1..%(until)d) through the chassis repair layers; c2tr's
# controller takes over at its start step (forced to %(until)d via start_div2). c2tr runs underneath every step.
# =====================================================================================================================
_NM1_TAPE = json.loads(zlib.decompress(base64.b85decode(%(blob)r)).decode())
_NM1_TAPE = _NM1_TAPE + [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(720 - len(_NM1_TAPE))]
_NM1_UNTIL = %(until)d
_NM1_BAND = (940.0, 980.0)
_NM1_CH = Chassis({"nm1": _NM1_TAPE}, None, {"hand_align": True, "weed_repair": True, "sell_lead": True, "front_run": False,
                                            "budget_guard": True, "room_guard": True, "clamp_sells": True,
                                            "dead_stock": False, "terminal_liquidation": False})
_NM1_PARENT = agent
_NM1_ST = {}


def agent(observation, configuration=None):
    step = int(observation["step"]); me = int(observation["player"])
    st = _NM1_ST.get(me)
    if st is None or step == 0 or step <= st["last"]:
        st = _NM1_ST[me] = {"on": None, "last": -1}
    st["last"] = step
    if step == 1 and st["on"] is None:
        try:
            rv = observation["farms"][1 - me]
            st["on"] = bool(_NM1_BAND[0] <= float(rv["money"]) <= _NM1_BAND[1] and len(rv.get("hands") or []) == 0)
        except Exception:
            st["on"] = False
        _GC_REPORT["nm1_on"] = int(st["on"])
    if st.get("on"):
        GC_P["start_div2"] = _NM1_UNTIL
    act = _NM1_PARENT(observation, configuration)
    if st.get("on") and 1 <= step < _NM1_UNTIL:
        gs = _GC_REPORT.get("gc_start")
        if isinstance(gs, int) and step >= gs:
            _GC_REPORT["nm1_handover"] = _GC_REPORT.get("nm1_handover") or step
            return act
        try:
            return _NM1_CH.act(observation, configuration)
        except Exception as e:
            _GC_REPORT["nm1_err"] = repr(e)[:120]
            return act
    return act


_nm1_submission_agent = agent   # the loader and Kaggle take the last callable defined in the module
''' % dict(src=os.path.basename(src_game), seat=src_seat, until=until, blob=blob)
open(out, 'w', encoding='utf-8', newline='').write(base + section.replace('\n', nl))
print('wrote', out, len(base), '->', len(base) + len(section), 'bytes; tape steps', until, '; step1 market', merged1, '; step2 market', tape[2]['market'])
