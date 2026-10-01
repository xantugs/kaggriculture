"""Evaluation-only engine patch: from day FROM on, the daily RNG no longer couples the two farms and the town.
Kaggle's engine draws weeds for farm 0, then farm 1, then the new shop from ONE random stream seeded by (seed, day),
consuming one draw per empty tile, so any change in how many tiles we leave empty re-draws the opponent's weeds and
every future shop.  Here weeds use a per-player stream and the shop draw its own stream, so a candidate and its
baseline see the same town and the opponent the same weeds.  Before day FROM the original engine runs unchanged."""
import random
from kaggle_environments.envs.kaggriculture import kaggriculture as K
_ORIG = K._end_of_day
FROM = [10 ** 9]
def _eod(state, env, day):
    if day < FROM[0]:
        return _ORIG(state, env, day)
    obs0 = state[0].observation
    cfg = env.configuration
    board_size = int(K.get(cfg, "boardSize", 10))
    turns_per_day = max(1, int(K.get(cfg, "turnsPerDay", 24)))
    weed_chance = float(K.get(cfg, "weedSpawnChance", 0.005))
    shed_cap = int(K.get(cfg, "shedCapacity", 100))
    shop_interval = max(1, int(K.get(cfg, "townShopUnlockInterval", 3)))
    seed = env.info.get("seed", 0)
    for player_id, farm in enumerate(obs0.farms):
        private = state[player_id].observation.private
        K._daily_refresh_plants(farm, day, turns_per_day)
        K._daily_refresh_animals(farm, day)
        rng = random.Random((seed * 1_000_003) ^ (day * 7919) ^ ((player_id + 1) * 104_729))
        K._spawn_weeds(farm, board_size, weed_chance, rng)
        K._drop_inventories_to_shed(private, shed_cap)
        farm["farmer"] = list(K._default_spawn(board_size))
        farm["hands"] = []
        farm["hires_today"] = 0
        private["inventories"] = [{}]
    next_day = day + 1
    town = obs0.town
    if next_day > 0 and next_day % shop_interval == 0:
        if len(town["unlocked_shops"]) < K.MAX_SHOP_INSTANCES:
            rng = random.Random((seed * 1_000_003) ^ (day * 7919) ^ 15_485_863)
            town["unlocked_shops"].append(rng.choice(sorted(K.SHOPS)))
def install(from_day):
    FROM[0] = from_day
    K._end_of_day = _eod
