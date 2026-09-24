# Verify key mechanics directly against the real simulator functions (not my reading of them).
import copy
from kaggle_environments.envs.kaggriculture import kaggriculture as K

def fresh_farm():
    f = K._new_farm(10, 3000); p = K._new_private(); return f, p

# --- 1. Care banking before first production: what does a cared-for animal give at first yield? ---
print("== first-production size with daily FEED+CARE from placement ==")
for animal in ("GOOSE", "COW", "SHEEP"):
    f, p = fresh_farm()
    f["tiles"][4][4] = K._new_animal(animal, 0)
    log = []
    for day in range(0, 14):
        t = f["tiles"][4][4]
        t["fed_today"] = True; t["cared_today"] = True
        K._daily_refresh_animals(f, day)
        t = f["tiles"][4][4]
        log.append((day + 1, t["yield_units"]))
        if t["yield_units"]:
            t["yield_units"] = 0  # harvest each morning
    print(f"  {animal:6s} morning-of-day -> units harvested:", [(d, u) for d, u in log if u])

# --- 2. No care, feed every other day: does it survive and produce? ---
print("== goose, feed every OTHER day, no care ==")
f, p = fresh_farm(); f["tiles"][4][4] = K._new_animal("GOOSE", 0); out = []
for day in range(0, 12):
    t = f["tiles"][4][4]
    if "animal" not in t: out.append("ESCAPED"); break
    t["fed_today"] = (day % 2 == 1)
    K._daily_refresh_animals(f, day)
    t = f["tiles"][4][4]; out.append(t.get("yield_units")); 
    if t.get("yield_units"): t["yield_units"] = 0
print("  per-morning eggs:", out)

# --- 3. Crop yields under different watering schedules ---
def grow(crop, water_days, fert_day=None, harvest_age=None):
    f, p = fresh_farm(); p["seeds"][crop] = 1; p["inventories"][0]["FERTILIZER"] = 1
    K._apply_unit_action(f, p, 0, ["PLANT", crop], 10, 0, 24)
    for day in range(0, 20):
        t = f["tiles"][4][4]
        if not (isinstance(t, dict) and t.get("kind") == "PLANT"): return f"DIED(day {day}: {t})"
        if fert_day == day: K._apply_unit_action(f, p, 0, ["FERTILIZE"], 10, day, 24)
        if day in water_days: K._apply_unit_action(f, p, 0, ["WATER"], 10, day, 24)
        if harvest_age is not None and day == harvest_age:
            return f["tiles"][4][4]["yield_units"]
        K._daily_refresh_plants(f, day, 24)
print("== one-time crop yields ==")
print("  wheat  water d0,2,3,4 harvest d4      :", grow("WHEAT", {0,2,3,4}, harvest_age=4))
print("  wheat  water d0,2,4   harvest d4      :", grow("WHEAT", {0,2,4}, harvest_age=4))
print("  wheat  +fert d2, harvest d3           :", grow("WHEAT", {0,2,3}, fert_day=2, harvest_age=3))
print("  carrot water d0,2,3   harvest d3      :", grow("CARROT", {0,2,3}, harvest_age=3))
print("  melon  water d0,2,4,6-10 harvest d10  :", grow("MELON", {0,2,4,6,7,8,9,10}, harvest_age=10))
print("  melon  same, but look at morning d10  :", grow("MELON", {0,2,4,6,7,8,9}, harvest_age=10), "(units available at hour 0 of day 10, before watering)")
print("  melon  +1 fert on d8                  :", grow("MELON", {0,2,4,6,7,8,9}, fert_day=8, harvest_age=10), "(at hour 0 of day 10)")
print("  melon  never watered after d0         :", grow("MELON", {0}, harvest_age=10))

print("== hire cost: cumulative $ for H hands/day ==")
print("  ", {h: sum(K._fib(i) for i in range(h)) for h in (4, 8, 10, 11, 12, 13, 14, 15, 16)})
