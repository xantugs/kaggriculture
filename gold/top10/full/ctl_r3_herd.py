
# =====================================================================================
# GOLD controller (offhand, 2026-09-24). From step GC_P['start'] (hour 0 of a day) this layer owns every
# unit and the market. Before that the chassis above plays unchanged.
# Each day at hour 0: value every tile job as the loss from deferring it a day, choose plantings/purchases,
# pick the number of hands by marginal value against the Fibonacci wage, build routes (angular sweep +
# nearest neighbour + 2-opt + cheapest insertion of overflow) that end with a delivery at the shed, then
# execute the routes turn by turn, skipping any action that would be a no-op. Everything in the shed
# beyond the feed/fertilizer reserve is sold every turn; the shed is kept clear for end-of-day drops.
# =====================================================================================
import math as _gc_math

GC_P = dict(
    start=288,            # takeover step (must be hour 0)
    open=None,            # dict: the controller plays from step 0 with a scheduled early game (see _OPEN_DEFAULT)
    start_div143=None,    # takeover step when ADAPT flagged the rival at step 143 already (else start_div)
    start_div=None,       # takeover step against a rival ADAPT classed as divergent (hour 0, >= 384)
    start_div2=None,      # takeover step when the step-2 cash rule (div2_band) classed the rival divergent (hour 0)
    div_over={},          # GC_P overrides applied for a divergent rival (restored at the next game's step 0)
    max_hands=12,
    animals_must=True,
    wheat_fert_gain=25.0,  # fertilize one-time crops only when the extra yield beats selling the fertilizer by this much
    wheat_last_plant=25,  # wheat planted on day d is ripe on day d+4
    carrot_last_plant=27,
    carrot_first=14,
    carrot_min_demand=1,
    wheat_feed_bonus=4.0,  # own wheat saves buying feed at the ask
    straw_last_plant=12,
    straw_target=33,      # strawberry plants to hold while planting them is allowed
    feed_reserve=1.0,     # wheat kept per animal for the next morning
    drop_refill=False,    # a unit that DROPs mid-queue (shed stop, courier) re-picks the wheat/fertilizer/animals the rest
                          # of its queue feeds/fertilizes/places (the engine's DROP empties the whole inventory: sf8 then
                          # skipped those FEEDs, and animals placed the day before escaped)
    fert_keep=6,
    fert_carrots=True,
    carrot_fert_gain=25.0,
    fert_res_extra=2,
    drip_on=True,
    drip={'STRAWBERRY': 6, 'MILK': 6, 'WOOL': 4, 'TOMATO': 6},
    drip_room=80,
    prem_drop=True,
    prem_drop_max=4,
    replant_done=False,
    replant_dig=False,
    dig_structs=True,     # an empty coop/pasture with no animal waiting is dug and planted    # a dig of a finished plant also replants the tile in the same visit
    feed_tiles_per_animal=0.75,
    feed_reserve_tiles=False,
    tomato_on=True,
    tomato_first=12,
    tomato_last=18,
    tomato_max_day=12,
    tomato_step=2,
    tomato_alt_day=35.0,
    tomato_labor=60.0,
    tomato_harvest_min=3,
    opp_tomato_w=1.0,
    future_shop_w=1.0,
    plant_must=True,
    plant_must_last=25,
    final_water=True,
    carrot_edge=1.0,
    lot_frac=0.0,         # >0: cap a timed lot where the marginal quote falls below this fraction of the current quote
    room0_v2=False,       # hour-0 room sales only for purchases, only the units needed, cheapest-to-sell first
    melon_on=False,       # forecast-driven melon plots (harvest ~11 days later)
    melon_last=18,
    melon_age=11,
    melon_max_day=10,
    melon_alt_day=40.0,
    melon_labor=60.0,
    carrot_fc=False,      # choose carrots per slot from the forecast quote at harvest (town drain, visible plots)
    carrot_fc_units=3.5,
    hire_cost_w=1.0,
    dispatch=True,
    dispatch_min_value=8.0,
    fert_cost_w=1.0,
    ongoing_fert_gain=10.0,
    feed_all=False,
    max_sell0=3,
    fert_buy_margin=20.0,
    trim_hour=10,
    trim_fix=False,       # _trim_queue gets the turns really left (hours h..23 = 24 - h; day 29 ends at hour 22): sf8 passed
                          # 23 - h and cut one planned visit from every full route that was exactly on time
    pick_fix=False,       # the market never sells the WHEAT/FERTILIZER that queued PICKUPs still need: sf8 kept only
                          # tomorrow's reserve, so the hour-1 sale sold the inputs of the hands hired at hour 1 (their
                          # pickups run at hour 2; on day 28 the reserve is 0 and everything went) and the hour-0 room
                          # lot sold below today's fert/wheat needs: FERTILIZE/FEED then popped as no-ops (day-28 escapes)
    plant23_fix=False,    # a PLANT that would run at the day's last turn (no turn left for its WATER: the new plant
                          # turns weed at the night refresh) is skipped with its WATER; the seed and the empty tile wait
    mtrim_fix=False,      # True or "surv" (strip only while a life-saving WATER/FEED would be lost, only parts before it). _trim_queue with only must visits left and still over the turns left (unplanned refill pickups,
                          # a late hire's actual spawn) strips their deferrable parts, latest first: fertilizer collects,
                          # fertilizations, plantings; sf8 ran the queue in order and lost its last must visits
    reserve_release_hour=18,
    care_min_price=12,
    anim_fwd_days=0.0,    # >0: care/harvest decisions price animal goods at the book after this many days of town drain (no sales)
    harvest_min_price=3,
    plant_defer=0.3,      # value of planting today = this fraction of the crop's net value
    eh_level=None,        # g_wheat: harvest-wave leveling, e.g. {"margin": 2, "min_units": 5, "last_day": 26, "frac": 0.5}: when the
                          # one-time crops due tomorrow (wheat age 3, carrots age 2) outnumber those due today by more than margin,
                          # harvest frac of the excess today among the age-3 wheat that holds min_units after today's water
                          # (nearest the shed first; replanted today). Splits the harvest/overflow wave that buys the 14th-15th hand.
    plant_last_w=None,    # g_wheat: on/after the last one-time planting day (max of wheat/carrot_last_plant) a planting is
                          # worth this fraction of the crop's value (deferring it loses the crop); None: plant_defer
    land_sw_day=11,
    drop_slack=0,         # turns kept free in each route for a shed stop
    always_drop=False,
    eod_room=88,
    prem_w=1.0,
    drop_after_animals=True,
    deliver_min=6,        # append a shed delivery when a route is expected to carry at least this many goods
    deliver_prem=0.0,     # >0: routes get a shed stop once they carry premium goods worth this much (sold the same day)
    deliver_prem_w=0.3,   # hire search: penalty per dollar of premium goods a plan leaves undelivered tonight
    hire_compact=False,   # hands the plan gives nothing to are not hired
    ovf_hire=True,        # hire search counts end-of-day shed overflow (goods lost) and visits popped for shed stops
    ovf_value=50.0,
    order_cap_fix=True,
    stop_v2=True,
    shed_any=True,        # pickups/drops at whichever shed-access tile the unit stands on
    water_first=True,     # ongoing-crop visits water (survival) before harvesting
    rematch=True,
    footprint=True,       # cap planted plots at the chassis's count at takeover (+ slack)
    footprint_slack=2,
    labor_cap=0,          # >0: cap new plots by a turns/day labour model instead of the takeover footprint
    labor_anim=5.3,
    labor_on=3.0,
    labor_one=4.2,
    multi_stop=True,      # a route may get several shed stops
    final_ret=False,      # day 29: plan routes including the return delivery against the hour-22 deadline
    final_cap=22,
    d28_cap=None,         # day 28: routes end with a delivery that lands by this hour (like day 29), else None
    final_sell0=0,        # day 29: sell this many top lots at hour 0 (ahead of the rival's hour-1 dump)
    late_sell0_day=99,    # from this day on (before day 29) sell late_sell0 top lots at hour 0 as well
    late_sell0=0,         # day 29: hour by which every route's final delivery must land (earlier sells before the rival's dump)
    final_by_value=False,  # day 29: routes/hires minimise the value left unserved (not the count of must visits)
    max_hands_final=15,
    d28_keep_carrots=False,  # day 28: leave age-2 carrots to grow into the final day
    final_flush=True,     # day 29: idle loaded units drop; dispatched jobs end with a drop
    d28_harvest_all=True,  # False: on day 28 leave still-growing one-time crops for the final day
    d28_zero_reserve=True,  # day 28 keeps no feed/fertilizer for the final day (nothing is fed or fertilized then)
    eod_room_d28=96,
    courier=True,         # execution-time shed drops when tonight's projected load would overflow the shed
    courier_hour=12,
    courier_min=4,
    courier_margin=2,
    courier_max_detour=8,
    sell_timing=False,    # hold premium lots and sell one turn before the rival's predicted sale
    timing_from_day=0,    # the timing hold applies from this day on (earlier days sell on arrival)
    timed=("STRAWBERRY", "MILK", "WOOL", "TOMATO"),
    rival_min_lot=2,
    rival_days=2,
    hold_max=23,
    hold_room=80,
    se_force_day=None,    # buy the SE quadrant at the first day plan on/after this day when cash allows (as land, no annex)
    se_force_fp=25,       # ... and raise the planting footprint by this many plots (else the new tiles stay unplanted)
    se_on=False,          # buy the SE quadrant as a tomato annex when the forecast pays for it
    se_first=12,
    se_last=17,
    se_plots=16,
    se_reserve=1500,
    se_margin=2000.0,
    sell_floor={},        # e.g. {'STRAWBERRY': 30}: hold a product while its quote is below this (until floor_last_day)
    floor_last_day=26,
    floor_marginal=False,  # cap each lot at the units whose marginal quote stays >= the floor
    floor_drain_aware=False,
    floor_rival_aware=False,  # with floor_drain_aware: the rival's last-day sales of p offset the drain  # hold below the floor only if the town drains the book back above it within floor_wait_days
    floor_wait_days=1.5,
    straw_fc=False,       # forecast-driven extra strawberry plots (town strawberry demand vs visible supply)
    straw_fc_last=17,     # last planting day (first production day+10, then every 2 days)
    straw_fc_max=30,      # extra plots per day at most
    straw_fc_step=2,
    straw_labor=90.0,     # labour per plot over its life (water, fertilize, 4 harvests)
    straw_alt_day=35.0,   # what the tile earns otherwise per day
    straw_units=2.0,      # units per production (fertilized)
    straw_opp_w=1.0,
    straw_our_w=1.0,      # calibrated on recorded rich towns: 0.9
    straw_future_w=1.0,   # weight of the expected strawberry demand from shops not yet open (trigger evaluation)
    straw_count_future_w=None,  # the same for choosing how many plots to add (None: straw_future_w)
    straw_replant=True,   # forecast strawberries may also take replant slots (else only free tiles)
    straw_lag=0,          # days between a production and its sale (calibrated: 1)
    se_straw=False,       # the SE quadrant as a strawberry annex when the forecast pays for land + plots
    se_straw_margin=2500.0,
    rich_start=None,      # take over at this step when the town is strawberry-rich (>= rich_min strawberry shops)
    rich_min=3,
    rich_steps=None,      # e.g. (288, 312, 336): re-check the rich rule at these steps until it fires
    rich_tom_min=0,       # > 0: also take over at the rich check when >= this many tomato buyers among the first four
    rich_tom_margin=2500.0,  # shops and the SE tomato annex clears this margin
    rich_tom_over={},
    v219x=False,          # size the chassis's day-18 SE tomato block (V219) by a tomato forecast (needs base_m7_t3)
    v219x_sizes=(10, 15, 20, 25),
    v219x_copy_n=10.0,    # tomato plants a rival without any yet is assumed to add on day 18 (a chassis copy's block)
    v219x_opp_w=1.0,
    v219x_worker_cost=300.0,  # one extra hand for a day (13th-14th hire)
    v219x_margin=1000.0,  # a bigger block must beat the 10-plant block by this much
    v219x_skip_below=None,  # no block at all when the 10-plant forecast (net of seeds and fertilizer) is below this
    v219x_margins=None,   # per size: {15: 1250, 20: 3500} = the largest size whose forecast beats 10 plants by its margin
    v219x_units=2.0,
    v219x_thirst=False,   # base_m7_t4: growth-day crews water only the thirsty plants (none the day after a watering)
    v219x_early_n=0,      # > 0: plant on v219x_early_day when that day's forecast already picks this many plants
    v219x_early_day=17,
    v219x_day=18,         # planting day of the block (base_m7_t4 moves V219 with it); a day before the copy's block
    unit_floor_frac=0.0,  # > 0: never sell a unit whose marginal quote is below this share of the product's base price
    unit_floor_items=("WOOL", "MILK", "STRAWBERRY", "MELON", "TOMATO", "EGG", "CARROT", "WHEAT"),
    unit_floor_step=716,  # from this step on everything goes (the last town purchase is at step 716)
    chassis_unit_floor=0.0,  # the same floor on the chassis's SELL lots before the takeover
    sells_first=False,     # controller: our SELLs go ahead of HIREs and purchases in each turn's list (the engine runs
                           # both farms' lists index by index: a lot at a lower index than the rival's sells first)
    sells_first_chassis=False,  # the same reorder on the chassis's own lists before the takeover
    cash_guard_min=0,           # >0: on day 0 the chassis's seed orders never take the cash below this (the day-1 hires need it)
    v233_wool_first=False,      # the chassis's SE sheep crew delivers its wool as soon as the harvest round is done (fertilizer after)
    sells_first_slots=False,    # hour 0: the programme's due premium lots outrank the day's last hires (they move to hour 1)
    sells_first_sort=False,     # our SELLs ordered by the price drop their lot causes (the costliest contest goes first)
    sells_first_slots1=False,   # hour 1: premium lots outrank the remaining hires as well (those move to hour 2)
    sells_first_order=(),       # a fixed product order for our SELLs (the rivals' own typical order) instead of the impact sort
    mkt_dp_d29=False,           # the programme also times day 29 (its last decision sells what is left; from step 716 all goes)
    mkt_dp_d29_prods=(),        # products the programme times on day 29 only (on top of mkt_dp_prods)
    sells_first_dp_due=False,   # a programme product the rival is forecast to sell this turn counts as due (sorted first)
    div_route=None,             # a route of the chassis library taken at the day-6 pick when ADAPT flagged the rival by step 143
    early_harvest=None,         # {crop: [min_age, min_units]}: harvest a one-time crop before its last window day once it
                                # holds min_units (a fertilized wheat has 5 at age 3: replanting beats one more +1 day)
    sells_first_div_sort=False, # chassis phase against a rival ADAPT flagged divergent: the same impact order (a copy's
                                # list mirrors ours, so against copies the tape's own order stays)
    fert_h0=False,              # hour 0: sell the shed's fertilizer beyond today's pickups and tomorrow's reserve (the book
                                # never drains, so a unit sold before the rival's morning lot is worth its lot x $0.20 more)
    chassis_floor_from=12,
    chassis_floor_room=20,   # shed units kept free for the night's drop
    chassis_floor_items=None,  # products the chassis floor applies to (None: unit_floor_items)
    dig_glut=False,       # dig live strawberries whose remaining output is worth less than a carrot plot there
    dig_glut_crops=("STRAWBERRY",),
    dig_first=16,
    dig_last=24,
    dig_units=1.5,        # units a production of an unfertilized plant is counted at
    dig_carrot_units=3.0,
    dig_labor=40.0,
    dig_margin=60.0,
    late_units=None,      # e.g. {"CARROT": 2.0}: plots planted from late_day on are valued at these units (not must)
    late_day=27,
    late_labor=40.0,
    visit_watered=False,  # a re-planned visit of a plant watered today gains nothing more from WATER (no early harvest)
    v219x_melon=0,        # base_m7_t5: up to this many melons on the block's free SE tiles, sized by a melon forecast
    v219x_melon_age=10,   # harvest age of a block melon (6 units: planted at 1, watered at ages 6-10)
    v219x_melon_cost=40.0,  # per plant: watering and harvest time beyond the extra hands
    v219x_melon_margin=0.0,
    v219x_melon_wc=None,  # cost of an extra hand-day for the melons (None: v219x_worker_cost)
                          # sells ahead of it      # units per plant and production day (fertilized)
    herd_on=False,        # buy extra sheep/cows/geese when a book forecast of their product pays (controller days)
    herd_denial_w=0.0,    # weight of the rival's forecast revenue of the product in the herd valuation (1: margin)
    herd_first=12,
    herd_last=18,
    herd_kinds=("SHEEP", "COW", "GOOSE"),
    herd_max=12,
    herd_margin=1500.0,
    herd_opp_rate=0.8,    # the rival's animals produce at this share of the cared rate
    herd_labor=20.0,      # care/feed/collect labour per animal-day
    herd_fert_w=0.8,      # fertilizer collected per animal-day, valued at this share of its price
    herd_tile_cost=250.0, # opportunity cost of an empty tile given to a structure
    herd_place_lag=0,     # days from purchase to placement
    herd_keep_free=6,
    herd_total_max=99,    # at most this many animals bought per game
    herd_rich_margin=None, # rich check (day 12): take over when the herd forecast beats this (copy games' only chance)
    herd_rich_over={},     # existing empty tiles stay for crops up to this many; the herd uses only the rest (or new SE)
    rich_div_margin=None, # strawberry-rich check against a rival ADAPT already flagged divergent: this margin instead
    chassis_globals=None, # override chassis module constants at step 0, e.g. {"V9_HERD_MIN_MILK_SHOPS": 2}
    ad_thresh=None,       # override ADAPT's rival-similarity thresholds, e.g. {359: 0.7}
    mkt_dp=False,         # controller days: for mkt_dp_prods, a dynamic programme over the next mkt_dp_periods post-tick turns decides
    mkt_dp_prods=("STRAWBERRY", "MILK", "WOOL"),   # how many units to sell now: exact price curve, the town's drain schedule,
    mkt_dp_cap=12,        # the rival's sales forecast (its hourly pattern over the last mkt_dp_rival_days days), tonight's carried
    mkt_dp_periods=6,     # units arriving; never holds more than mkt_dp_cap units of a product; decisions only right after a tick
    mkt_dp_rival_days=2,
    mkt_dp_fresh=False,   # no rival sale of the product in the pattern window: sell now (its first lot would otherwise land first)
    mkt_dp_from_day=0,
    mkt_dp_rival_w=1.0,   # the programme also charges the rival's forecast sales at the book our decision leaves (margin, not revenue)
    mkt_dp_w_behind=None, # rival weight used instead while the rival's cash leads ours by more than mkt_dp_w_gap (from mkt_dp_w_day)
    mkt_dp_w_gap=3000.0,
    mkt_dp_w_day=16,
    mkt_dp_w_ahead=None,  # rival weight used instead while our cash leads by more than mkt_dp_w_gap_ahead
    mkt_dp_w_gap_ahead=5000.0,
    es_days=(),           # chassis days on which the tape's wheat replants in NW become strawberries (early strawberries)
    es_n=8,               # how many tiles to convert
    es_skip_cows=(),      # chassis days whose cow purchases are dropped to fund the seeds (costly: two early cows floor the milk market)
    es_min_cash=105.0,    # a seed purchase is converted only with this much cash per seed
    es_quads=("NW",),
    es_waves=(),          # more waves: dicts {days, quads, n}: the tape's wheat replants in those quadrants on those days become strawberries
    es_cow_days=(),       # days on which one skipped cow is bought back (hour 0, cash permitting); units that pick up
    es_cow_reserve=300.0, # cows at the shed carry the extra ones and place them on the tape's empty pastures
    w2t_days=(),          # TOMATO track: chassis days on which the tape's PLANT WHEAT become PLANT TOMATO (the elites run
                          # ~13 tomatoes by day 16 on the tiles we keep in wheat); rival div2-flagged, farms differ (s2t_max_sim)
    w2t_n=3,              # at most this many conversions per day (tomato seeds bought at the day's first free market slot)
    w2t_total=12,         # no conversion once our farm holds this many tomato plants (s2t's included)
    w2t_min_dem=6,        # tomato demand among the unlocked shops (6 per pizza shop / farmers market) at least this
    w2t_cash=3000.0,      # and at least this much cash when the seeds are bought
    w2t_adapt=False,      # also require ADAPT's divergent flag (_AD_STATE off) at the time
    tomato_alt_dyn=False, # TOMATO track: a tomato plot's alternative is the filler's value per tile-day at today's prices
    tomato_alt_min=15.0,  #   (wheat/carrot, as _choose_crops values them) but at least this, instead of tomato_alt_day
    tomato_units_fc=8.0,  # units a tomato plot is valued at in the planner (4 at age 9 and 11); the recorded plots give ~6
    s2t_ext=None,         # TOMATO track: also convert in towns over s2t_max_shops, e.g. {"straw": 1, "tom": 1, "days": [11],
                          # "max_n": 99}: with at most `straw` strawberry-buying shops unlocked, when at least `tom` tomato
                          # buyers (pizza shop / farmers market) are unlocked, on `days`, at most max_n plantings that day
    herd_goose=None,      # HERD track: against a divergent rival (div2 cash band or ADAPT at step 143) in a town with no
                          # YARN_STORE among the shops known on day 6, the tape's day-8/9 sheep become geese: the tape's
                          # pastures for them (found by replaying the route's unit moves) are built as coops, BUY/PICKUP/
                          # PLACE SHEEP become GOOSE, the geese's eggs are sold as they reach the shed. e.g. {"days": [8, 9]}
    hg_rebuy=None,        # HERD track companion: when herd_goose fired and a YARN_STORE is among shops 4-5 (not the first 3),
                          # the controller's herd check also prices sheep only, e.g. {"margin": 1500, "max": 4}
    s2t_max_n=99,         # at most this many strawberry plantings converted per day
    s2t_days=(),          # chassis days: on these planting days, when the rival's cash at step 2 lies outside the band of
    s2t_crop="TOMATO",    # chassis copies (div2_band), the tape's PLANT STRAWBERRY and its strawberry seed purchases become
    div2_band=(1000, 1070),   # s2t_crop (the elites run ~16 strawberry tiles to the tape's 33; strawberries floor 75 over)
    s2t_max_shops=None,   # convert a day's batch only when at most this many strawberry-buying shops are unlocked by then
                          # (e60 on the elite gate: 0 shops by day 9 +$6.7k a seat, 2+ shops -$5k to -$9k: the flood is a weapon)
    s2t_by_town=False,    # replacement crop from the town: tomato with a pizza/farmers market, carrot with a pet cafe, else wheat
    s2t_all=False,        # convert against every rival (a copy's 33 plants floor a strawberry-poor town's book by themselves)
    s2t_max_sim=0.97,     # and only while the rival's farm differs from ours (tile kinds equal on at most this share: a
                          # copy is at 1.00 through day 11, the elites at 0.74-0.86 on day 8)
    lead2=False,          # chassis days: sell every premium lot the tape plans within the current town-tick window now
    lead2_items=("MILK", "WOOL", "STRAWBERRY", "MELON"),   # (the market settles order by order in lockstep and the
    lead2_min_price=5,    # copy's own one-step lead lands one step later, so ours goes first; no tick is ever crossed)
    late_plan=False,      # from late_plan_from: plant wheat/carrots by their exact remaining growth (a one-time crop starts
    late_plan_from=24,    # at 1 unit, each watering in its window on a day up to 29 adds 2 fertilized / 1 not, capped),
    late_plan_min=15.0,   # whichever nets more after seed and fertilizer, when that is at least late_plan_min
    late_keep=False,      # day 28: keep any one-time crop that still gains from a day-29 watering (as d28_keep_carrots)
    mkt_dp_farm=False,    # rival forecast also from its farm: the ripe units of p visible on its tiles now are taken as
    mkt_dp_farm_h=8,      # sales spread over the next mkt_dp_farm_h hours (per hour the larger of pattern and farm)
    mkt_dp_every=False,   # also decide at the steps before a forecast rival sale (sell ahead of it), not only after a tick
    mkt_dp_every_min=1.0, # ... when the forecast sale before the next post-tick decision is at least this many units
    mkt_dp_copy_plan=False,  # copy rival: forecast its sales from our own tape (same route), its one-step lead applied,
    mkt_dp_copy_hit=0.5,     # capped by the ripe units on its farm; used only while >= this share of its planned sale
                             # steps over the last day showed an observed sale (else the hourly pattern)
    mkt_dp_room=0,        # >0: the units the programme may hold across the day boundary are capped by the shed room left
                          # after tonight's load (reserves kept, goods still carried after each unit's last queued drop);
                          # within the day it holds up to mkt_dp_cap as before; the night cap shrinks product by product
    tick_defer=False,     # no sells at hours 4, 8, ..., 20 (the town buys right after them): sell an hour later
    tick_defer0=False,    # also keep the timed premium lots out of hour 0 (they go at hour 1)
    tick_last_day=29,
    tick_keep_due=True,
    v219e=None,           # {'day':13,'min_dem':6,'sizes':{'6':10,'12':15,'18':20},'min_shops':1,'cash':9000,'min_price':55}: at step 288 move
                          # the chassis's SE tomato block (V219, base_m7_t4) to that day, sized by tomato demand among the first four shops
    rich_tom_dem=0,       # > 0: take over at the rich check when the tomato demand of the first four shops (6 per pizza shop or
    rich_tom_dem_over={},  # farmers market) reaches this; no land is bought, the planner's tomato jobs use free/replant tiles
    rich_car_min=0,       # > 0: also take over at the rich check when the carrot demand of the first four shops
    rich_car_over={},     # (pet cafe 2, farmers market 1) reaches this
    rich_over={},
    rich_eval=False,
    rich_hire_budget=1500.0,      # take over only when today's SE strawberry annex evaluation clears se_straw_margin
    race_harvest=False,   # premium goods race the rival: harvest them as soon as race_min units wait
    race_prods=("MILK", "WOOL", "STRAWBERRY"),
    race_min=1,
    race_w=0.3,           # value per unit (x price) of taking a race product a day earlier
    race_min_price=20,    # only while the quote is worth racing for
    race_from=0,          # race window: first day
    race_to=99,           # race window: last day
    sanx_on=False,        # strawberry annex run by hired workers while the chassis plays (replaces the day-12 takeover)
    sanx_step=288,
    sanx_plant_last=13,
    sanx_per_worker=9,
    sanx_max_workers=3,
    sanx_fert=True,
    sanx_reserve=3000.0,
    sanx_mask_adapt=True,
    arb_chassis=False,    # the same arbitrage while the chassis plays (days arb_first..), handed over at takeover
    straw_cap=None,       # chassis days: cap the tape's strawberry plantings by strawberry demand among the shops known so far,
                          # e.g. {"0": 18, "6": 22, "12": 26}: PLANT STRAWBERRY beyond the cap becomes PASS (positions unchanged) and
                          # further BUY_SEED STRAWBERRY orders are dropped; tiles left empty go to the controller at takeover
    fert_idle=False,      # chassis days: a unit that would PASS while standing on an animal tile with fertilizer collects it (no move)
    fert_idle_room=95,    # only while shed + carried goods stay below this many units (end-of-day drops discard overflow)
    arb_first=8,
    arb_room_chassis=45,  # shed room the chassis keeps free after our purchases (its end-of-day drops must fit)
    arb_on=False,         # glut arbitrage: buy a crashed product the town will drain back, sell it after it recovers
    arb_prods=("WOOL", "MILK", "STRAWBERRY"),
    arb_buy_max=8,        # buy while the next unit's quote is at or below this
    arb_target={"WOOL": 150, "MILK": 120, "STRAWBERRY": 120},  # bought units are held until the quote reaches this
    arb_cap=40,           # bought units held at most (all products)
    arb_room=35,          # shed room kept free after buying
    arb_last_day=25,
    arb_step_max=10,
    arb_recover_frac=0.5,  # the town's drain must bring the book back to the target within this share of the days left
    room_v3=False,        # courier/stop planning count the lots held in the shed (floors, timing) as tonight's load;
                          # room releases go unit by unit to the smallest loss vs each product's floor
    room_v3_min=40,       # never plan with less than this end-of-day room for carried goods         # at hour 2, give the hour-1 hires the queues that fit their actual spawn tiles         # shed stops are route visits; a stop that does not fit moves visits to other routes
    shed_skip=False,      # night drop: while tonight's projected shed load (reserves kept + goods carried into the night +
                          # harvests queued after each unit's last drop) exceeds the shed, a HARVEST after the unit's last
                          # queued drop is skipped when the tile keeps its units for tomorrow without loss (shed_skip_cls)
    shed_skip_cls=("A", "O", "G"),  # A: animal whose product stays under max_held after tonight's production; O: ongoing
                          # crop under max_yield after tonight, not decaying tomorrow; G: one-time crop before its last
                          # window day (watered or not thirsty: it keeps its units and may still grow)
    shed_skip_hour=0,     # skip only from this hour on
    shed_skip_d28=True,   # also on day 28 (the final day harvests and delivers what is left)
    shed_skip_margin=0,   # skip only while the projected load exceeds the shed by more than this many units
    shed_perm=False,      # night drop order: the engine fills the shed from the farmer, then hand 1, 2, ... and discards
                          # the rest; among units with the same spawn tile and turn cap (interchangeable routes) the routes
                          # whose goods reach the night drop with the highest value go to the lowest unit indices
    shed_perm_min=60,     # only on days whose planned night load (units carried after each route's last stop) is this big
    market_fix1=False,    # au_market: never sell shed WHEAT/FERTILIZER that today's queued PICKUPs still need. sf8 kept only the
                          # reserve for the NEXT morning (0 on day 28: d28_zero_reserve), so the hour-1 market sold the inputs of
                          # the hands hired at hours 1-2 and of every unit's second PICKUP (one PICKUP per turn: wheat at hour 1,
                          # fertilizer at hour 2); those FEEDs/FERTILIZEs then ran dry. Also the hour-0 room sale of WHEAT /
                          # FERTILIZER keeps today's planned need, not only the reserve.
    market_fix2=False,    # au_market: the hour-0 room sale (a full shed rejects BUY_PRODUCT/BUY_ANIMAL) sold only the top lot
                          # even when it freed less than the purchases need (partial wheat/fertilizer fills, FEEDs/FERTILIZEs
                          # ran dry): take further lots, in the same order, until the room is covered
    w3val_fix=False,      # au_crops: an optional window water of a one-time crop whose harvest (and its watering) is tomorrow
                          # is valued by what max_yield leaves of it: sf8 valued a fertilized wheat's age-3 water at +2 units
                          # although the age-4 water then adds only 1 (6 cap) instead of 2: the true gain is 1 unit
    d28feed_fix=False,    # au_crops: day 28 (the last night refresh: day 29 has none) feeds only animals that produce tonight
                          # and only when it pays: unfed yesterday, FEED saves (1 + pend) units from the escape; fed yesterday,
                          # it adds the banked care bonus pend (sf8 counted 1 + pend: the base unit comes unfed). sf8 fed every
                          # unfed animal as a must visit (sheep with no production left: wheat, turns and hires for nothing).
                          # An animal left to escape has its held units harvested as a must visit (never skipped by shed_skip)
    pickres_fix=False,    # au_crops: the market keeps in the shed what today's queued PICKUPs still need (late hires pick up
                          # at hour 2): sf8 kept only the next-morning reserve, which is 0 on day 28 (d28_zero_reserve), so
                          # the hour-1 sale took the wheat/fertilizer of the late hires' FEEDs/FERTILIZEs (cows unfed, care lost)
    handover_fix1=False,  # the rival-sale tracker (_mk_track/_mk_store, sell_timing) also runs through the chassis phase on the
                          # chassis's final market list: at takeover sf8 had no rival history, so the market programme's rival
                          # forecast was empty on the first controller day and half the pattern on the second (ndays=2)
    handover_fix2=False,  # step 0 of a game: clear ADAPT's divergent flag (and its report) before the takeover rules read it; sf8
                          # read the previous game's flag first (ADAPT restores it only inside the chassis call that follows), so
                          # in a process that reuses the module, a game after a divergent one ran with div_over applied all game
    handover_fix3=False,  # the hire search starts from 0 hands on the first controller day (the day the controller really took over);
                          # sf8 tested day == start // 24 (the copy day 22), so on the rich (12) / divergent (16) first day the search
                          # started at last_hires - 3 = 7 from the default last_hires 10 (it forced 7 hands where 4-6 were best);
                          # day start // 24 keeps its search from 0 as before
)

_GC_CROPS = {
    "WHEAT": dict(seed=10, fy=2, my=4, iv=0, mx=6, on=False),
    "CARROT": dict(seed=20, fy=2, my=3, iv=0, mx=4, on=False),
    "TOMATO": dict(seed=50, fy=8, my=8, iv=1, mx=4, on=True),
    "STRAWBERRY": dict(seed=100, fy=10, my=10, iv=2, mx=4, on=True),
    "MELON": dict(seed=80, fy=10, my=12, iv=0, mx=6, on=False),
}
_GC_ANIM = {
    "GOOSE": dict(cost=300, st="COOP", fy=4, iv=1, held=4, prod="EGG"),
    "COW": dict(cost=400, st="PASTURE", fy=8, iv=2, held=6, prod="MILK"),
    "SHEEP": dict(cost=500, st="PASTURE", fy=6, iv=3, held=6, prod="WOOL"),
}
_GC_MKT = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20), "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60), "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60), "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60), "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
_GC_SHOPS = {
    "BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
_GC_PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
_GC_PREMIUM = ("MELON", "WOOL", "MILK", "STRAWBERRY", "TOMATO")
_GC_ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]
_GC_ACCESS_SET = set(_GC_ACCESS)
_GC_REPORT = dict(gc_days=0, gc_errors=0, gc_hires=0, gc_noops=0, gc_unserved=0, gc_plan_ms=0, gc_room_sells=0)


def _gc_shape(f, x, T):
    x = max(0.0, x)
    if f == "linear": return x
    if f == "sq": return x * x
    if f == "sqrt": return _gc_math.sqrt(x)
    if f == "log": return _gc_math.log(1.0 + x)
    if f == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def _gc_price(item, inv):
    base, T, bf, bt, af, at = _GC_MKT[item]
    if inv < 10000:
        amp = bt * base / _gc_shape(bf, T, T)
        p = base + amp * _gc_shape(bf, 10000 - inv, T)
    else:
        amp = at * base / _gc_shape(af, T, T)
        p = base - amp * _gc_shape(af, inv - 10000, T)
    return max(1, int(round(p)))


def _gc_cash_guard(obs, action):
    """Day 0: trim the chassis's BUY_SEED orders that would leave less than cash_guard_min for tomorrow's hires
    (a rival's wheat round trips at steps 0-1 can move our feed cost enough to end day 0 broke: no hands on day 1,
    the unfed cows escape)."""
    me = int(obs["player"]); farm = obs["farms"][me]
    cash = float(farm["money"]); nh = int(farm.get("hires_today", 0) or 0)
    px = obs["market"]["prices"]; floor = float(GC_P["cash_guard_min"])
    out = []; trimmed = 0
    for o in action.get("market") or []:
        if not isinstance(o, list) or not o:
            out.append(o); continue
        op = o[0]
        if op == "HIRE":
            cash -= _gc_fib(nh); nh += 1
        elif op == "BUY_ANIMAL" and len(o) >= 3:
            cash -= _GC_ANIM.get(o[1], {}).get("cost", 0) * int(o[2])
        elif op == "BUY_PRODUCT" and len(o) >= 3:
            cash -= (float(px.get(o[1], 0)) + 1.0) * int(o[2])
        elif op == "BUY_SEED" and len(o) >= 3 and o[1] in _GC_CROPS:
            unit = float(_GC_CROPS[o[1]]["seed"]); n = int(o[2])
            k = n
            while k > 0 and cash - unit * k < floor:
                k -= 1
            if k < n:
                trimmed += n - k
                if k <= 0:
                    continue
                o = [o[0], o[1], k]
            cash -= unit * k
        out.append(o)
    if trimmed:
        _GC_REPORT["gc_cash_guard"] = _GC_REPORT.get("gc_cash_guard", 0) + trimmed
        action = dict(action); action["market"] = out
    return action


def _gc_sells_first(orders, inv=None, shed=None, due=None):
    """SELL orders first (stable), then the rest in order; a SELL of an item stays behind a purchase of the same item
    listed before it (a buy-then-sell pair keeps its meaning). With sells_first_sort and the town's book, the SELLs go
    in order of the price drop each lot causes (what the rival loses when ours goes first, and we when it does)."""
    orders = list(orders or [])
    if len(orders) > 10:
        # the engine reads the first ten orders only: reorder those, never pull a sell past a hire into the cut
        return _gc_sells_first(orders[:10], inv, shed, due) + orders[10:]
    front, rest, bought = [], [], set()
    for o in orders:
        if isinstance(o, list) and len(o) >= 2 and o[0] == "BUY_PRODUCT":
            bought.add(o[1])
        if isinstance(o, list) and len(o) >= 2 and o[0] == "SELL" and o[1] not in bought:
            front.append(o)
        else:
            rest.append(o)
    if GC_P["sells_first_order"] and inv is not None and len(front) > 1:
        rank = {p: i for i, p in enumerate(GC_P["sells_first_order"])}
        return sorted(front, key=lambda o: rank.get(o[1], 99)) + rest
    if GC_P["sells_first_sort"] and inv is not None and len(front) > 1:
        def impact(o):
            try:
                # the order's own quantity: units dropped this turn reach the shed before the market runs
                p = o[1]; n = min(100, int(o[2]) if len(o) > 2 else 1)
                if n <= 0 or p not in _GC_MKT:
                    return 0.0
                i0 = int(inv[p])
                return float(n) * (_gc_price(p, i0) - _gc_price(p, i0 + n))
            except Exception:
                return 0.0
        due = due or set()
        front = sorted(front, key=lambda o: (0 if o[1] in due else 1, -impact(o)))
    return front + rest


def _gc_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _gc_quad(x, y):
    return ("N" if y < 5 else "S") + ("W" if x < 5 else "E")


def _gc_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _gc_near_access(p):
    return min(_GC_ACCESS, key=lambda a: abs(a[0] - p[0]) + abs(a[1] - p[1]))


def _gc_get(d, k, default=None):
    if isinstance(d, dict):
        return d.get(k, default)
    return getattr(d, k, default)


_OPEN_DEFAULT = dict(
    from_day=0,                # first day of the scheduled opening (with start=24*from_day the tape plays the days before)
    until=12,                  # from this day the normal controller rules apply (footprint, chooser, the rich-town logic)
    hires0=5,                  # hire budget reserved on day 0
    melon=12,                  # melon plots (planted from day 0, topped up through melon_last)
    melon_last=2,
    wheat0=None,               # day-0 wheat plots (None: every free NW tile left)
    straw_early={5: 4},        # cumulative strawberry plots by day before day 6 (the tape: 4 on day 5; DSM: 2/6/8 on days 2/3/4)
    straw_d6={0: 16, 6: 20, 12: 23},  # cumulative target from day 6 by the strawberry demand known (units/day)
    straw_slope=(15.0, 0.96),  # days 9-12: target = a + b * demand
    straw_max=38,
    straw_last=12,
    early_harvest=(2, 5),      # days on which wheat of age >= 2 is harvested to free tiles for due strawberries
    land={"NE": 7, "SW": 9},   # earliest purchase day per quadrant (bought when the cash is there)
    anim={"COW": {0: 2, 2: 3, 3: 4, 6: 6, 7: 7, 9: 8}, "SHEEP": {0: 2, 6: 4, 8: 5, 9: 6}, "GOOSE": {6: 3, 9: 4}},   # cumulative targets by day (the tape's herd)
    sheep_yarn=8,              # sheep target once a yarn store is known (day 6+)
    anim_before_straw=False,   # cash order: scheduled animals before the day's strawberry seeds
    anim_order=("COW", "SHEEP", "GOOSE"),
    after={"footprint": False},   # GC_P overrides applied for good when the opening ends
    anim_first_day=True,       # day 0: animals before seeds
    feed_place=True,           # feed and care a newly placed animal on its first day
    wheat_fill=True,           # free tiles not needed by the schedule are planted with wheat
    wheat_fill_from=0,
    keep_free=0,               # tiles left empty for tomorrow
    cash_keep=140.0,           # cash left at every morning plan for the next morning's feed and hires
    cash_low=1e9,              # below this cash at the plan, routes drop their goods right after the animal cluster (always)
    hire_min_budget=20.0,      # cash reserved for hires before any purchase
    over={"plant_must": False, "max_hands": 12, "hire_cost_w": 1.0, "prem_drop": True, "prem_drop_max": 6, "deliver_prem": 800.0, "hire_compact": True},   # GC_P overrides while the opening runs
    feed_buy_hour=14,          # buy tomorrow's feed at this hour when the shed is short and the cash is in
    replan_hours=(5, 9, 13),   # hours at which affordable scheduled purchases are made and the routes redone
)


def _open_target(table, day):
    """Cumulative target from a {day: n} table: the entry of the latest day <= day (0 before the first)."""
    out = 0
    for d in sorted(int(k) for k in table):
        if d <= day:
            out = table[d] if d in table else table[str(d)]
    return out


class _GcVisit:
    __slots__ = ("pos", "acts", "wheat", "fert", "anim", "value", "must", "gain", "tag", "carry")

    def __init__(self, pos, acts, value=0.0, must=False, wheat=0, fert=0, anim=None, gain=None, tag="", carry=0):
        self.pos = pos; self.acts = acts; self.value = value; self.must = must
        self.wheat = wheat; self.fert = fert; self.anim = anim; self.gain = gain or {}; self.tag = tag
        self.carry = carry


class GoldCtl:
    def __init__(self):
        self.reset()

    def reset(self):
        self.me = None
        self.herd_total = 0
        self.herd_day = None
        self.day_plan = None
        self.queues = {}
        self.routes = []
        self.spawns = []
        self.orders0 = []
        self.orders1 = []
        self.hires_planned = 0; self.hires_left = 0
        self.reserve = {}
        self.arb = {}
        self._held_now = {}
        self.fp_bonus = 0
        self._straw_path = None
        self.last_hires = 10
        self.rival_sales = {}
        self._mk_prev = None
        self.se_day = None
        self.footprint_n = None
        self.n_animals = 0
        self.final = False
        self._first_day = None
        self.open = None
        if getattr(self, "_open_over", None):
            GC_P.update(self._open_over)
        self._open_over = None
        if GC_P["open"] is not None:
            self.open = dict(_OPEN_DEFAULT)
            self.open.update(GC_P["open"] if isinstance(GC_P["open"], dict) else {})

    def _open_on(self, day):
        return self.open is not None and self.open["from_day"] <= day < self.open["until"]

    def _straw_demand(self, shops):
        return sum(6 for sh in shops if sh in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")) + 1

    def _open_straw_target(self, day, shops):
        op = self.open
        if day > op["straw_last"]:
            return 0
        if day < 6:
            return _open_target(op["straw_early"], day)
        dem = self._straw_demand(shops) - 1
        if day <= 8:
            tab = {int(k): v for k, v in op["straw_d6"].items()}
            t = 0
            for k in sorted(tab):
                if dem >= k:
                    t = tab[k]
        else:
            a, b = op["straw_slope"]
            t = int(round(a + b * dem))
        return min(op["straw_max"], t)

    def _open_crops(self, obs, day, free, replant, shops, counts, avail, seeds):
        """Opening schedule: strawberries (nearest the shed), melons, then wheat on what is left; seeds limited by cash."""
        op = self.open
        out = {}
        cash = avail
        slots = sorted(free, key=lambda p: _gc_dist(p, (4.5, 4.5))) + sorted(replant, key=lambda p: _gc_dist(p, (4.5, 4.5)))
        want = []
        n_s = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))
        want.append(("STRAWBERRY", n_s))
        if day <= op["melon_last"]:
            want.append(("MELON", max(0, op["melon"] - counts.get("MELON", 0))))
        n_w = 0
        if day == 0 and op["wheat0"] is not None:
            n_w = op["wheat0"]
        elif op["wheat_fill"] and day >= op["wheat_fill_from"]:
            n_w = len(slots)
        want.append(("WHEAT", n_w))
        held = dict(seeds)
        k = 0
        for crop, n in want:
            price = _GC_CROPS[crop]["seed"]
            while n > 0 and k < len(slots) - (op["keep_free"] if crop == "WHEAT" else 0):
                if held.get(crop, 0) > 0:
                    held[crop] -= 1
                elif cash >= price:
                    cash -= price
                else:
                    break
                out[slots[k]] = crop; k += 1; n -= 1
        self.open_spent = avail - cash
        return out

    # ------------------------------------------------------------------ valuation
    def _values(self, obs):
        inv = obs["market"]["inventory"]
        val = {}
        for p in _GC_PRODUCTS:
            val[p] = float(_gc_price(p, inv[p]))
        self.pnow = dict(val)
        return val

    # ------------------------------------------------------------------ planning
    def plan_day(self, obs):
        _GC_REPORT["gc_days"] += 1
        step = int(obs["step"]); day = step // 24
        if getattr(self, "_first_day", None) is None:
            self._first_day = day   # handover_fix3: the controller's first day (reset() clears it)
        self.day = day
        me = self.me
        farm = obs["farms"][me]
        priv = obs["private"]
        shed = {k: int(v) for k, v in dict(priv["shed"]).items()}
        seeds = {k: int(v) for k, v in dict(priv["seeds"]).items()}
        money = float(farm["money"])
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        tiles = farm["tiles"]
        self.tiles_today = tiles
        final = day >= 29
        self.final = final
        val = self._values(obs)
        self.val = val
        self.pfwd = {}
        if GC_P["anim_fwd_days"] > 0:
            try:
                inv_ = obs["market"]["inventory"]; D_ = float(GC_P["anim_fwd_days"])
                dr_ = {}
                for s2 in range(step, step + 24):
                    for it, q in self._town_draw(shops, s2).items():
                        dr_[it] = dr_.get(it, 0) + q
                for it in ("MILK", "WOOL", "EGG"):
                    self.pfwd[it] = float(_gc_price(it, int(inv_[it] - dr_.get(it, 0) * D_)))
            except Exception as e:
                _GC_REPORT["gc_pfwd_err"] = repr(e)[:120]
        quads = list(farm["unlocked_quadrants"])
        orders0 = []
        spend = 0.0
        hire_budget = sum(_gc_fib(k) for k in range(min(self.last_hires + 1, 13)))
        opn = self.open if self._open_on(day) else None
        keep = 0.0
        if opn is not None and not getattr(self, "_open_over", None):
            self._open_over = {k: GC_P.get(k) for k in opn["over"]}
            GC_P.update(opn["over"])
        elif opn is None and getattr(self, "_open_over", None):
            GC_P.update(self._open_over); self._open_over = None
            self.footprint_n = None
            GC_P.update(self.open.get("after", {}) or {})
        if opn is not None:
            if day == opn["from_day"]:
                self.last_hires = opn["hires0"]
                hire_budget = sum(_gc_fib(k) for k in range(opn["hires0"] + 1))
            hire_budget = max(hire_budget, opn["hire_min_budget"])
            # tomorrow's hires and feed (the evening purchase covers the feed when the cash is in)
            n_an_k = sum(1 for row in tiles for t in row if isinstance(t, dict) and "animal" in t) + sum(int(shed.get(a_, 0)) for a_ in ("COW", "SHEEP", "GOOSE"))
            keep = max(opn["cash_keep"], sum(_gc_fib(k) for k in range(min(self.last_hires, 11))) + n_an_k * (self.pnow.get("WHEAT", 30) + 3) + 40)
            self._open_keep = keep

        # ---- land (the chassis schedule: NE early, SW around day 11)
        new_quads = []
        if opn is not None:
            for q_, price_ in (("NE", 1000), ("SW", 2000), ("SE", 4000)):
                d_ = opn["land"].get(q_)
                if q_ not in quads and not new_quads and d_ is not None and day >= int(d_) and money - spend - hire_budget - keep >= price_:
                    orders0.append(["BUY_LAND"]); spend += price_; new_quads.append(q_)
                    _GC_REPORT["gc_open_land"] = _GC_REPORT.get("gc_open_land", "") + "%s%d " % (q_, day)
                    break
        elif not final and day <= 16:
            if "NE" not in quads and money - hire_budget >= 1300:
                orders0.append(["BUY_LAND"]); spend += 1000; new_quads.append("NE")
            elif "NE" in quads and "SW" not in quads and day >= GC_P["land_sw_day"] and money - hire_budget >= 2400:
                orders0.append(["BUY_LAND"]); spend += 2000; new_quads.append("SW")
        if (GC_P["se_force_day"] is not None and not new_quads and not final and "NE" in quads and "SW" in quads
                and "SE" not in quads and day >= GC_P["se_force_day"] and day <= 24
                and money - hire_budget >= 4000 + GC_P["se_reserve"]):
            orders0.append(["BUY_LAND"]); spend += 4000; new_quads.append("SE")
            self.se_day = day
            self.fp_bonus = getattr(self, "fp_bonus", 0) + int(GC_P["se_force_fp"])
            _GC_REPORT["gc_se_bought"] = day
            _GC_REPORT["gc_se_forced"] = 1
        if (GC_P["se_on"] and not new_quads and not final and "NE" in quads and "SW" in quads and "SE" not in quads
                and GC_P["se_first"] <= day <= GC_P["se_last"] and money - hire_budget >= 4000 + GC_P["se_reserve"]):
            # the last quadrant pays only as a tomato annex: price the plots it would carry against land + inputs + labour
            n_se = GC_P["se_plots"]
            fert = self.pnow.get("FERTILIZER", 50)
            gain = self._tomato_value(obs, day, n_se, shops) - self._tomato_value(obs, day, 0, shops)
            cost = 4000 + n_se * (50 + 2 * fert + GC_P["tomato_labor"])
            _GC_REPORT["gc_se_eval"] = int(gain - cost)
            if gain - cost > GC_P["se_margin"]:
                orders0.append(["BUY_LAND"]); spend += 4000; new_quads.append("SE")
                self.se_day = day
                _GC_REPORT["gc_se_bought"] = day
        if (GC_P["se_straw"] and not new_quads and not final and "NE" in quads and "SW" in quads and "SE" not in quads
                and day <= GC_P["straw_fc_last"] and money - hire_budget >= 4000 + GC_P["se_reserve"]):
            n_se = min(GC_P["se_plots"], int((money - hire_budget - 4000 - GC_P["se_reserve"]) // 100))
            if n_se > 0:
                fert = self.pnow.get("FERTILIZER", 50)
                gain = self._straw_value(obs, day, n_se, shops) - self._straw_value(obs, day, 0, shops)
                life = min(16, 29 - day) + 1
                cost = 4000 + n_se * (100 + 3 * fert + GC_P["straw_labor"])
                _GC_REPORT["gc_se_straw_eval"] = int(gain - cost)
                if gain - cost > GC_P["se_straw_margin"]:
                    orders0.append(["BUY_LAND"]); spend += 4000; new_quads.append("SE")
                    self.se_day = day
                    self.fp_bonus = getattr(self, "fp_bonus", 0) + GC_P["se_plots"]
                    _GC_REPORT["gc_se_bought"] = day
        owned = set(quads) | set(new_quads)

        # ---- scan
        plants = []; animals = []; empties = []; weeds = []; structs = []
        counts = {}
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if t == "LOCKED":
                    if _gc_quad(x, y) in owned:
                        empties.append((x, y))
                    continue
                if t is None:
                    empties.append((x, y)); continue
                k = t.get("kind")
                if k == "PLANT":
                    plants.append(((x, y), t)); counts[t["crop"]] = counts.get(t["crop"], 0) + 1
                elif k == "WEED": weeds.append((x, y))
                elif "animal" in t: animals.append(((x, y), t))
                elif k in ("COOP", "PASTURE"): structs.append(((x, y), k))
        self.n_animals = len(animals)

        visits = []
        replant = []
        self._eh_set = set()
        ehl = GC_P.get("eh_level")
        if ehl and not final and day <= int(ehl.get("last_day", 26)):
            try:
                due_t = 0; due_n = 0; cand_w = []
                mu = int(ehl.get("min_units", 5))
                for pos_, t_ in plants:
                    c_ = t_["crop"]
                    if c_ not in ("WHEAT", "CARROT"):
                        continue
                    my_ = _GC_CROPS[c_]["my"]; a_ = day - int(t_["planted_day"])
                    if a_ >= my_:
                        due_t += 1
                    elif a_ == my_ - 1:
                        due_n += 1
                        if c_ == "WHEAT":
                            fa_ = int(t_.get("fertilized_until_day", -1)) >= day
                            yu_ = int(t_["yield_units"]) + (2 if fa_ else 1)
                            if yu_ >= mu and not t_.get("watered_today"):
                                cand_w.append(pos_)
                ex = due_n - due_t - int(ehl.get("margin", 2))
                if ex > 0 and cand_w:
                    k = min(len(cand_w), int(ex * float(ehl.get("frac", 0.5)) + 0.5))
                    self._eh_set = set(sorted(cand_w, key=lambda q: _gc_dist(q, (4.5, 4.5)))[:k])
                    _GC_REPORT["gc_eh_level"] = _GC_REPORT.get("gc_eh_level", 0) + len(self._eh_set)
            except Exception as e:
                _GC_REPORT["gc_eh_level_err"] = repr(e)[:120]
        for pos, t in plants:
            v = self._plant_visit(pos, t, day, val, final)
            if v is not None:
                visits.append(v)
                if (v.tag == "C" and v.acts and v.acts[-1][0] == "HARVEST") or v.tag == "R" or (v.tag == "D" and GC_P["replant_dig"]):
                    replant.append(v)
        for pos, t in animals:
            v = self._animal_visit(pos, t, day, val, final)
            if v is not None:
                visits.append(v)

        # ---- extra herd (forecast of the product's book)
        herd_new = {}
        rb = GC_P.get("hg_rebuy")
        rb_on = bool(rb and _HG.get("on") and _HG.get("bought", 0) > 0 and not _HG.get("rb_done")
                     and "YARN_STORE" not in list(shops)[:3] and "YARN_STORE" in list(shops)[3:int(rb.get("upto", 5))]
                     and day <= int(rb.get("last", 18)))
        herd_win = bool(GC_P["herd_on"] and GC_P["herd_first"] <= day <= GC_P["herd_last"])
        if ((herd_win or rb_on) and not final and getattr(self, "herd_day", None) != day):
            self.herd_day = day
            se_open = ("SE" not in owned and "NE" in owned and "SW" in owned and not new_quads)
            spare_tiles = max(0, len(empties) - GC_P["herd_keep_free"]) if not new_quads else 0
            kind, k, hv, need_se = None, 0, 0.0, False
            if herd_win:
                try:
                    kind, k, hv, need_se = self._herd_plan(obs, day, shops, spare_tiles, se_open, money - spend - hire_budget)
                except Exception as e:
                    kind, k, hv = None, 0, 0.0
                    _GC_REPORT["gc_herd_err"] = repr(e)[:120]
            h_margin = GC_P["herd_margin"]
            if rb_on and not (kind and hv > h_margin):
                # HERD track: the tape's day-8/9 sheep went to geese and a yarn store came later: price sheep alone
                _hm = GC_P["herd_max"]
                try:
                    GC_P["herd_max"] = min(_hm, int(rb.get("max", 4)))
                    k2, n2, v2, se2 = self._herd_plan(obs, day, shops, spare_tiles, se_open, money - spend - hire_budget,
                                                      kinds=("SHEEP",))
                except Exception as e:
                    k2, n2, v2, se2 = None, 0, 0.0, False
                    _GC_REPORT["gc_herd_err"] = repr(e)[:120]
                finally:
                    GC_P["herd_max"] = _hm
                _GC_REPORT["gc_hg_rebuy"] = "d%d:%s%d:%d" % (day, (k2 or "-")[0], n2, int(v2))
                if k2 and v2 > float(rb.get("margin", 1500.0)):
                    kind, k, hv, need_se = k2, n2, v2, se2
                    h_margin = float(rb.get("margin", 1500.0))
                    _HG["rb_done"] = True
            if kind and hv > h_margin and len(orders0) < 7:
                if need_se:
                    orders0.append(["BUY_LAND"]); spend += 4000; new_quads.append("SE"); owned.add("SE")
                    se_tiles = [(xx, yy) for yy in range(5, 10) for xx in range(5, 10) if tiles[yy][xx] == "LOCKED"]
                    self.herd_tiles = sorted(se_tiles, key=lambda p: _gc_dist(p, (4.5, 4.5)))[:k]
                    for pp in se_tiles:
                        empties.append(pp)
                orders0.append(["BUY_ANIMAL", kind, k]); spend += k * _GC_ANIM[kind]["cost"]
                herd_new[kind] = k
                self.herd_total = getattr(self, "herd_total", 0) + k
                _GC_REPORT["gc_herd"] = _GC_REPORT.get("gc_herd", "") + "d%d:%s%dx$%d " % (day, kind[0], k, int(hv))

        # ---- opening schedule: animals (cumulative targets by day, what the cash allows, cheapest first)
        if opn is not None:
            have = {}
            for _p, t in animals:
                have[t["animal"]] = have.get(t["animal"], 0) + 1
            for an in ("COW", "SHEEP", "GOOSE"):
                have[an] = have.get(an, 0) + shed.get(an, 0)
            targets = []
            for an, tab in opn["anim"].items():
                t_ = _open_target({int(k): v for k, v in tab.items()}, day)
                if an == "SHEEP" and day >= 6 and "YARN_STORE" in shops:
                    t_ = max(t_, opn["sheep_yarn"])
                targets.append((an, t_))
            # cows, sheep, geese: the order of their first batches' value
            land_res = 0.0
            if not new_quads:
                for q_, price_ in (("NE", 1000), ("SW", 2000), ("SE", 4000)):
                    d_ = opn["land"].get(q_)
                    if q_ not in quads and d_ is not None and day >= int(d_):
                        land_res = price_; break
            for an, t_ in sorted(targets, key=lambda x: opn["anim_order"].index(x[0]) if x[0] in opn["anim_order"] else 9):
                n_ = max(0, t_ - have.get(an, 0))
                cost_ = _GC_ANIM[an]["cost"]
                straw_due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0)) * 100
                n_an0 = len(animals) + sum(herd_new.values()) + sum(int(shed.get(a_, 0)) for a_ in ("COW", "SHEEP", "GOOSE"))
                feed0 = max(0, n_an0 - int(shed.get("WHEAT", 0))) * (self.pnow.get("WHEAT", 30) + 3)
                budget_ = money - spend - hire_budget - keep - feed0 - land_res - (0 if (opn["anim_before_straw"] or (opn["anim_first_day"] and day == 0)) else straw_due)
                k_ = min(n_, int(budget_ // cost_)) if cost_ > 0 else 0
                if k_ > 0 and len(orders0) < 7:
                    orders0.append(["BUY_ANIMAL", an, k_]); spend += k_ * cost_
                    herd_new[an] = herd_new.get(an, 0) + k_
                    _GC_REPORT["gc_open_anim"] = _GC_REPORT.get("gc_open_anim", "") + "d%d:%s%d " % (day, an[0], k_)
        # ---- animals waiting in the shed
        free_struct = {"COOP": [p for p, k in structs if k == "COOP"], "PASTURE": [p for p, k in structs if k == "PASTURE"]}
        taken = set()
        for an in ("COW", "SHEEP", "GOOSE"):
            for _ in range(shed.get(an, 0) + herd_new.get(an, 0)):
                st = _GC_ANIM[an]["st"]
                if free_struct[st]:
                    pos = free_struct[st].pop(0)
                    fc = [["FEED"], ["CARE"]] if (opn is not None and opn["feed_place"] and day <= 28) else []
                    visits.append(_GcVisit(pos, [["PLACE", an]] + fc, value=300.0, must=True, anim=an, tag="L", wheat=1 if fc else 0))
                else:
                    cand = [p for p in empties if p not in taken]
                    if not cand:
                        break
                    pos = min(cand, key=lambda p: _gc_dist(p, (4.5, 4.5)))
                    taken.add(pos)
                    fc = [["FEED"], ["CARE"]] if (opn is not None and opn["feed_place"] and day <= 28) else []
                    visits.append(_GcVisit(pos, [["BUILD_" + st], ["PLACE", an]] + fc, value=300.0, must=True, anim=an, tag="L", wheat=1 if fc else 0))

        # ---- empty coops/pastures no animal will use: dig and plant them like weeds
        if GC_P["dig_structs"] and not final:
            for st in ("COOP", "PASTURE"):
                for pos in free_struct[st]:
                    weeds.append(pos)
        # ---- planting
        need_seeds = {}
        if not final:
            free = [p for p in empties if p not in taken] + list(weeds)
            if opn is not None:
                # early wheat harvest: free the tiles the due strawberries need (oldest wheat first, age >= 2)
                eh0, eh1 = opn["early_harvest"]
                due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))
                short = due - len(free) - sum(1 for v in replant)
                if eh0 <= day <= eh1 and short > 0:
                    cand = []
                    for v in visits:
                        if v.tag == "C" and not any(a[0] == "HARVEST" for a in v.acts):
                            t = tiles[v.pos[1]][v.pos[0]]
                            if isinstance(t, dict) and t.get("crop") == "WHEAT":
                                age = day - int(t["planted_day"])
                                yu = int(t.get("yield_units", 0))
                                if age >= 2 and yu + 1 >= 2:
                                    cand.append((-(age), v, yu))
                    cand.sort(key=lambda x: x[0])
                    for _a, v, yu in cand[:short]:
                        g = 1 if any(a[0] == "WATER" for a in v.acts) else 0
                        v.acts = [a for a in v.acts if a[0] != "HARVEST"] + [["HARVEST"]]
                        v.carry = yu + g; v.must = True; v.value += (yu + g) * val["WHEAT"]
                        replant.append(v)
                        _GC_REPORT["gc_open_eh"] = _GC_REPORT.get("gc_open_eh", 0) + 1
            if GC_P["footprint"] and opn is None:
                # never grow more plots than the chassis ran at takeover (its labour plan): extra plots overcommit
                # the hands and the shed. Plots freed by harvests/digs today are replanted inside the cap.
                n_plants = len(plants)
                if getattr(self, "footprint_n", None) is None:
                    self.footprint_n = n_plants + len(weeds) + GC_P["footprint_slack"]
                room_new = max(0, self.footprint_n + getattr(self, "fp_bonus", 0) - n_plants)
                if GC_P["labor_cap"] > 0:
                    # labour model (turns/day): animals, ongoing crops, one-time crops
                    n_on = sum(1 for _p, t in plants if _GC_CROPS[t["crop"]]["on"])
                    load = GC_P["labor_anim"] * len(animals) + GC_P["labor_on"] * n_on + GC_P["labor_one"] * (len(plants) - n_on)
                    room_new = max(0, int((GC_P["labor_cap"] - load) / GC_P["labor_one"]))
                if len(free) > room_new:
                    free = sorted(free, key=lambda q: _gc_dist(q, (4.5, 4.5)))[:room_new]
                    _GC_REPORT["gc_footprint_cut"] = _GC_REPORT.get("gc_footprint_cut", 0) + 1
            if opn is not None:
                n_an = len(animals) + sum(herd_new.values()) + sum(int(shed.get(an, 0)) for an in ("COW", "SHEEP", "GOOSE"))
                feed_est = max(0, n_an - int(shed.get("WHEAT", 0))) * (self.pnow.get("WHEAT", 30) + 3)
                crop_for = self._open_crops(obs, day, free, [v.pos for v in replant], shops, counts, money - spend - hire_budget - keep - feed_est, seeds)
                # anything scheduled and still unfunded makes today's sales urgent (no market holds)
                n_s_planned = sum(1 for c in crop_for.values() if c == "STRAWBERRY")
                straw_left = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0) - n_s_planned)
                land_left = any(q_ not in quads and q_ not in new_quads and opn["land"].get(q_) is not None and day >= int(opn["land"][q_]) for q_ in ("NE", "SW", "SE"))
                anim_left = False
                for an, tab in opn["anim"].items():
                    t_ = _open_target({int(k): v for k, v in tab.items()}, day)
                    have_ = sum(1 for _p, t in animals if t["animal"] == an) + int(shed.get(an, 0)) + herd_new.get(an, 0)
                    if t_ > have_:
                        anim_left = True
                self._open_urgent = bool(land_left or straw_left > 0 or anim_left)
                if self._open_urgent:
                    _GC_REPORT["gc_open_urgent_days"] = _GC_REPORT.get("gc_open_urgent_days", 0) + 1
            else:
                crop_for = self._choose_crops(obs, day, free, [v.pos for v in replant], shops, val, counts)
            for pos in free:
                crop = crop_for.get(pos)
                if not crop:
                    continue
                acts = ([["DIG"]] if pos in weeds else []) + [["PLANT", crop], ["WATER"]]
                pv_ = self._crop_value(crop, val)
                if GC_P["late_units"] and day >= GC_P["late_day"] and crop in GC_P["late_units"]:
                    # a late plot only grows what the last day allows (a day-27 carrot: 2 units at age 2)
                    pv_ = GC_P["late_units"][crop] * val[crop] - _GC_CROPS[crop]["seed"] - GC_P["late_labor"]
                visits.append(_GcVisit(pos, acts, value=self._pdefer(day) * pv_, tag="P",
                                       must=GC_P["plant_must"] and day <= GC_P["plant_must_last"]))
                need_seeds[crop] = need_seeds.get(crop, 0) + 1
            for v in replant:
                crop = crop_for.get(v.pos)
                if not crop:
                    continue
                if opn is not None and GC_P["deliver_prem"] and self._prem_value(v) >= float(GC_P["deliver_prem"]):
                    continue   # delivery day: the tile is planted tomorrow, the hands carry the goods home now
                v.acts = v.acts + [["PLANT", crop], ["WATER"]]
                pv_ = self._crop_value(crop, val)
                if GC_P["late_units"] and day >= GC_P["late_day"] and crop in GC_P["late_units"]:
                    pv_ = GC_P["late_units"][crop] * val[crop] - _GC_CROPS[crop]["seed"] - GC_P["late_labor"]
                v.value += self._pdefer(day) * pv_
                need_seeds[crop] = need_seeds.get(crop, 0) + 1
            for crop, n in need_seeds.items():
                buy = n - seeds.get(crop, 0)
                if buy > 0:
                    cost = buy * _GC_CROPS[crop]["seed"]
                    avail = money - spend - hire_budget
                    if cost > avail:
                        buy = max(0, int(avail // _GC_CROPS[crop]["seed"]))
                        cost = buy * _GC_CROPS[crop]["seed"]
                    if buy > 0:
                        orders0.append(["BUY_SEED", crop, buy]); spend += cost

        # ---- inputs
        wheat_need = sum(v.wheat for v in visits)
        fert_need = sum(v.fert for v in visits)
        wheat_have = shed.get("WHEAT", 0)
        if wheat_need > wheat_have:
            short = wheat_need - wheat_have
            price = _gc_price("WHEAT", obs["market"]["inventory"]["WHEAT"] - short)
            if opn is not None:
                # the hands come first (the day's income needs them); the evening purchase covers the rest
                short = min(short, max(0, int((money - spend - hire_budget) // max(1, price))))
            if short > 0:
                orders0.append(["BUY_PRODUCT", "WHEAT", short]); spend += short * price
        fert_have = shed.get("FERTILIZER", 0)
        if fert_need > fert_have:
            # buy the shortfall when the fertilizations it enables are worth more than the fertilizer
            fv = sorted([v for v in visits if v.fert], key=lambda v: -v.gain.get("fert", 0.0))
            short = fert_need - fert_have
            fprice = _gc_price("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"] - short)
            buy = sum(1 for v in fv[:short] if v.gain.get("fert", 0.0) > fprice + GC_P["fert_buy_margin"])
            if buy > 0 and money - spend - hire_budget > buy * fprice + 100:
                orders0.append(["BUY_PRODUCT", "FERTILIZER", buy]); spend += buy * fprice
                fert_have += buy
        if fert_need > fert_have:
            fv = sorted([v for v in visits if v.fert], key=lambda v: v.gain.get("fert", 0.0))
            for v in fv[:fert_need - fert_have]:
                v.acts = [a for a in v.acts if a[0] != "FERTILIZE"]; v.fert = 0
                v.value -= v.gain.get("fert", 0.0)
        visits = [v for v in visits if v.acts]
        self._fert_need_day = sum(v.fert for v in visits)

        # ---- hour-0 sales: free shed room before the input purchases land (a full shed rejects them)
        buys0 = [o for o in orders0 if o[0] in ("BUY_PRODUCT", "BUY_ANIMAL")]
        res_w = int(GC_P["feed_reserve"] * len(animals)) + 2
        keep0 = {"WHEAT": res_w, "FERTILIZER": GC_P["fert_keep"]}
        sell0 = []
        for p in sorted(_GC_PRODUCTS, key=lambda p: -(shed.get(p, 0) * val.get(p, 0))):
            n = int(shed.get(p, 0)) - (res_w if p == "WHEAT" else (GC_P["fert_keep"] if p == "FERTILIZER" else 0))
            if GC_P.get("market_fix1") and p in ("WHEAT", "FERTILIZER"):
                need_ = int(wheat_need) if p == "WHEAT" else int(self._fert_need_day)
                if n > 0 and int(shed.get(p, 0)) - need_ < n:
                    _GC_REPORT["gc_mfix1"] = _GC_REPORT.get("gc_mfix1", 0) + 1
                    n = int(shed.get(p, 0)) - need_
            if n > 0:
                sell0.append(["SELL", p, n])
        need_room = sum(int(v) for v in shed.values()) + sum(int(o[2]) for o in buys0) - 95
        if GC_P["room0_v2"] and GC_P["max_sell0"] == 0:
            # a full shed only matters for this morning's purchases: free exactly that room, selling first what
            # loses least by being sold now (untimed goods, then those quoted furthest below normal... last)
            sell0 = []
            if buys0 and need_room > 0:
                timed = set(GC_P["timed"]) if GC_P["sell_timing"] else set()
                cands = []
                for p in _GC_PRODUCTS:
                    n = int(shed.get(p, 0)) - keep0.get(p, 0)
                    if n > 0:
                        cands.append(((1 if p in timed else 0), -val.get(p, 0) / float(_GC_MKT[p][0]), p, n))
                take = need_room
                for _t, _r, p, n in sorted(cands):
                    if take <= 0:
                        break
                    k = min(n, take)
                    sell0.append(["SELL", p, k]); take -= k
        else:
            if GC_P["unit_floor_frac"] > 0 and need_room <= 0:
                sell0 = [["SELL", o[1], self._unit_cap(obs, o[1], int(o[2]))] for o in sell0]
                sell0 = [o for o in sell0 if o[2] > 0]
            if final and GC_P["final_sell0"] > 0:
                sell0 = sell0[:max(GC_P["final_sell0"], 1 if need_room > 0 else 0)]
            elif not final and day >= GC_P["late_sell0_day"] and GC_P["late_sell0"] > 0:
                sell0 = sell0[:max(GC_P["late_sell0"], 1 if need_room > 0 else 0)]
            else:
                sell0_all = list(sell0)
                sell0 = sell0[:max(GC_P["max_sell0"], 1 if need_room > 0 else 0)]
                if GC_P.get("market_fix2") and need_room > 0 and buys0 and sum(int(o[2]) for o in sell0) < need_room - 5:
                    # the purchases would really not fit (engine: BUY_PRODUCT/BUY_ANIMAL fail at 100 units)
                    got = sum(int(o[2]) for o in sell0)
                    for o in sell0_all[len(sell0):]:
                        if got >= need_room:
                            break
                        k = min(int(o[2]), need_room - got)
                        sell0.append(["SELL", o[1], k]); got += k
                        _GC_REPORT["gc_mfix2"] = _GC_REPORT.get("gc_mfix2", 0) + 1
        self.sell0 = sell0
        self.n0_hires = 10 - len(buys0) - len(sell0)
        import time as _t
        t0 = _t.perf_counter()
        routes, hires, spawns = self._route_and_hire(visits, money - spend, final, day)
        _GC_REPORT["gc_plan_ms"] = max(_GC_REPORT["gc_plan_ms"], int(1000 * (_t.perf_counter() - t0)))
        self.hires_planned = hires
        self.last_hires = hires
        _GC_REPORT["gc_hires"] += hires
        self.orders0 = list(self.sell0) + [o for o in orders0 if o[0] in ("BUY_PRODUCT", "BUY_ANIMAL")]
        self.orders1 = [o for o in orders0 if o[0] not in ("BUY_PRODUCT", "BUY_ANIMAL")]
        if opn is not None and len(self.orders0) + len(self.orders1) + hires <= 10:
            self.orders0 = self.orders0 + self.orders1; self.orders1 = []
        self.routes = routes
        self.spawns = spawns
        self.day = day
        # shed stops: only as many as needed so the end-of-day drop fits in the shed
        if GC_P["stop_v2"]:
            self.drop_at = {}
            d28r = GC_P["d28_cap"] is not None and day == 28 and not final
            if (final and GC_P["final_ret"]) or d28r:
                _ovf, _pv = 0, 0.0
            else:
                _ovf, _pv = self._plan_stops(routes, spawns)
            if final or d28r:
                for u, r in enumerate(routes):
                    if r and r[-1].tag != "S":
                        r.append(self._stop_visit(r[-1].pos))
        else:
            self.drop_at, _ovf, _pv = self._plan_drops(routes, spawns)
        _GC_REPORT["gc_ovf_plan"] = _GC_REPORT.get("gc_ovf_plan", 0) + int(_ovf)
        if opn is not None and money - spend < opn["cash_low"] and not final:
            for u, r in enumerate(routes):
                if u in self.drop_at or not r or any(v.tag == "S" for v in r):
                    continue
                ai = [k for k, v in enumerate(r) if v.tag == "A" and v.carry > 0]
                if ai and sum(v.carry for v in r[:ai[-1] + 1]) > 0:
                    k = ai[-1]; v = r[k]
                    a = _gc_near_access(v.pos)
                    back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
                    if k + 1 < len(r):
                        nx = r[k + 1].pos
                        extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
                    else:
                        extra = back + 1
                    cap = 23 if u == 0 else (23 if u <= self.n0_hires else 22)
                    if self._rcost(spawns[u], r) + extra <= cap:
                        self.drop_at[u] = k
                        _GC_REPORT["gc_open_drops"] = _GC_REPORT.get("gc_open_drops", 0) + 1
        if GC_P["prem_drop"] and not final:
            for u, r in enumerate(routes):
                if u in self.drop_at or not r:
                    continue
                prem_idx = [k for k, v in enumerate(r) if v.carry > 0 and self._is_premium_visit(v)]
                if not prem_idx:
                    continue
                k = prem_idx[-1]
                v = r[k]
                a = _gc_near_access(v.pos)
                back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
                if k + 1 < len(r):
                    nx = r[k + 1].pos
                    extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
                else:
                    extra = back + 1
                cap = 23 if u == 0 else (23 if u <= self.n0_hires else 22)
                if extra <= GC_P["prem_drop_max"] and self._rcost(spawns[u], r) + extra <= cap:
                    self.drop_at[u] = k
                    _GC_REPORT["gc_prem_drops"] = _GC_REPORT.get("gc_prem_drops", 0) + 1
        if GC_P.get("shed_perm") and not final:
            self._shed_perm(routes, spawns)
        if final and not GC_P["stop_v2"]:
            for u, r in enumerate(routes):
                if r:
                    self.drop_at[u] = len(r) - 1
        # tomorrow's fertilizations: ongoing crops on a production eve without cover, one-time crops entering the window
        fert_tom = 0
        for pos, t in plants:
            cd = _GC_CROPS[t["crop"]]; age1 = day + 1 - int(t["planted_day"])
            fu = int(t.get("fertilized_until_day", -1))
            if cd["on"]:
                k1 = age1 + 1 - cd["fy"]
                if k1 >= 0 and k1 % cd["iv"] == 0 and (k1 // cd["iv"] + 1) <= cd["mx"] and fu < day + 1:
                    fert_tom += 1
            elif t["crop"] in ("WHEAT", "CARROT") and age1 == (cd["my"] + 1) // 2 and fu < day + 1:
                fert_tom += 1
        self.fert_tomorrow = fert_tom
        self.reserve = {"WHEAT": int(GC_P["feed_reserve"] * len(animals)) + 2,
                        "FERTILIZER": max(GC_P["fert_keep"], fert_tom + GC_P["fert_res_extra"])}
        if GC_P["d28_zero_reserve"] and day >= 28:
            self.reserve = {"WHEAT": 0, "FERTILIZER": 0}
        if opn is not None:
            # the opening lives on fertilizer sales: keep only what tomorrow's ongoing-crop production eves use
            fert_on = 0
            for pos, t in plants:
                cd = _GC_CROPS[t["crop"]]; age1 = day + 1 - int(t["planted_day"]); fu = int(t.get("fertilized_until_day", -1))
                if cd["on"]:
                    k1 = age1 + 1 - cd["fy"]
                    if k1 >= 0 and k1 % cd["iv"] == 0 and (k1 // cd["iv"] + 1) <= cd["mx"] and fu < day + 1:
                        fert_on += 1
            self.reserve["FERTILIZER"] = fert_on

    # ------------------------------------------------------------------ opening: mid-day purchases and re-routing
    def _open_midday(self, obs, hour):
        """A scheduled purchase (land, strawberry seeds, animals) that the morning could not afford but the day's sales
        can: buy it now, add its visits and re-route the unfinished work (with extra hands if they pay)."""
        opn = self.open
        step = int(obs["step"]); day = step // 24
        me = self.me; farm = obs["farms"][me]; priv = obs["private"]
        money = float(farm["money"])
        shed = {k: int(v) for k, v in dict(priv["shed"]).items()}
        seeds = {k: int(v) for k, v in dict(priv["seeds"]).items()}
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        tiles = farm["tiles"]; quads = list(farm["unlocked_quadrants"])
        keep = getattr(self, "_open_keep", opn["cash_keep"])
        cash = money - keep
        orders = []
        # ---- what is planned already (queued visits)
        claimed = set(); planned_crop = {}; pending_place = {}
        for u, q in self.queues.items():
            for tgt, a, v in (q or []):
                claimed.add(tuple(tgt))
                if a[0] == "PLANT": planned_crop[a[1]] = planned_crop.get(a[1], 0) + 1
                if a[0] == "PLACE" and len(a) > 1 and a[1] in _GC_ANIM: pending_place[a[1]] = pending_place.get(a[1], 0) + 1
        counts = {}; animals_n = {}; free = []
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if t is None:
                    if (x, y) not in claimed:
                        free.append((x, y))
                elif isinstance(t, dict):
                    if t.get("kind") == "PLANT": counts[t["crop"]] = counts.get(t["crop"], 0) + 1
                    elif "animal" in t: animals_n[t["animal"]] = animals_n.get(t["animal"], 0) + 1
        for c, n in planned_crop.items():
            counts[c] = counts.get(c, 0) + n
        # ---- land (a due purchase the cash cannot cover yet holds the cash: nothing below it is bought)
        new_q = None
        for q_, price_ in (("NE", 1000), ("SW", 2000), ("SE", 4000)):
            d_ = opn["land"].get(q_)
            if q_ not in quads and d_ is not None and day >= int(d_):
                if cash >= price_:
                    orders.append(["BUY_LAND"]); cash -= price_; new_q = q_
                    for y in range(10):
                        for x in range(10):
                            if tiles[y][x] == "LOCKED" and _gc_quad(x, y) == q_:
                                free.append((x, y))
                    _GC_REPORT["gc_open_land"] = _GC_REPORT.get("gc_open_land", "") + "%s%d@%d " % (q_, day, hour)
                else:
                    return []
                break
        # ---- strawberries (targets) reserved first, then animals (targets) with what the cash allows
        visits = []
        n_an_tot = sum(animals_n.values()) + sum(shed.get(a_, 0) for a_ in _GC_ANIM) + sum(pending_place.values())
        feed0 = max(0, n_an_tot - shed.get("WHEAT", 0)) * (self.pnow.get("WHEAT", 30) + 3)
        cash -= feed0
        n_s_due = max(0, self._open_straw_target(day, shops) - counts.get("STRAWBERRY", 0))
        s_res = 100.0 * max(0, min(n_s_due, len(free)) - seeds.get("STRAWBERRY", 0))
        s_res = min(s_res, max(0.0, cash))
        cash -= s_res
        herd_new = {}
        targets = []
        for an, tab in opn["anim"].items():
            t_ = _open_target({int(k): v for k, v in tab.items()}, day)
            if an == "SHEEP" and day >= 6 and "YARN_STORE" in shops:
                t_ = max(t_, opn["sheep_yarn"])
            targets.append((an, t_))
        for an, t_ in sorted(targets, key=lambda x: opn["anim_order"].index(x[0]) if x[0] in opn["anim_order"] else 9):
            have = animals_n.get(an, 0) + shed.get(an, 0) + pending_place.get(an, 0)
            k_ = min(max(0, t_ - have), int(cash // _GC_ANIM[an]["cost"]))
            if k_ > 0:
                orders.append(["BUY_ANIMAL", an, k_]); cash -= k_ * _GC_ANIM[an]["cost"]; herd_new[an] = k_
                _GC_REPORT["gc_open_anim"] = _GC_REPORT.get("gc_open_anim", "") + "d%d@%d:%s%d " % (day, hour, an[0], k_)
        taken = set()
        for an, k_ in herd_new.items():
            st = _GC_ANIM[an]["st"]
            for _ in range(k_):
                cand = [p for p in free if p not in taken]
                if not cand:
                    break
                pos = min(cand, key=lambda p: _gc_dist(p, (4.5, 4.5)))
                taken.add(pos)
                fc = [["FEED"], ["CARE"]] if opn["feed_place"] else []
                # the animal lands in the shed after this step: a PASS keeps the pickup from firing too early
                visits.append(_GcVisit(pos, [["BUILD_" + st], ["PLACE", an]] + fc, value=300.0, must=True, anim=an, tag="L", wheat=1 if fc else 0))
        free = [p for p in free if p not in taken]
        cash += s_res
        n_s = n_s_due
        slots = sorted(free, key=lambda p: _gc_dist(p, (4.5, 4.5)))
        held = seeds.get("STRAWBERRY", 0)
        buy_s = 0; k = 0
        while n_s > 0 and k < len(slots):
            if held > 0:
                held -= 1
            elif cash >= 100:
                cash -= 100; buy_s += 1
            else:
                break
            pv_ = self._crop_value("STRAWBERRY", self.val)
            visits.append(_GcVisit(slots[k], [["PLANT", "STRAWBERRY"], ["WATER"]], value=GC_P["plant_defer"] * pv_, tag="P"))
            k += 1; n_s -= 1
        if buy_s > 0:
            orders.append(["BUY_SEED", "STRAWBERRY", buy_s])
        if new_q is not None and opn["wheat_fill"]:
            # the rest of the new land: wheat, as far as the seeds are affordable
            n_w = 0
            for p in slots[k:]:
                if cash < 10:
                    break
                cash -= 10; n_w += 1
                pv_ = self._crop_value("WHEAT", self.val)
                visits.append(_GcVisit(p, [["PLANT", "WHEAT"], ["WATER"]], value=GC_P["plant_defer"] * pv_, tag="P"))
            if n_w > seeds.get("WHEAT", 0):
                orders.append(["BUY_SEED", "WHEAT", n_w - seeds.get("WHEAT", 0)])
        self._open_urgent = bool(n_s > 0 or any(max(0, t_ - (animals_n.get(an, 0) + shed.get(an, 0) + pending_place.get(an, 0) + herd_new.get(an, 0))) > 0 for an, t_ in targets))
        if not visits:
            return orders
        # ---- incremental routing: the morning's queues stay as they are (their deliveries included); the new
        # visits are appended where they fit, else new hands take them
        positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
        n_units = len(positions)
        turns = 23 - hour

        def q_cost(u, q, pos):
            t = 0; p = pos
            for tgt, a, v in q:
                t += abs(p[0] - tgt[0]) + abs(p[1] - tgt[1]) + 1; p = tgt
            return t, p

        def v_cost(pos, v, has_wheat):
            t = abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts)
            if v.anim:
                a = _gc_near_access(pos)
                t += abs(pos[0] - a[0]) + abs(pos[1] - a[1]) + 1 + abs(a[0] - v.pos[0]) + abs(a[1] - v.pos[1]) - (abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]))
            if v.wheat and not has_wheat:
                t += 1
            return t

        best = None
        cash_h = money - keep
        invs = list(priv["inventories"])
        for h_new in range(0, 5):
            cost = sum(_gc_fib(len(farm["hands"]) + q) for q in range(h_new))
            if h_new > 0 and (cost > cash_h or len(farm["hands"]) + h_new > GC_P["max_hands"]):
                break
            starts = list(positions) + self._spawns(h_new, positions[0])
            caps = [turns] * n_units + [turns - 1] * h_new
            used = []; ends = []; wheat_ok = []
            for u in range(len(starts)):
                if u < n_units:
                    c, e = q_cost(u, self.queues.get(u) or [], starts[u])
                    inv = dict(invs[u]) if u < len(invs) else {}
                    wheat_ok.append(int(inv.get("WHEAT", 0)) > 0 or any(a[0] == "PICKUP" and a[1] == "WHEAT" for _t, a, _v in (self.queues.get(u) or [])))
                else:
                    c, e = 0, starts[u]; wheat_ok.append(False)
                used.append(c); ends.append(e)
            assign = {u: [] for u in range(len(starts))}
            unserved = []
            for v in sorted(visits, key=lambda v: (0 if v.must else 1, -v.value)):
                bu = None
                for u in range(len(starts)):
                    c = v_cost(ends[u], v, wheat_ok[u])
                    if used[u] + c <= caps[u] and (bu is None or c < bu[0]):
                        bu = (c, u)
                if bu is None:
                    unserved.append(v); continue
                c, u = bu
                assign[u].append(v); used[u] += c; ends[u] = v.pos
                if v.wheat: wheat_ok[u] = True
            pen = sum((v.value + (1e5 if v.must else 0.0)) for v in unserved)
            score = -pen - GC_P["hire_cost_w"] * cost
            if best is None or score > best[0]:
                best = (score, h_new, assign, starts)
            if not unserved:
                break
        _, h_new, assign, starts = best
        for u, vs in assign.items():
            if not vs:
                continue
            q = list(self.queues.get(u) or []) if u < n_units else []
            if u < n_units and u < len(invs):
                has_w = int(dict(invs[u]).get("WHEAT", 0)) > 0 or any(a[0] == "PICKUP" and a[1] == "WHEAT" for _t, a, _v in q)
            else:
                has_w = False
            wheat_n = sum(v.wheat for v in vs)
            if wheat_n and not has_w:
                q.append((_gc_near_access(starts[u]), ["PICKUP", "WHEAT", wheat_n], None))
            for an in ("COW", "SHEEP", "GOOSE"):
                n_an = sum(1 for v in vs if v.anim == an)
                if n_an:
                    q.append((_gc_near_access(starts[u]), ["PASS"], None))   # the animal lands in the shed after this step
                    q.append((_gc_near_access(starts[u]), ["PICKUP", an, n_an], None))
            for v in vs:
                for a in v.acts:
                    q.append((v.pos, list(a), v))
            self.queues[u] = q
        if h_new > 0:
            orders = [["HIRE"]] * h_new + orders
            _GC_REPORT["gc_hires"] += h_new
        _GC_REPORT["gc_open_mid"] = _GC_REPORT.get("gc_open_mid", 0) + 1
        return orders

    # ------------------------------------------------------------------ jobs
    def _plant_visit(self, pos, t, day, val, final):
        crop = t["crop"]; cd = _GC_CROPS[crop]
        age = day - int(t["planted_day"])
        cu = int(t["consecutive_unwatered"])
        yu = int(t["yield_units"])
        fu = int(t.get("fertilized_until_day", -1))
        acts = []; value = 0.0; must = False; fert = 0; gain = {}; carry = 0
        pv = val[crop]
        if not cd["on"]:
            ws = (cd["my"] + 1) // 2
            ready = age >= cd["fy"]
            in_window = ws <= age <= cd["my"]
            if final:
                if ready and yu > 0:
                    acts = []
                    g = 0
                    if GC_P["final_water"] and in_window and yu < cd["mx"] and not t.get("watered_today"):
                        g = min(2 if fu >= day else 1, cd["mx"] - yu)
                        acts.append(["WATER"])
                    acts.append(["HARVEST"])
                    return _GcVisit(pos, acts, value=(yu + g) * pv, must=True, tag="H", carry=yu + g)
                return None
            yu2 = yu
            if in_window and yu < cd["mx"]:
                fert_active = fu >= day
                if (not fert_active) and age == ws and not (crop == "CARROT" and not GC_P["fert_carrots"]):
                    rem_days = cd["my"] - age + 1
                    extra = min(cd["mx"] - yu, 2 * rem_days) - min(cd["mx"] - yu, rem_days)
                    fert_gain = extra * pv - self.pnow.get("FERTILIZER", 50)
                    if fert_gain > (GC_P["carrot_fert_gain"] if crop == "CARROT" else GC_P["wheat_fert_gain"]):
                        acts.append(["FERTILIZE"]); fert = 1; gain["fert"] = fert_gain; value += fert_gain
                        fert_active = True
                g = min(2 if fert_active else 1, cd["mx"] - yu)
                if GC_P["visit_watered"] and t.get("watered_today"):
                    g = 0   # a mid-day re-plan: today's watering is already in yield_units
                acts.append(["WATER"]); value += g * pv; yu2 = yu + g
                if cu >= 1:
                    must = True; value += (yu + g) * pv
                if crop == "MELON" and self.open is not None and self._open_on(day):
                    must = True   # a missed window water delays the whole melon harvest by a day
            elif cu >= 1 and not (ready and yu > 0 and age >= cd["my"]):
                acts.append(["WATER"]); value += max(1, yu) * pv + 30; must = True
            harvest_now = ready and yu2 > 0 and (age >= cd["my"] or yu2 >= cd["mx"])
            if (not harvest_now and ready and yu2 > 0 and pos in getattr(self, "_eh_set", ())
                    and yu2 >= int((GC_P.get("eh_level") or {}).get("min_units", 5))):
                harvest_now = True
            eh = (GC_P["early_harvest"] or {}).get(crop)
            if eh and ready and age >= int(eh[0]) and yu2 >= int(eh[1]) and not harvest_now:
                harvest_now = True
                _GC_REPORT["gc_early_harvest"] = _GC_REPORT.get("gc_early_harvest", 0) + 1
            if crop == "MELON":
                harvest_now = age >= cd["fy"] and yu2 > 0 and (yu2 >= cd["mx"] or age >= cd["my"])
            if day >= 28 and ready and yu2 > 0 and (GC_P["d28_harvest_all"] or age >= cd["my"] or yu2 >= cd["mx"]):
                keep = GC_P["d28_keep_carrots"] and crop == "CARROT" and age < cd["my"] and yu2 < cd["mx"]
                if GC_P["late_keep"] and day == 28 and age < cd["my"] and yu2 < cd["mx"] and age + 1 >= ws:
                    keep = True
                if not keep:
                    harvest_now = True
            if (GC_P.get("w3val_fix") and not harvest_now and not must and crop in ("WHEAT", "CARROT") and yu2 > yu
                    and any(a_[0] == "WATER" for a_ in acts)):
                # w3val_fix: tomorrow is this plant's harvest day, whose watering (in the yield window) adds b anyway up to
                # max_yield: today's water is worth only what the cap leaves of it (a fertilized wheat at age 3: +1, not +2)
                hd = int(t["planted_day"]) + cd["my"]
                if day >= 27 and GC_P["d28_harvest_all"] and not (GC_P["d28_keep_carrots"] and crop == "CARROT"):
                    hd = min(hd, 28)
                if hd == day + 1:
                    fu2 = (day + 2) if fert else fu
                    b = 2 if fu2 >= hd else 1
                    gm = min(cd["mx"], yu2 + b) - min(cd["mx"], yu + b)
                    if gm < yu2 - yu:
                        value -= (yu2 - yu - gm) * pv
                        _GC_REPORT["gc_w3val"] = _GC_REPORT.get("gc_w3val", 0) + 1
            if harvest_now:
                acts.append(["HARVEST"]); value += yu2 * pv; must = True; carry = yu2
                gain["prod"] = crop; gain["pv"] = pv
            if not acts:
                return None
            return _GcVisit(pos, acts, value=value, must=must, fert=fert, gain=gain, tag="C", carry=carry)
        # ongoing crops
        k_next = age + 1 - cd["fy"]
        eve = k_next >= 0 and k_next % cd["iv"] == 0 and (k_next // cd["iv"] + 1) <= cd["mx"]
        done = int(t.get("max_lifespan_step", -1)) >= 0
        if final:
            if yu > 0:
                return _GcVisit(pos, [["HARVEST"]], value=yu * pv, must=True, tag="H", carry=yu)
            return None
        fert_active = fu >= day
        add = (2 if fert_active else 1) if eve else 0
        if yu > 0:
            over = max(0, yu + add - cd["mx"])
            thr = GC_P["tomato_harvest_min"] if crop == "TOMATO" else 2
            race = GC_P["race_harvest"] and crop in GC_P["race_prods"] and pv >= GC_P["race_min_price"] and GC_P["race_from"] <= day <= GC_P["race_to"]
            if race:
                thr = min(thr, GC_P["race_min"])
            if over > 0 or done or day >= 28 or yu >= thr:
                acts.append(["HARVEST"]); value += over * pv + (yu * pv * 0.15) + (yu * pv if done else 0); carry = yu
                gain["prod"] = crop; gain["pv"] = pv
                if race:
                    value += yu * pv * GC_P["race_w"]
        if eve:
            if not fert_active:
                covered = sum(1 for dd in range(3) if (k_next + dd) >= 0 and (k_next + dd) % cd["iv"] == 0 and ((k_next + dd) // cd["iv"] + 1) <= cd["mx"])
                fert_gain = covered * pv - self.pnow.get("FERTILIZER", 50) * GC_P["fert_cost_w"]
                if fert_gain > GC_P["ongoing_fert_gain"]:
                    acts.append(["FERTILIZE"]); fert = 1; gain["fert"] = fert_gain; value += fert_gain
                    fert_active = True
            if fert_active:
                acts.append(["WATER"]); value += pv
                if cu >= 1:
                    must = True; value += 4 * pv
            elif cu >= 1:
                acts.append(["WATER"]); value += 4 * pv; must = True
        elif cu >= 1 and not done:
            acts.append(["WATER"]); value += 4 * pv; must = True
        if (GC_P["dig_glut"] and not done and crop in GC_P["dig_glut_crops"] and GC_P["dig_first"] <= day <= GC_P["dig_last"]
                and GC_P["replant_done"]):
            # a live plant in a crashed book: its remaining output against a carrot plot on the same tile
            pd_ = int(t["planted_day"]); left = 0
            for dd in range(day, 29):
                kk = dd + 1 - pd_ - cd["fy"]
                if kk >= 0 and kk % cd["iv"] == 0 and kk // cd["iv"] + 1 <= cd["mx"]:
                    left += 1
            u_ = 2.0 if fert_active else GC_P["dig_units"]
            rem = (yu + left * u_) * pv
            cycles = max(0, (GC_P["carrot_last_plant"] - day) // 3 + 1)
            alt = cycles * (GC_P["dig_carrot_units"] * self.pnow.get("CARROT", 40) - 20 - GC_P["dig_labor"])
            if alt - rem > GC_P["dig_margin"]:
                _GC_REPORT["gc_dig_glut"] = _GC_REPORT.get("gc_dig_glut", 0) + 1
                acts = ([["HARVEST"]] if yu > 0 else []) + [["DIG"]]
                return _GcVisit(pos, acts, value=yu * pv + 40.0, must=GC_P["plant_must"], tag="R", carry=yu)
        if done and day <= GC_P["carrot_last_plant"] and GC_P["replant_done"]:
            # no further production: take what is left, clear the plant and let the tile be replanted now
            acts = [a for a in acts if a[0] == "HARVEST"] + [["DIG"]]
            return _GcVisit(pos, acts, value=value + 40.0, must=GC_P["plant_must"], tag="R", carry=carry)
        if done and yu == 0 and not acts:
            if day <= 26:
                return _GcVisit(pos, [["DIG"]], value=40.0, tag="D", must=GC_P["plant_must"])
            return None
        if not acts:
            return None
        if GC_P["water_first"]:
            acts = [a for a in acts if a[0] != "HARVEST"] + [a for a in acts if a[0] == "HARVEST"]
        return _GcVisit(pos, acts, value=value, must=must, fert=fert, gain=gain, tag="O", carry=carry)

    def _animal_visit(self, pos, t, day, val, final):
        a = _GC_ANIM[t["animal"]]
        yu = int(t["yield_units"]); pv = val[a["prod"]]
        if GC_P["anim_fwd_days"] > 0 and getattr(self, "pfwd", None):
            pv0 = pv; pv = max(pv, self.pfwd.get(a["prod"], pv))
            if pv > pv0 and pv0 < GC_P["care_min_price"] <= pv:
                _GC_REPORT["gc_pfwd_care"] = _GC_REPORT.get("gc_pfwd_care", 0) + 1
        pend = int(t.get("pending_care_bonus", 0) or 0)
        acts = []; value = 0.0; must = False; wheat = 0; carry = 0
        if final:
            acts = []
            if yu > 0 and pv >= 2:
                acts.append(["HARVEST"])
            if t.get("fertilizer_available") and self.pnow.get("FERTILIZER", 0) >= 3:
                acts.append(["COLLECT_FERTILIZER"])
            if acts:
                return _GcVisit(pos, acts, value=yu * pv + self.pnow.get("FERTILIZER", 0), must=True, tag="H", carry=yu + 1)
            return None
        placed = int(t.get("placed_day", 0))

        def prod_at(e):
            k = e + 1 - placed - a["fy"]
            return k >= 0 and k % a["iv"] == 0
        prod_tonight = prod_at(day)
        e = day + 1
        while e <= 28 and not prod_at(e):
            e += 1
        # bonus banked before the first production is capped by the held limit
        care_useful = e <= 28 and pend + 2 <= a["held"]
        care_worth = care_useful and pv >= GC_P["care_min_price"]
        unfed = int(t["consecutive_unfed"]) >= 1
        wheat_px = self.pnow.get("WHEAT", 40)
        bonus_tonight = prod_tonight and pv * (1 + pend) > wheat_px
        feed = day <= 28 and (unfed or care_worth or bonus_tonight or GC_P["feed_all"])
        d28_escape = False
        if GC_P.get("d28feed_fix") and day == 28 and not GC_P["feed_all"]:
            # tonight's production is the last one that counts: a FEED today saves it from the escape (unfed yesterday:
            # 1 + pend units) or adds the banked care bonus (fed yesterday: pend units; the base unit comes unfed)
            f28 = prod_tonight and ((1 + pend) if unfed else pend) * pv > wheat_px
            if feed and not f28:
                _GC_REPORT["gc_d28feed"] = _GC_REPORT.get("gc_d28feed", 0) + 1
            feed = f28
            d28_escape = unfed and not feed
        if feed:
            acts.append(["FEED"]); wheat = 1
            if unfed:
                value += 500.0; must = True
            else:
                value += (pv * (1 + pend) if prod_tonight else 0.0) + 5.0
        if care_worth and feed:
            acts.append(["CARE"]); value += pv * 0.9
        if yu > 0:
            nxt = (1 + pend) if prod_tonight else 0
            over = max(0, yu + nxt - a["held"])
            race = GC_P["race_harvest"] and a["prod"] in GC_P["race_prods"] and pv >= GC_P["race_min_price"] and GC_P["race_from"] <= day <= GC_P["race_to"]
            thr = min(3, GC_P["race_min"]) if race else 3
            if (over > 0 or yu >= thr or day >= 27) and (pv >= GC_P["harvest_min_price"] or day >= 28):
                acts.append(["HARVEST"]); value += over * pv + yu * pv * 0.1; carry += yu
                gain_a = {"prod": a["prod"], "pv": pv, "units": yu}
                if race:
                    value += yu * pv * GC_P["race_w"]
        if t.get("fertilizer_available"):
            acts.append(["COLLECT_FERTILIZER"]); value += max(3.0, self.pnow.get("FERTILIZER", 30) * 0.8); carry += 1
        if not acts:
            return None
        # animals are the densest value on the farm: visit every fed one every day
        must = must or (GC_P["animals_must"] and wheat > 0)
        if d28_escape and yu > 0 and any(a_[0] == "HARVEST" for a_ in acts):
            must = True   # d28feed_fix: the animal escapes tonight with whatever it still holds
        return _GcVisit(pos, acts, value=value, must=must, wheat=wheat, tag="A", carry=carry, gain=locals().get("gain_a"))

    def _pdefer(self, day):
        w = GC_P.get("plant_last_w")
        if w is not None and day >= max(GC_P["wheat_last_plant"], GC_P["carrot_last_plant"]):
            return float(w)
        return GC_P["plant_defer"]

    def _crop_value(self, crop, val):
        cd = _GC_CROPS[crop]
        units = {"WHEAT": 5.0, "CARROT": 3.5, "TOMATO": 7.0, "STRAWBERRY": 7.0, "MELON": 6.0}[crop]
        return units * val[crop] - cd["seed"]

    def _herd_value(self, obs, day, kind, k, shops):
        """Our revenue of kind's product with k extra animals placed today: every visible animal of the kind supplies
        its cared rate (the rival's weighted), the town's shops (now and expected) drain the book, the new animals yield
        min(held, fy) units fy days after placement, then 1 + iv every iv days; the day's lot sells together and we get
        our share."""
        a = _GC_ANIM[kind]; prod = a["prod"]
        inv = float(obs["market"]["inventory"][prod])
        drain_now = 1.0 + sum((12.0 if len(_GC_SHOPS.get(sh, [])) == 1 else 6.0) for sh in shops if prod in _GC_SHOPS.get(sh, []))
        per_unlock = sum((12.0 if len(v) == 1 else 6.0) for v in _GC_SHOPS.values() if prod in v) / 8.0
        rate = (1.0 + a["iv"]) / a["iv"]
        ours = 0; theirs = 0
        for side in (self.me, 1 - self.me):
            for row in obs["farms"][side]["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("animal") == kind:
                        if side == self.me: ours += 1
                        else: theirs += 1
        placed = day + GC_P["herd_place_lag"]
        sched = {}
        dd = placed + a["fy"]
        if dd <= 29:
            sched[dd] = min(a["held"], a["fy"])
            dd += a["iv"]
            while dd <= 29:
                sched[dd] = min(a["held"], 1 + a["iv"]); dd += a["iv"]
        n_shops = len(shops)
        rev = 0.0; rev_th = 0.0
        for d in range(day, 30):
            unl = min(8, d // 3) - n_shops
            inv -= drain_now + max(0, unl) * per_unlock * GC_P["future_shop_w"]
            q_ours = ours * rate + k * sched.get(d, 0)
            q_tot = q_ours + theirs * rate * GC_P["herd_opp_rate"]
            n = int(round(q_tot))
            if n > 0:
                sm = sum(_gc_price(prod, inv + i) for i in range(n))
                rev += sm * q_ours / q_tot
                rev_th += sm * (q_tot - q_ours) / q_tot
            inv += q_tot
        # the margin view: what the rival's own animals earn in the book we leave them counts against us
        return rev - float(GC_P["herd_denial_w"]) * rev_th

    def _herd_plan(self, obs, day, shops, n_empty, se_open, money, kinds=None):
        """Best (kind, k, value, needs_se) for extra animals bought now."""
        pn = getattr(self, "pnow", None) or {}
        wheat_px = pn.get("WHEAT", 40); fert_px = pn.get("FERTILIZER", 30)
        best = (None, 0, 0.0, False)
        days = 30 - (day + GC_P["herd_place_lag"])
        for kind in (kinds or GC_P["herd_kinds"]):
            a = _GC_ANIM[kind]
            base = self._herd_value(obs, day, kind, 0, shops)
            for k in range(1, min(GC_P["herd_max"], GC_P["herd_total_max"] - getattr(self, "herd_total", 0)) + 1):
                need_se = k > n_empty
                if need_se and not se_open:
                    break
                cost = k * (a["cost"] + days * (wheat_px + GC_P["herd_labor"] - GC_P["herd_fert_w"] * fert_px))
                cost += min(k, n_empty) * GC_P["herd_tile_cost"] + (4000.0 if need_se else 0.0)
                if cost + 500 > money:
                    break
                v = self._herd_value(obs, day, kind, k, shops) - base - cost
                if v > best[2]:
                    best = (kind, k, v, need_se)
        return best

    def _tomato_value(self, obs, day, n, shops):
        """Forecast revenue of n tomato plots planted today (4 units at age 9 and 11 each), selling on arrival,
        against town demand (current + expected new shops) and the opponent's visible tomato plants."""
        inv = float(obs["market"]["inventory"]["TOMATO"])
        uh = float(GC_P.get("tomato_units_fc", 8.0)) / 2.0
        k_now = sum(1 for s in shops if s in ("PIZZA_SHOP", "FARMERS_MARKET"))
        n_shops = len(shops)
        opp = obs["farms"][1 - self.me]
        opp_sup = {}
        for row in opp["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("crop") == "TOMATO":
                    pd = int(t["planted_day"])
                    for age, u in ((9, uh), (11, uh)):
                        d = pd + age
                        if d >= day:
                            opp_sup[d] = opp_sup.get(d, 0) + u * GC_P["opp_tomato_w"]
        mine = {}
        for row in obs["farms"][self.me]["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("crop") == "TOMATO":
                    pd = int(t["planted_day"])
                    for age, u in ((9, uh), (11, uh)):
                        d = pd + age
                        if d >= day:
                            mine[d] = mine.get(d, 0) + u
        rev = 0.0
        for d in range(day, 30):
            # expected tomato shops by day d (a shop unlocks at the start of days 3,6,..., 8 at most)
            unl = min(8, d // 3) - n_shops
            k = k_now + max(0, unl) * 0.25 * GC_P["future_shop_w"]
            inv -= 6.0 * k + 1.0
            inv += opp_sup.get(d, 0) + mine.get(d, 0)
            for age in (9, 11):
                if d == day + age and d <= 29:
                    q = uh * n
                    p0 = _gc_price("TOMATO", inv); p1 = _gc_price("TOMATO", inv + q)
                    rev += q * 0.5 * (p0 + p1)
                    inv += q
        return rev

    def _straw_value(self, obs, day, n, shops, fw=None):
        """Revenue of n strawberry plots planted today (straw_units at ages 10, 12, 14, 16 up to day 29), sold on
        arrival into a book drained by the town's strawberry shops and supplied by every visible strawberry plant."""
        inv = float(obs["market"]["inventory"]["STRAWBERRY"])
        sshops = ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")
        k_now = sum(1 for s in shops if s in sshops)
        n_shops = len(shops)
        sup = {}
        lag = int(GC_P["straw_lag"])
        for side, w in ((self.me, GC_P["straw_our_w"]), (1 - self.me, GC_P["straw_opp_w"])):
            for row in obs["farms"][side]["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                        pd = int(t["planted_day"])
                        for k in range(4):
                            d = pd + 10 + 2 * k + lag
                            if d >= day:
                                sup[d] = sup.get(d, 0) + GC_P["straw_units"] * w
                        yu = int(t.get("yield_units", 0) or 0)
                        if yu:
                            sup[day + lag] = sup.get(day + lag, 0) + yu * w
        rev = 0.0
        new_days = {day + 10 + 2 * k + lag for k in range(4)}
        for d in range(day, 30):
            unl = min(8, d // 3) - n_shops
            k = k_now + max(0, unl) * 0.5 * GC_P["future_shop_w"] * (GC_P["straw_future_w"] if fw is None else fw)
            inv -= 6.0 * k + 1.0
            inv += sup.get(d, 0)
            if n == 0 and getattr(self, "_straw_path", None) is not None:
                self._straw_path.append((d, _gc_price("STRAWBERRY", int(inv))))
            if d in new_days and n > 0:
                q = GC_P["straw_units"] * n
                p0 = _gc_price("STRAWBERRY", int(inv)); p1 = _gc_price("STRAWBERRY", int(inv + q))
                rev += q * 0.5 * (p0 + p1)
                inv += q
        return rev

    def rich_eval(self, obs):
        """Value of the SE quadrant as a strawberry annex today (forecast gain - land, seeds, inputs, labour);
        -inf when it is not available or not affordable."""
        farm = obs["farms"][self.me]
        quads = list(farm["unlocked_quadrants"])
        if "SE" in quads or "NE" not in quads or "SW" not in quads:
            return -1e9
        money = float(farm["money"])
        if money < 4000 + GC_P["se_reserve"] + GC_P["rich_hire_budget"]:
            return -1e9
        day = int(obs["step"]) // 24
        self._values(obs)
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        n_se = min(GC_P["se_plots"], int((money - GC_P["rich_hire_budget"] - 4000 - GC_P["se_reserve"]) // 100))
        if n_se <= 0:
            return -1e9
        fert = self.pnow.get("FERTILIZER", 50)
        gain = self._straw_value(obs, day, n_se, shops) - self._straw_value(obs, day, 0, shops)
        if GC_P.get("straw_debug"):
            self._straw_path = []
            self._straw_value(obs, day, 0, shops)
            _GC_REPORT["gc_straw_path"] = " ".join("%d:%d" % x for x in self._straw_path)
            _GC_REPORT["gc_straw_inv0"] = int(obs["market"]["inventory"]["STRAWBERRY"])
            pl = []
            for side in (self.me, 1 - self.me):
                for row in obs["farms"][side]["tiles"]:
                    for t in row:
                        if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                            pl.append("%s%d/%d" % ("u" if side == self.me else "r", int(t["planted_day"]), int(t.get("yield_units", 0) or 0)))
            _GC_REPORT["gc_straw_plants"] = " ".join(pl)
            _GC_REPORT["gc_straw_shops"] = ",".join(shops)
        return gain - (4000 + n_se * (100 + 3 * fert + GC_P["straw_labor"]))

    def rich_eval_tom(self, obs):
        """Value of the SE quadrant as a tomato annex today (the controller's own se_on pricing)."""
        farm = obs["farms"][self.me]
        quads = list(farm["unlocked_quadrants"])
        if "SE" in quads or "NE" not in quads or "SW" not in quads:
            return -1e9
        money = float(farm["money"])
        if money < 4000 + GC_P["se_reserve"] + GC_P["rich_hire_budget"]:
            return -1e9
        day = int(obs["step"]) // 24
        self._values(obs)
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        n_se = GC_P["se_plots"]
        fert = self.pnow.get("FERTILIZER", 50)
        gain = self._tomato_value(obs, day, n_se, shops) - self._tomato_value(obs, day, 0, shops)
        return gain - (4000 + n_se * (50 + 2 * fert + GC_P["tomato_labor"]))

    def _straw_count(self, obs, day, n_free, shops):
        if not GC_P["straw_fc"] or day > GC_P["straw_fc_last"] or n_free <= 0:
            return 0
        fert = self.pnow.get("FERTILIZER", 50)
        life = min(16, 29 - day) + 1
        alt = GC_P["straw_alt_day"] * life
        cost = 100 + 3 * fert + GC_P["straw_labor"]
        cfw = GC_P["straw_count_future_w"]
        base = self._straw_value(obs, day, 0, shops, fw=cfw)
        best_n, best_v = 0, 0.0
        for n in range(GC_P["straw_fc_step"], min(n_free, GC_P["straw_fc_max"]) + 1, GC_P["straw_fc_step"]):
            v = self._straw_value(obs, day, n, shops, fw=cfw) - base - n * (cost + alt)
            if v > best_v:
                best_n, best_v = n, v
        _GC_REPORT["gc_straw_fc"] = _GC_REPORT.get("gc_straw_fc", 0) + best_n
        return best_n

    def _tomato_count(self, obs, day, n_free, shops, val):
        if not GC_P["tomato_on"] or day < GC_P["tomato_first"] or day > GC_P["tomato_last"] or n_free <= 0:
            return 0
        fert = self.pnow.get("FERTILIZER", 50)
        alt = GC_P["tomato_alt_day"] * 12.0      # what the tile earns as wheat/carrot over the same 12 days
        if GC_P.get("tomato_alt_dyn"):
            v_w = (6 * val["WHEAT"] - 10 - fert) / 4.0 + GC_P["wheat_feed_bonus"]
            cd_ = sum(2 if x == "PET_CAFE" else (1 if x == "FARMERS_MARKET" else 0) for x in shops)
            v_c = (4 * val["CARROT"] - 20 - fert) / 3.0 if cd_ >= GC_P["carrot_min_demand"] else -1e9
            alt = max(float(GC_P["tomato_alt_min"]), v_w, v_c) * min(12.0, 30.0 - day)
            _GC_REPORT["gc_tom_alt"] = "%d:%d" % (day, int(alt))
        cost = 50 + 2 * fert + GC_P["tomato_labor"]
        best_n, best_v = 0, 0.0
        base = self._tomato_value(obs, day, 0, shops)
        mx = GC_P["tomato_max_day"]
        if getattr(self, "se_day", None) == day:
            mx = max(mx, GC_P["se_plots"])
        for n in range(GC_P["tomato_step"], min(n_free, mx) + 1, GC_P["tomato_step"]):
            v = self._tomato_value(obs, day, n, shops) - base - n * (cost + alt)
            if v > best_v:
                best_n, best_v = n, v
        return best_n

    def _melon_value(self, obs, day, n):
        """Revenue of n melon plots planted today (6 units at age ~11), sold on arrival into a book drained one unit
        a day by the town centre and supplied by every visible melon plot maturing before them."""
        inv = float(obs["market"]["inventory"]["MELON"])
        sup = {}
        for farm in obs["farms"]:
            for row in farm["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "MELON":
                        hd = int(t["planted_day"]) + GC_P["melon_age"]
                        if hd >= day:
                            sup[hd] = sup.get(hd, 0) + 6
        rev = 0.0
        hd_new = day + GC_P["melon_age"]
        for d in range(day, 30):
            inv -= 1.0
            inv += sup.get(d, 0)
            if d == min(hd_new, 29) and n > 0:
                q = 6 * n
                tot = 0.0
                for k in range(q):
                    tot += _gc_price("MELON", int(inv) + k)
                rev += tot
                inv += q
        return rev

    def _melon_count(self, obs, day, n_free):
        if not GC_P["melon_on"] or day > GC_P["melon_last"] or n_free <= 0:
            return 0
        fert = self.pnow.get("FERTILIZER", 50)
        alt = GC_P["melon_alt_day"] * GC_P["melon_age"]
        cost = 80 + GC_P["melon_labor"]
        base = self._melon_value(obs, day, 0)
        best_n, best_v = 0, 0.0
        for n in range(1, min(n_free, GC_P["melon_max_day"]) + 1):
            v = self._melon_value(obs, day, n) - base - n * (cost + alt)
            if v > best_v:
                best_n, best_v = n, v
        return best_n

    def _carrot_book_at_harvest(self, obs, day, shops):
        """Projected carrot market inventory on the harvest day of a carrot planted today (age 3)."""
        inv = float(obs["market"]["inventory"]["CARROT"])
        per_day = 1.0 + sum((12.0 if sh == "PET_CAFE" else (6.0 if sh == "FARMERS_MARKET" else 0.0)) for sh in shops)
        sup = 0.0
        for farm in obs["farms"]:
            for row in farm["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "CARROT":
                        hd = int(t["planted_day"]) + 3
                        if day <= hd <= day + 3:
                            sup += GC_P["carrot_fc_units"]
        return inv - per_day * 3.0 + sup

    def _choose_crops(self, obs, day, free, replant, shops, val, counts):
        out = {}
        straw_room = 0
        if day <= GC_P["straw_last_plant"]:
            straw_room = max(0, GC_P["straw_target"] - counts.get("STRAWBERRY", 0))
        carrot_demand = sum(2 if s == "PET_CAFE" else (1 if s == "FARMERS_MARKET" else 0) for s in shops)
        fert = self.pnow.get("FERTILIZER", 50)
        # value per tile-day at today's prices (fertilized yields, seed and fertilizer paid)
        v_wheat = (6 * val["WHEAT"] - 10 - fert) / 4.0 + GC_P["wheat_feed_bonus"]
        v_carrot = (4 * val["CARROT"] - 20 - fert) / 3.0
        filler = "WHEAT"
        if carrot_demand >= GC_P["carrot_min_demand"] and v_carrot > GC_P["carrot_edge"] * v_wheat and day >= GC_P["carrot_first"]:
            filler = "CARROT"

        def fill(d):
            if filler == "CARROT" and d <= GC_P["carrot_last_plant"]:
                return "CARROT"
            if d <= GC_P["wheat_last_plant"]:
                return "WHEAT"
            if d <= GC_P["carrot_last_plant"]:
                return "CARROT"
            return None
        # wheat plots needed to feed the herd (a fertilized plot yields ~6 per 4-day cycle)
        wheat_now = max(0, counts.get("WHEAT", 0) - len(replant))  # plots that stay wheat today
        need_w = int(GC_P["feed_tiles_per_animal"] * self.n_animals + 0.999) if (day <= GC_P["wheat_last_plant"] and GC_P["feed_reserve_tiles"]) else 0
        slots = sorted(free, key=lambda p: _gc_dist(p, (4.5, 4.5))) + sorted(replant, key=lambda p: _gc_dist(p, (4.5, 4.5)))
        n_slots = len(slots)
        feed_first = max(0, need_w - wheat_now) if need_w > 0 else 0
        spare = max(0, n_slots - feed_first - (straw_room if day <= GC_P["straw_last_plant"] else 0))
        n_sfc = min(self._straw_count(obs, day, spare, shops), spare) if GC_P["straw_fc"] else 0
        straw_room += n_sfc
        spare -= n_sfc
        n_tom = min(self._tomato_count(obs, day, spare, shops, val), spare)
        self.n_tomato_today = n_tom
        n_mel = min(self._melon_count(obs, day, spare - n_tom), spare - n_tom) if GC_P["melon_on"] else 0
        placed_m = 0
        placed_t = 0
        straw_any = n_sfc > 0 and GC_P["straw_replant"]   # forecast strawberries may also take replant slots
        # feed wheat goes on the farthest slots (low-maintenance), tomatoes and strawberries near the shed
        far = sorted(slots, key=lambda p: -_gc_dist(p, (4.5, 4.5)))
        feed_tiles = set(far[:feed_first])
        # carrot forecast: quote at harvest (day+3) after the town's drain and every visible carrot plot maturing by
        # then; the k-th new carrot plot sells 4 units into a book already holding the previous k-1 plots' units
        n_car = 0; car_inv = None
        late = GC_P["late_plan"] and day >= GC_P["late_plan_from"]
        if GC_P["carrot_fc"] and day >= GC_P["carrot_first"] and (day <= GC_P["carrot_last_plant"] or late):
            car_inv = self._carrot_book_at_harvest(obs, day, shops)
        if late:
            def late_units(crop, bonus):
                cd = _GC_CROPS[crop]; ws = (cd["my"] + 1) // 2
                if day + cd["fy"] > 29:
                    return 0
                return min(cd["mx"], 1 + bonus * len([d for d in range(day + ws, day + cd["my"] + 1) if d <= 29]))
            uw = late_units("WHEAT", 2); uc = late_units("CARROT", 2 if GC_P["fert_carrots"] else 1)
            vw_late = uw * val["WHEAT"] - 10 - fert if uw else -1e9
            if car_inv is None:
                car_inv = float(obs["market"]["inventory"]["CARROT"])
        for pos in slots:
            if pos in feed_tiles:
                out[pos] = "WHEAT"; continue
            if straw_room > 0 and (pos in free or straw_any):
                out[pos] = "STRAWBERRY"; straw_room -= 1
            elif placed_t < n_tom:
                out[pos] = "TOMATO"; placed_t += 1
            elif placed_m < n_mel:
                out[pos] = "MELON"; placed_m += 1
            elif late:
                pc = _gc_price("CARROT", int(car_inv + uc * n_car + 2))
                vc_late = uc * pc - 20 - (fert if GC_P["fert_carrots"] else 0) if uc else -1e9
                if max(vc_late, vw_late) >= GC_P["late_plan_min"]:
                    if vc_late >= vw_late:
                        out[pos] = "CARROT"; n_car += 1
                    else:
                        out[pos] = "WHEAT"
                        _GC_REPORT["gc_late_wheat"] = _GC_REPORT.get("gc_late_wheat", 0) + 1
            elif car_inv is not None:
                q = car_inv + 4 * n_car + 2
                pc = _gc_price("CARROT", int(q))
                vc = (4 * pc - 20 - fert) / 3.0
                vw = v_wheat if day <= GC_P["wheat_last_plant"] else -1e9
                if vc > GC_P["carrot_edge"] * vw and vc > 0:
                    out[pos] = "CARROT"; n_car += 1
                elif day <= GC_P["wheat_last_plant"]:
                    out[pos] = "WHEAT"
            else:
                c = fill(day)
                if c:
                    out[pos] = c
        if n_car:
            _GC_REPORT["gc_carrot_fc"] = _GC_REPORT.get("gc_carrot_fc", 0) + n_car
        if placed_m:
            _GC_REPORT["gc_melon"] = _GC_REPORT.get("gc_melon", 0) + placed_m
        n_tom = n_tom - placed_t
        if self.n_tomato_today:
            _GC_REPORT["gc_tomato_planned"] = _GC_REPORT.get("gc_tomato_planned", 0) + self.n_tomato_today - n_tom
        return out

    # ------------------------------------------------------------------ routing
    def _spawns(self, n_hires, farmer_pos):
        occ = {p: 0 for p in _GC_ACCESS}
        if tuple(farmer_pos) in occ:
            occ[tuple(farmer_pos)] += 1
        out = []
        for _ in range(n_hires):
            best = min(_GC_ACCESS, key=lambda p: (occ[p], _GC_ACCESS.index(p)))
            occ[best] += 1
            out.append(best)
        return out

    @staticmethod
    def _cost(start, visits):
        t = 0
        if any(v.wheat for v in visits): t += 1
        if any(v.fert for v in visits): t += 1
        t += len({v.anim for v in visits if v.anim})
        pos = start
        carry = 0
        for v in visits:
            t += abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts)
            pos = v.pos; carry += v.carry
        if carry >= GC_P["deliver_min"]:
            a = _gc_near_access(pos)
            t += abs(pos[0] - a[0]) + abs(pos[1] - a[1]) + 1
        return t

    def _vrp(self, visits, h, starts=None, caps=None):
        def k_far(v):
            return (0 if v.must else 1, -(abs(v.pos[0] - 4.5) + abs(v.pos[1] - 4.5)) if v.must else -v.value / (len(v.acts) + 2.0))

        def k_ang(v):
            return (0 if v.must else 1, _gc_math.atan2(v.pos[1] - 4.5, v.pos[0] - 4.5) if v.must else -v.value / (len(v.acts) + 2.0))

        def k_val(v):
            return (0 if v.must else 1, -v.value / (len(v.acts) + 2.0))
        best = None
        for key in (k_far, k_ang, k_val):
            routes, spawns, unserved = self._vrp1(visits, h, key, starts, caps)
            nm = sum(1 for v in unserved if v.must)
            if self.final and GC_P["final_by_value"]:
                nm = 0      # final day: every visit is "must"; what matters is the value left behind
            uv = sum(v.value for v in unserved)
            tc = sum(self._rcost(spawns[u], r) for u, r in enumerate(routes))
            sc = (nm, uv, tc)
            if best is None or sc < best[0]:
                best = (sc, routes, spawns, unserved)
        routes, spawns, unserved = best[1], best[2], best[3]
        if float(GC_P["deliver_prem"] or 0.0) > 0:
            # premium deliveries first whenever the route can afford the detour (the day's cash depends on them)
            for u, r in enumerate(routes):
                if len(r) > 1 and any(self._prem_value(v) >= float(GC_P["deliver_prem"]) for v in r):
                    cap = caps[u] if caps is not None else self._cap(u)
                    new = self._order_anim_first(spawns[u], r, cap)
                    if self._rcost(spawns[u], new) <= cap:
                        routes[u] = new
        return routes, spawns, unserved

    def _order_anim_first(self, start, vs, cap):
        """Animals (premium goods) first so their products reach the shed early; keep the plain order if that costs more than 2 turns."""
        plain = self._order(start, vs)
        dprem = float(GC_P["deliver_prem"] or 0.0)
        pr = [v for v in vs if dprem > 0 and self._prem_value(v) >= dprem]
        an = [v for v in vs if v.tag == "A" and v not in pr]
        if not (an or pr) or len(an) + len(pr) == len(vs):
            if pr and an:
                pass
            else:
                return plain
        # premium deliveries first (they sell today, before the rival), then the animals, then the rest
        head = self._order(start, pr) if pr else []
        pos = head[-1].pos if head else start
        a_ord = self._order(pos, an) if an else []
        pos = a_ord[-1].pos if a_ord else pos
        rest = self._order(pos, [v for v in vs if v not in pr and v not in an])
        mixed = head + a_ord + rest
        cm = self._rcost(start, mixed)
        if pr and cm <= cap:
            return mixed
        if cm <= min(cap, self._rcost(start, plain) + 2):
            return mixed
        return plain

    @staticmethod
    def _order(start, vs):
        if len(vs) <= 1:
            return list(vs)
        rem = list(vs); out = []; pos = start
        while rem:
            j = min(range(len(rem)), key=lambda i: abs(pos[0] - rem[i].pos[0]) + abs(pos[1] - rem[i].pos[1]))
            v = rem.pop(j); out.append(v); pos = v.pos
        n = len(out)
        # 2-opt on a path that returns to the shed area (so routes end near a delivery tile)
        end = (4.5, 4.5)
        improved = True; it = 0
        while improved and it < 8:
            improved = False; it += 1
            for i in range(0, n - 1):
                a = start if i == 0 else out[i - 1].pos
                b = out[i].pos
                for j in range(i + 1, n):
                    c = out[j].pos
                    d = out[j + 1].pos if j + 1 < n else end
                    old = abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(c[0] - d[0]) + abs(c[1] - d[1])
                    new = abs(a[0] - c[0]) + abs(a[1] - c[1]) + abs(b[0] - d[0]) + abs(b[1] - d[1])
                    if new < old - 1e-9:
                        out[i:j + 1] = out[i:j + 1][::-1]; improved = True
                        b = out[i].pos
        return out

    def _rcost(self, start, r):
        """Turns for one route: pickups at the spawn tile, then moves + actions (no return trip), plus the delivery
        trip a premium load (deliver_prem) still needs after its last premium visit."""
        t = 0
        if any(v.wheat for v in r): t += 1
        if any(v.fert for v in r): t += 1
        t += len({v.anim for v in r if v.anim})
        pos = start
        dprem = float(GC_P["deliver_prem"] or 0.0)
        pv = 0.0; last_p = None
        for v in r:
            t += abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts)
            pos = v.pos
            if dprem > 0:
                if v.tag == "S":
                    pv = 0.0; last_p = None
                else:
                    x = self._prem_value(v)
                    pv += x
                    if x > 0:
                        last_p = v.pos
        if dprem > 0 and pv >= dprem and last_p is not None:
            t += self._ret(last_p) + 1   # the stop must land by hour 22 (its goods sell that day)
        return t

    @staticmethod
    def _ret(pos):
        a = _gc_near_access(pos)
        return abs(pos[0] - a[0]) + abs(pos[1] - a[1]) + 1

    def _vrp1(self, visits, h, order_key, starts=None, caps=None):
        n_units = 1 + h
        spawns = [(4, 4)] + self._spawns(h, (4, 4))
        if starts is not None:
            spawns = list(starts); n_units = len(spawns)
        d28r = GC_P["d28_cap"] is not None and getattr(self, "day", 0) == 28 and not self.final
        fr = (self.final and GC_P["final_ret"]) or d28r
        s = GC_P["drop_slack"] if not self.final else 5
        n0 = getattr(self, "n0_hires", 9)
        if fr:
            # final day: every route ends with a delivery that must land by hour 22 (the last processed step)
            fc = GC_P["d28_cap"] if d28r else GC_P["final_cap"]
            caps = [fc] + [(fc if i < n0 else fc - 1) for i in range(h)]
        elif caps is None:
            caps = [23 - s] + [(23 if i < n0 else 22) - s for i in range(h)]
        ret = self._ret
        routes = [[] for _ in range(n_units)]
        costs = [0] * n_units
        flags = [[False, False, set()] for _ in range(n_units)]   # has wheat, has fert, animal kinds

        unserved = []
        dprem = float(GC_P["deliver_prem"] or 0.0)
        pvals = [0.0] * n_units
        for v in sorted(visits, key=order_key):
            best = None
            xv = self._prem_value(v) if dprem > 0 else 0.0
            for u in range(n_units):
                r = routes[u]; fl = flags[u]
                extra = (1 if v.wheat and not fl[0] else 0) + (1 if v.fert and not fl[1] else 0) + (1 if v.anim and v.anim not in fl[2] else 0)
                if dprem > 0 and xv > 0 and pvals[u] < dprem and pvals[u] + xv >= dprem:
                    extra += self._ret(v.pos) + 1   # this load will need a delivery trip
                base = costs[u] + extra + len(v.acts)
                if base > caps[u]:
                    continue
                r_old = ret(r[-1].pos) if (fr and r) else 0
                prev = spawns[u]
                for i in range(len(r) + 1):
                    nxt = r[i].pos if i < len(r) else None
                    dd = abs(prev[0] - v.pos[0]) + abs(prev[1] - v.pos[1])
                    if nxt is not None:
                        dd += abs(v.pos[0] - nxt[0]) + abs(v.pos[1] - nxt[1]) - abs(prev[0] - nxt[0]) - abs(prev[1] - nxt[1])
                    c = base + dd
                    if fr:
                        r_new = ret(v.pos) if i == len(r) else r_old
                        if c + r_new <= caps[u] and (best is None or c + r_new - costs[u] - r_old < best[0]):
                            best = (c + r_new - costs[u] - r_old, u, i, c)
                    elif c <= caps[u] and (best is None or c - costs[u] < best[0]):
                        best = (c - costs[u], u, i, c)
                    if nxt is not None:
                        prev = nxt
            if best is None:
                unserved.append(v); continue
            _, u, i, c = best
            routes[u].insert(i, v); costs[u] = c
            pvals[u] += xv
            fl = flags[u]
            if v.wheat: fl[0] = True
            if v.fert: fl[1] = True
            if v.anim: fl[2].add(v.anim)
        # local search: 2-opt inside each route (animal cluster first), then try to place unserved visits again
        for u in range(n_units):
            if len(routes[u]) > 2:
                new = self._order_anim_first(spawns[u], routes[u], caps[u])
                c = self._rcost(spawns[u], new)
                if fr:
                    if c + ret(new[-1].pos) <= caps[u]:
                        routes[u] = new; costs[u] = c
                elif c <= caps[u] or c <= costs[u] or not GC_P["order_cap_fix"]:
                    routes[u] = new; costs[u] = c
        if unserved:
            left = []
            for v in unserved:
                best = None
                for u in range(n_units):
                    r = routes[u]
                    for i in range(len(r) + 1):
                        rr = r[:i] + [v] + r[i:]
                        c = self._rcost(spawns[u], rr) + (ret(rr[-1].pos) if fr else 0)
                        if c <= caps[u] and (best is None or c < best[0]):
                            best = (c, u, i)
                if best is None:
                    left.append(v)
                else:
                    c, u, i = best
                    routes[u].insert(i, v); costs[u] = self._rcost(spawns[u], routes[u])
            unserved = left
        return routes, spawns, unserved

    @staticmethod
    def _order(start, vs):
        """Nearest neighbour then 2-opt for an open path starting at `start`."""
        if len(vs) <= 1:
            return list(vs)
        rem = list(vs); out = []; pos = start
        while rem:
            j = min(range(len(rem)), key=lambda i: abs(pos[0] - rem[i].pos[0]) + abs(pos[1] - rem[i].pos[1]))
            v = rem.pop(j); out.append(v); pos = v.pos
        n = len(out)
        P = [v.pos for v in out]
        improved = True; it = 0
        while improved and it < 8:
            improved = False; it += 1
            for i in range(0, n - 1):
                a = start if i == 0 else P[i - 1]
                for j in range(i + 1, n):
                    b = P[i]; c = P[j]
                    old = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    new = abs(a[0] - c[0]) + abs(a[1] - c[1])
                    if j + 1 < n:
                        d = P[j + 1]
                        old += abs(c[0] - d[0]) + abs(c[1] - d[1])
                        new += abs(b[0] - d[0]) + abs(b[1] - d[1])
                    if new < old:
                        out[i:j + 1] = out[i:j + 1][::-1]; P[i:j + 1] = P[i:j + 1][::-1]; improved = True
        return out

    def _route_and_hire(self, visits, cash, final, day):
        best = None
        first = day == GC_P["start"] // 24 or (bool(GC_P.get("handover_fix3")) and day == getattr(self, "_first_day", None))
        lo = 0 if (first or final) else max(0, self.last_hires - 3)
        hi = GC_P["max_hands_final"] if final else GC_P["max_hands"]
        while lo > 0 and sum(_gc_fib(q) for q in range(lo)) > cash - 20:
            lo -= 1   # a farm that wakes up broke must still get a plan (fewer hands), not a crashed day
        for h in range(lo, hi + 1):
            cost = sum(_gc_fib(q) for q in range(h))
            if h > 0 and cost > cash - 20:
                break
            routes, spawns, unserved = self._vrp(visits, h)
            keep_idx = [u for u in range(len(routes)) if u == 0 or routes[u]]
            if GC_P["hire_compact"] and len(keep_idx) < len(routes):
                # hands the plan gave nothing to are not hired
                h2 = len(keep_idx) - 1
                sp2 = [(4, 4)] + self._spawns(h2, (4, 4)); r2 = [routes[u] for u in keep_idx]
                if all(self._rcost(sp2[i], r2[i]) <= self._cap(i) for i in range(len(r2))):
                    routes, spawns = r2, sp2
                    if h2 < h:
                        cost = sum(_gc_fib(q) for q in range(h2))
                        h = h2
            if final and GC_P["final_by_value"]:
                pen = sum(v.value for v in unserved)
            else:
                pen = sum((v.value + (1e5 if v.must else 0.0)) for v in unserved)
            ovf = 0
            if GC_P["ovf_hire"] and not final:
                if GC_P["stop_v2"]:
                    rr = [list(r) for r in routes]
                    ovf, popped = self._plan_stops(rr, spawns)
                    dprem = float(GC_P["deliver_prem"] or 0.0)
                    if dprem > 0:
                        undel = sum(self._prem_after_stop(r) for r in rr if self._prem_after_stop(r) >= dprem)
                        pen += undel * GC_P["deliver_prem_w"]
                        if undel > 0:
                            ovf += 1   # keeps the search going: more hands may make the delivery fit
                else:
                    _d, ovf, popped = self._plan_drops([list(r) for r in routes], spawns)
                pen += ovf * GC_P["ovf_value"] + popped
            score = -pen - GC_P["hire_cost_w"] * cost
            if best is None or score > best[0]:
                best = (score, h, routes, spawns, sum(v.value for v in unserved))
                self._last_unserved = (sum(1 for v in unserved if v.must), len(unserved), sorted({v.tag for v in unserved}))
            if not unserved and ovf == 0 and best[1] < h:
                break
        _GC_REPORT["gc_unserved"] += int(best[4])
        return best[2], best[1], best[3]

    # ------------------------------------------------------------------ execution
    def _compile(self, routes, spawns, hour0=True):
        qs = []
        for u, r in enumerate(routes):
            q = []
            if u == 0 and hour0:
                q.append((spawns[0], ["PASS"], None))   # keep the farmer on (4,4) at hour 0 so hires spawn where planned
            wheat = sum(v.wheat for v in r); fert = sum(v.fert for v in r)
            if wheat:
                q.append((spawns[u], ["PICKUP", "WHEAT", wheat], None))
            if fert:
                q.append((spawns[u], ["PICKUP", "FERTILIZER", fert], None))
            for an in ("COW", "SHEEP", "GOOSE"):
                n = sum(1 for v in r if v.anim == an)
                if n:
                    q.append((spawns[u], ["PICKUP", an, n], None))
            drop_at = self.drop_at.get(u)
            for k, v in enumerate(r):
                for a in v.acts:
                    q.append((v.pos, list(a), v))
                if drop_at is not None and k == drop_at:
                    q.append((_gc_near_access(v.pos), ["DROP"], None))
            qs.append(q)
        return qs

    def _cap(self, u):
        s = GC_P["drop_slack"] if not self.final else 5
        return (23 if u == 0 else (23 if u <= self.n0_hires else 22)) - s

    @staticmethod
    def _stop_visit(pos):
        return _GcVisit(_gc_near_access(pos), [["DROP"]], value=0.0, must=True, tag="S")

    @staticmethod
    def _eod_carry(r):
        c = 0
        for v in r:
            if v.tag == "S":
                c = 0
            else:
                c += v.carry
        return c

    @staticmethod
    def _ins_delta(start, r, v):
        """Cheapest insertion of v into route r: (extra turns, index)."""
        extra = len(v.acts)
        if v.wheat and not any(x.wheat for x in r): extra += 1
        if v.fert and not any(x.fert for x in r): extra += 1
        if v.anim and all(x.anim != v.anim for x in r): extra += 1
        best_d, best_i = None, 0
        prev = start
        n = len(r)
        for i in range(n + 1):
            dd = abs(prev[0] - v.pos[0]) + abs(prev[1] - v.pos[1])
            if i < n:
                nx = r[i].pos
                dd += abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]) - abs(prev[0] - nx[0]) - abs(prev[1] - nx[1])
                prev = nx
            if best_d is None or dd < best_d:
                best_d, best_i = dd, i
        return best_d + extra, best_i

    @staticmethod
    def _prem_value(v):
        g = v.gain or {}
        if g.get("prod") in _GC_PREMIUM:
            return float(g.get("units", v.carry)) * float(g.get("pv", 0.0))
        return 0.0

    def _prem_after_stop(self, r):
        val = 0.0
        for v in r:
            if v.tag == "S":
                val = 0.0
            else:
                val += self._prem_value(v)
        return val

    def _plan_stops(self, routes, spawns, caps_in=None):
        """Insert shed-stop visits (tag S) until the goods carried at the end of the day fit the shed room.
        A stop that does not fit its route moves visits after it to other routes (cheapest feasible insertion),
        popping optional ones only when nobody can take them. Mutates `routes`. Returns (overflow units, popped value)."""
        room = GC_P["eod_room"]
        if GC_P["d28_zero_reserve"] and getattr(self, "day", 0) == 28:
            room = GC_P["eod_room_d28"]
        if GC_P["room_v3"]:
            # lots held in the shed through the day (floors) still occupy it tonight
            held = sum(int(v) for v in getattr(self, "_held_now", {}).values())
            room = max(GC_P["room_v3_min"], room - held)
        popped = 0.0
        n = len(routes)
        caps = list(caps_in) if caps_in is not None else [self._cap(u) for u in range(n)]
        costs = [self._rcost(spawns[u], routes[u]) for u in range(n)]
        tried = set()
        dprem = float(GC_P["deliver_prem"] or 0.0)
        for _it in range(3 * n + 5):
            total = sum(self._eod_carry(r) for r in routes)
            pending = [u for u in range(n) if dprem > 0 and u not in tried and self._prem_after_stop(routes[u]) >= dprem]
            if total <= room and not pending:
                break
            best = None
            for u in range(n):
                r = routes[u]
                if u in tried or not r:
                    continue
                if total <= room and u not in pending:
                    continue
                if u not in pending and self._eod_carry(r) < GC_P["deliver_min"]:
                    continue
                last_s = max((i for i, v in enumerate(r) if v.tag == "S"), default=-1)
                carried = 0
                t = 0; pos = spawns[u]
                if any(v.wheat for v in r): t += 1
                if any(v.fert for v in r): t += 1
                t += len({v.anim for v in r if v.anim})
                pcar = 0.0
                kp = max((i for i, v in enumerate(r) if i > last_s and self._prem_value(v) >= dprem), default=None) if u in pending else None
                for k, v in enumerate(r):
                    t += abs(pos[0] - v.pos[0]) + abs(pos[1] - v.pos[1]) + len(v.acts); pos = v.pos
                    if k <= last_s:
                        continue
                    carried += v.carry
                    if dprem > 0:
                        pcar += self._prem_value(v)
                    if kp is not None and k != kp:
                        continue
                    if carried < GC_P["deliver_min"] and not (u in pending and pcar >= dprem):
                        continue
                    a = _gc_near_access(v.pos)
                    back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
                    if t + back + 1 > caps[u] - 1:     # the stop must land by hour 22 so its goods sell today
                        continue
                    if k + 1 < len(r):
                        nx = r[k + 1].pos
                        extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
                    else:
                        extra = back + 1
                    sc = (carried + pcar / 50.0) / (extra + 0.5)
                    if best is None or sc > best[0]:
                        best = (sc, u, k, extra)
            if best is None:
                break
            _, u, k, extra = best
            if not GC_P["multi_stop"]:
                tried.add(u)
            r2 = routes[u][:k + 1] + [self._stop_visit(routes[u][k].pos)] + routes[u][k + 1:]
            c2 = costs[u] + extra
            moved = []
            pv = 0.0
            guard = 0
            while c2 > caps[u] and guard < 15:
                guard += 1
                cands = []
                for i in range(k + 2, len(r2)):
                    v = r2[i]
                    if v.tag == "S":
                        continue
                    sav = c2 - self._rcost(spawns[u], r2[:i] + r2[i + 1:])
                    cands.append((sav, i))
                if not cands:
                    break
                cands.sort(key=lambda x: -x[0])
                done = False
                for sav, i in cands[:6]:
                    v = r2[i]
                    bw = None
                    for w in range(n):
                        if w == u:
                            continue
                        d, j = self._ins_delta(spawns[w], routes[w], v)
                        if costs[w] + d <= caps[w] and (bw is None or d < bw[0]):
                            bw = (d, w, j)
                    if bw is not None:
                        d, w, j = bw
                        routes[w] = routes[w][:j] + [v] + routes[w][j:]
                        costs[w] += d
                        moved.append((w, v))
                        r2 = r2[:i] + r2[i + 1:]
                        c2 = self._rcost(spawns[u], r2)
                        done = True
                        break
                if not done:
                    opt = [i for i in range(k + 2, len(r2)) if not r2[i].must and r2[i].tag != "S"]
                    if not opt:
                        break
                    j = min(opt, key=lambda i: r2[i].value / (len(r2[i].acts) + 1.0))
                    pv += r2[j].value
                    r2 = r2[:j] + r2[j + 1:]
                    c2 = self._rcost(spawns[u], r2)
            if c2 <= caps[u]:
                routes[u] = r2; costs[u] = c2; popped += pv
            else:
                # undo the moves
                tried.add(u)
                for w, v in moved:
                    routes[w] = [x for x in routes[w] if x is not v]
                    costs[w] = self._rcost(spawns[w], routes[w])
        return max(0, sum(self._eod_carry(r) for r in routes) - room), popped

    def _plan_drops(self, routes, spawns):
        """Shed stops so the end-of-day drop fits in the shed. Mutates routes (may pop optional visits after a stop).
        Returns (drop_at, units still over the room, value of popped visits)."""
        drop_at = {}
        room = GC_P["eod_room"]
        carried = [sum(v.carry for v in r) for r in routes]
        total = sum(carried)
        done = set(); popped = 0.0
        guard = 0
        while (total > room or GC_P["always_drop"]) and guard < 40:
            guard += 1
            best = None
            for u, r in enumerate(routes):
                if u in done or not r or carried[u] < GC_P["deliver_min"]:
                    continue
                cap = 23 if u == 0 else (23 if u <= self.n0_hires else 22)
                k, extra, got = self._drop_best(spawns[u], r, cap + 99)
                if k is None:
                    continue
                sc = got / (extra + 0.5)
                if best is None or sc > best[0]:
                    best = (sc, u, k, extra, got)
            if best is None:
                break
            _, u, k, extra, got = best
            cap = 23 if u == 0 else (23 if u <= self.n0_hires else 22)
            r = routes[u]
            # make room by dropping the lowest-value optional visits after the stop
            while self._rcost(spawns[u], r) + extra > cap:
                opt = [i for i, v in enumerate(r) if not v.must and i > k]
                if not opt:
                    break
                j = min(opt, key=lambda i: r[i].value / (len(r[i].acts) + 1.0))
                popped += r[j].value
                r.pop(j)
            if self._rcost(spawns[u], r) + extra <= cap:
                drop_at[u] = k; total -= got
            done.add(u)
        return drop_at, max(0, total - room), popped

    def _is_premium_visit(self, v):
        t = self.tiles_today[v.pos[1]][v.pos[0]] if getattr(self, "tiles_today", None) else None
        if not isinstance(t, dict):
            return False
        if t.get("kind") == "PLANT":
            return t.get("crop") in ("STRAWBERRY", "TOMATO", "MELON") and any(a[0] == "HARVEST" for a in v.acts)
        if t.get("animal") in ("COW", "SHEEP"):
            return any(a[0] == "HARVEST" for a in v.acts)
        return False

    def _drop_best(self, spawn, r, cap):
        """(index, extra turns, goods delivered) of the best single shed stop in a route."""
        base = self._rcost(spawn, r)
        best = None; carried = 0
        for k, v in enumerate(r):
            carried += v.carry
            if carried < GC_P["deliver_min"]:
                continue
            a = _gc_near_access(v.pos)
            back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
            if k + 1 < len(r):
                nx = r[k + 1].pos
                extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
            else:
                extra = back + 1
            if base + extra > cap:
                continue
            prem = sum(x.carry for x in r[:k + 1] if x.tag == "A")
            sc = (carried + GC_P["prem_w"] * prem) / (extra + 0.5)
            if best is None or sc > best[0]:
                best = (sc, k, extra, carried)
        if best is None:
            return None, 0, 0
        return best[1], best[2], best[3]

    def _drop_point(self, spawn, r, cap):
        """Index after which a shed stop is inserted (None = rely on the end-of-day drop).
        Routes with animal goods stop right after their last animal (premium goods sell early);
        otherwise maximise goods delivered per extra turn, within the unit's turn budget."""
        if not r:
            return None
        base = self._rcost(spawn, r)
        last_a = max((k for k, v in enumerate(r) if v.tag == "A" and v.carry > 0), default=None)
        if last_a is not None and GC_P["drop_after_animals"]:
            v = r[last_a]
            a = _gc_near_access(v.pos)
            back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
            if last_a + 1 < len(r):
                nx = r[last_a + 1].pos
                extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
            else:
                extra = back + 1
            if base + extra <= cap:
                return last_a
        best = None; carried = 0
        for k, v in enumerate(r):
            carried += v.carry
            if carried < GC_P["deliver_min"]:
                continue
            a = _gc_near_access(v.pos)
            back = abs(v.pos[0] - a[0]) + abs(v.pos[1] - a[1])
            if k + 1 < len(r):
                nx = r[k + 1].pos
                extra = back + 1 + abs(a[0] - nx[0]) + abs(a[1] - nx[1]) - (abs(v.pos[0] - nx[0]) + abs(v.pos[1] - nx[1]))
            else:
                extra = back + 1
            if base + extra > cap:
                continue
            prem = sum(v.carry for v in r[:k + 1] if v.tag == "A")
            score = (carried + 2.0 * prem) / (extra + 0.5) - 0.15 * k
            if best is None or score > best[0]:
                best = (score, k)
        return None if best is None else best[1]

    def _useful(self, act, tile, inv, seeds, planting, shed, room):
        op = act[0]
        if op == "PASS":
            return True
        if op == "PICKUP":
            return shed.get(act[1], 0) > 0
        if op == "DROP":
            n = sum(int(x) for x in inv.values())
            return n > 0 and room[0] >= n
        if op == "PLACE":
            return inv.get(act[1], 0) > 0 and isinstance(tile, dict) and tile.get("kind") == _GC_ANIM[act[1]]["st"] and "animal" not in tile
        if tile == "LOCKED":
            return False
        if op == "PLANT":
            return tile is None and seeds.get(act[1], 0) - planting.get(act[1], 0) > 0
        if op == "DIG":
            return tile is not None and not (isinstance(tile, dict) and "animal" in tile)
        if op in ("BUILD_COOP", "BUILD_PASTURE"):
            return tile is None
        if not isinstance(tile, dict):
            return False
        k = tile.get("kind")
        if op == "WATER":
            return k == "PLANT" and not tile.get("watered_today")
        if op == "HARVEST":
            return int(tile.get("yield_units", 0) or 0) > 0 and (k == "PLANT" or "animal" in tile)
        if op == "FERTILIZE":
            return k == "PLANT" and inv.get("FERTILIZER", 0) > 0
        if op == "FEED":
            return "animal" in tile and not tile.get("fed_today") and inv.get("WHEAT", 0) > 0
        if op == "CARE":
            return "animal" in tile and not tile.get("cared_today")
        if op == "COLLECT_FERTILIZER":
            return "animal" in tile and bool(tile.get("fertilizer_available"))
        return True

    def _trim_queue(self, q, pos, turns_left):
        """Drop optional visits (latest, lowest value first) until the remaining queue fits the turns left."""
        def cost(qq):
            t = 0; p = pos
            for tgt, a, v in qq:
                t += abs(p[0] - tgt[0]) + abs(p[1] - tgt[1]) + 1
                p = tgt
            return t
        guard = 0
        while q and cost(q) > turns_left and guard < 30:
            guard += 1
            opt = {id(v): v for _, _, v in q if v is not None and not v.must}
            if not opt:
                break
            worst = min(opt.values(), key=lambda v: v.value / (len(v.acts) + 1.0))
            q[:] = [it for it in q if it[2] is not worst]
            _GC_REPORT["gc_trimmed"] = _GC_REPORT.get("gc_trimmed", 0) + 1
        if GC_P.get("mtrim_fix") and q:
            # mtrim_fix: only must visits are left and they still overrun (unplanned refill pickups, a late hire's
            # actual spawn): the queue would run in order and lose its last must visits (often the thirsty day-2
            # water of a new wheat/carrot). Strip their deferrable parts instead, latest first: fertilizer collects,
            # fertilizations (and a fertilizer pickup nothing needs any more), then plantings (with their water).
            def cost2(qq):
                t = 0; p = tuple(pos)
                for tgt, a, v in qq:
                    if GC_P["shed_any"] and a[0] in ("PICKUP", "DROP"):
                        tgt = p if p in _GC_ACCESS_SET else _gc_near_access(p)
                    t += abs(p[0] - tgt[0]) + abs(p[1] - tgt[1]) + 1
                    p = tuple(tgt)
                return t
            surv = GC_P.get("mtrim_fix") == "surv"
            tl_ = getattr(self, "_tiles_now", None)

            def last_lost_surv(qq):
                """surv variant: index of the last item the turn budget cannot reach that saves a life tonight (WATER of a
                plant unwatered since yesterday, FEED of an animal unfed since yesterday); None when every such item fits."""
                if tl_ is None:
                    return None
                t = 0; p = tuple(pos); out = None
                for i, (tgt, a, v) in enumerate(qq):
                    if GC_P["shed_any"] and a[0] in ("PICKUP", "DROP"):
                        tgt = p if p in _GC_ACCESS_SET else _gc_near_access(p)
                    t += abs(p[0] - tgt[0]) + abs(p[1] - tgt[1]) + 1
                    p = tuple(tgt)
                    if t > turns_left and a[0] in ("WATER", "FEED"):
                        tile = tl_[tgt[1]][tgt[0]]
                        if not isinstance(tile, dict):
                            continue
                        if a[0] == "WATER" and tile.get("kind") == "PLANT" and not tile.get("watered_today") and int(tile.get("consecutive_unwatered", 0)) >= 1:
                            out = i
                        elif a[0] == "FEED" and "animal" in tile and not tile.get("fed_today") and int(tile.get("consecutive_unfed", 0)) >= 1:
                            out = i
                return out
            for stage in ("COLLECT_FERTILIZER", "FERTILIZE", "PLANT"):
                while q and cost2(q) > turns_left:
                    lim = len(q)
                    if surv:
                        k_ = last_lost_surv(q)
                        if k_ is None:
                            break
                        lim = k_
                    idx = [i for i, it in enumerate(q[:lim]) if it[2] is not None and it[1][0] == stage]
                    if not idx:
                        break
                    i = idx[-1]; v = q[i][2]
                    if stage == "PLANT" and v.tag == "P":
                        q[:] = [it for it in q if it[2] is not v]
                    elif stage == "PLANT":
                        drop = {i}
                        if i + 1 < len(q) and q[i + 1][1][0] == "WATER" and q[i + 1][2] is v:
                            drop.add(i + 1)
                        q[:] = [it for j, it in enumerate(q) if j not in drop]
                    else:
                        q.pop(i)
                        if stage == "FERTILIZE" and not any(it[1][0] == "FERTILIZE" for it in q):
                            q[:] = [it for it in q if not (it[1][0] == "PICKUP" and len(it[1]) > 1 and it[1][1] == "FERTILIZER")]
                    _GC_REPORT["gc_mtrim"] = _GC_REPORT.get("gc_mtrim", 0) + 1

    def _dispatch(self, u, pos, inv, turns_left, tiles, sim, seeds, shed, claimed, day, hour):
        """Idle unit: queue the best remaining unclaimed job it can finish today (value per turn)."""
        if turns_left <= 1:
            return None
        cache = getattr(self, "_dcache", None)
        if cache is None or cache[0] != (day, hour):
            cands = []
            for y in range(10):
                for x in range(10):
                    key = (x, y)
                    t = sim[key] if key in sim else tiles[y][x]
                    if not isinstance(t, dict):
                        continue
                    if t.get("kind") == "PLANT":
                        v = self._plant_visit(key, t, day, self.val, self.final)
                    elif t.get("animal"):
                        v = self._animal_visit(key, t, day, self.val, self.final)
                    else:
                        v = None
                    if v is None:
                        continue
                    acts = []
                    for a in v.acts:
                        op = a[0]
                        if op == "WATER" and t.get("watered_today"): continue
                        if op == "FEED" and t.get("fed_today"): continue
                        if op == "CARE" and t.get("cared_today"): continue
                        if op == "COLLECT_FERTILIZER" and not t.get("fertilizer_available"): continue
                        if op == "HARVEST" and int(t.get("yield_units", 0) or 0) <= 0: continue
                        if op in ("PLANT", "DIG", "BUILD_COOP", "BUILD_PASTURE", "PLACE"): continue
                        acts.append(list(a))
                    if not acts:
                        continue
                    # value of the remaining actions only (rough: scale by the share of actions left)
                    val = v.value * len(acts) / max(1, len(v.acts))
                    if any(a[0] == "CARE" for a in acts) and not t.get("fed_today") and not any(a[0] == "FEED" for a in acts):
                        acts = [a for a in acts if a[0] != "CARE"]
                        if not acts:
                            continue
                    cands.append((key, acts, val, v.must))
            self._dcache = ((day, hour), cands)
            cache = self._dcache
        best = None
        for key, acts, val, must in cache[1]:
            if key in claimed:
                continue
            need_w = any(a[0] == "FEED" for a in acts) and inv.get("WHEAT", 0) <= 0
            need_f = any(a[0] == "FERTILIZE" for a in acts) and inv.get("FERTILIZER", 0) <= 0
            acts2 = acts
            if need_f:
                acts2 = [a for a in acts2 if a[0] != "FERTILIZE"]
            detour = 0; pick = None
            if need_w:
                if shed.get("WHEAT", 0) <= 0:
                    acts2 = [a for a in acts2 if a[0] not in ("FEED", "CARE")]
                else:
                    a0 = _gc_near_access(pos)
                    detour = _gc_dist(pos, a0) + 1 + _gc_dist(a0, key) - _gc_dist(pos, key)
                    pick = a0
            if not acts2:
                continue
            cost = _gc_dist(pos, key) + detour + len(acts2)
            if cost > turns_left:
                continue
            v2 = val if acts2 is acts else val * len(acts2) / max(1, len(acts))
            if v2 < GC_P["dispatch_min_value"]:
                continue
            sc = (1e4 if must else 0) + v2 / (cost + 0.5)
            if best is None or sc > best[0]:
                best = (sc, key, acts2, pick)
        if best is None:
            return None
        _, key, acts2, pick = best
        q = []
        if pick is not None:
            q.append((pick, ["PICKUP", "WHEAT", 2], None))
        for a in acts2:
            q.append((key, a, None))
        _GC_REPORT["gc_dispatch"] = _GC_REPORT.get("gc_dispatch", 0) + 1
        return q

    def _rematch(self, farm):
        """Hands hired after hour 0 spawn wherever the engine's occupancy rule puts them at that moment, which the
        plan could not know. Swap their queues so each route starts from the closest actual hand (cheapest total)."""
        n0 = getattr(self, "n0_hires", 10)
        hands = [tuple(p) for p in farm["hands"]]
        late = [u for u in range(n0 + 1, len(hands) + 1) if u in self.queues]
        if len(late) < 2:
            return
        def qcost(q, start):
            t = 0; p = start
            for tgt, a, v in q:
                if a[0] in ("PICKUP", "DROP"):
                    tg = p if p in _GC_ACCESS_SET else _gc_near_access(p)
                else:
                    tg = tgt
                t += abs(p[0] - tg[0]) + abs(p[1] - tg[1]) + 1
                p = tuple(tg)
            return t
        qs = [self.queues[u] for u in late]
        pos = [hands[u - 1] for u in late]
        import itertools
        best = None
        if len(late) <= 6:
            for perm in itertools.permutations(range(len(late))):
                c = sum(max(0, qcost(qs[perm[i]], pos[i]) - 22) * 100 + qcost(qs[perm[i]], pos[i]) for i in range(len(late)))
                if best is None or c < best[0]:
                    best = (c, perm)
            perm = best[1]
        else:
            perm = list(range(len(late)))
        for i, u in enumerate(late):
            self.queues[u] = qs[perm[i]]
        _GC_REPORT["gc_rematch"] = _GC_REPORT.get("gc_rematch", 0) + 1

    def _courier(self, positions, invs, tiles, shed, hour):
        """End-of-day room at execution time: project tonight's shed load (reserves + goods carried + harvests still
        queued after each unit's last queued drop); while it exceeds the shed, send the loaded units that can
        afford the detour (nearest first) to drop at the closest shed-access tile."""
        turns_left = 23 - hour + 1
        res = sum(int(v) for v in self.reserve.values())
        shed_eod = min(sum(int(v) for v in shed.values()), res)
        hn = getattr(self, "_held_now", {}) if GC_P["room_v3"] else {}
        if GC_P["room_v3"]:
            # what stays in the shed tonight: reserves plus the lots the market is holding (floors, timing)
            shed_eod = min(sum(int(v) for v in shed.values()), res + sum(min(int(n), int(hn.get(p, 0))) for p, n in shed.items()))
        info = []
        total = shed_eod
        for u, pos in enumerate(positions):
            pos = tuple(pos)
            inv = invs[u] if u < len(invs) else {}
            c = sum(int(x) for x in inv.values())
            if GC_P["room_v3"]:
                # a drop frees tonight's room only for goods that sell on arrival
                c_sell = sum(int(x) for k, x in inv.items() if not hn.get(k))
            else:
                c_sell = c
            q = self.queues.get(u) or []
            last_drop = max((i for i, it in enumerate(q) if it[1][0] == "DROP"), default=-1)
            fut = 0
            for i, (tgt, a, v) in enumerate(q):
                if i <= last_drop:
                    continue
                if a[0] == "HARVEST":
                    t = tiles[tgt[1]][tgt[0]]
                    fut += int(t.get("yield_units", 0) or 0) if isinstance(t, dict) else 0
                elif a[0] == "COLLECT_FERTILIZER":
                    fut += 1
            eod = fut + (0 if last_drop >= 0 else c)
            total += eod
            if last_drop < 0 and c_sell >= GC_P["courier_min"]:
                qc = 0; pp = pos
                for tgt, a, v in q:
                    qc += abs(pp[0] - tgt[0]) + abs(pp[1] - tgt[1]) + 1; pp = tuple(tgt)
                acc = pos if pos in _GC_ACCESS_SET else _gc_near_access(pos)
                d0 = abs(pos[0] - acc[0]) + abs(pos[1] - acc[1])
                if q:
                    nx = q[0][0]
                    detour = d0 + 1 + abs(acc[0] - nx[0]) + abs(acc[1] - nx[1]) - (abs(pos[0] - nx[0]) + abs(pos[1] - nx[1]))
                else:
                    detour = d0 + 1
                info.append((detour / float(c_sell), u, acc, c_sell, qc, detour))
        limit = 100 - GC_P["courier_margin"]
        if total <= limit:
            return
        for _sc, u, acc, c, qc, detour in sorted(info):
            if total <= limit:
                break
            if qc + detour > turns_left or detour > GC_P["courier_max_detour"]:
                continue
            q = self.queues.get(u) or []
            self.queues[u] = [(acc, ["DROP"], None)] + list(q)
            total -= c
            _GC_REPORT["gc_courier"] = _GC_REPORT.get("gc_courier", 0) + 1

    def _shed_perm(self, routes, spawns):
        """shed_perm: permute interchangeable routes (same spawn tile, same turn cap) so that the goods carried into the
        night drop are worth more on lower unit indices (the engine discards the tail of farmer, hand 1, 2, ...)."""
        val = getattr(self, "val", None) or {}
        fert = float(self.pnow.get("FERTILIZER", 0)) if getattr(self, "pnow", None) else 0.0
        eod = []
        for u, r in enumerate(routes):
            k0 = max((i for i, v in enumerate(r) if v.tag == "S"), default=-1)
            if self.drop_at.get(u) is not None:
                k0 = max(k0, self.drop_at[u])
            units = 0; value = 0.0
            for v in r[k0 + 1:]:
                c = int(v.carry or 0)
                if c <= 0:
                    continue
                g = v.gain or {}
                p = g.get("prod")
                pv = float(g.get("pv", val.get(p, 0.0))) if p else 0.0
                if v.tag == "A":
                    k = int(g.get("units", 0) or 0) if p else 0
                    value += k * pv + (c - k) * fert
                else:
                    value += c * pv
                units += c
            eod.append((units, value))
        if sum(x[0] for x in eod) < GC_P.get("shed_perm_min", 60):
            return
        groups = {}
        for u in range(len(routes)):
            groups.setdefault((tuple(spawns[u]), self._cap(u)), []).append(u)
        new = list(routes); new_da = {}; moved = 0
        for key, us in groups.items():
            order = sorted(us, key=lambda u: (-eod[u][1], u))
            for dst, src in zip(sorted(us), order):
                new[dst] = routes[src]
                if src in self.drop_at:
                    new_da[dst] = self.drop_at[src]
                moved += dst != src
        if moved:
            routes[:] = new
            self.drop_at = new_da
            _GC_REPORT["gc_shed_perm"] = _GC_REPORT.get("gc_shed_perm", 0) + 1

    def _shed_over(self, positions, invs, tiles, shed):
        """shed_skip: tonight's projected shed load minus the shed capacity. Goods carried into the night: the inventory of
        each unit with no drop left in its queue (less the wheat/fertilizer/animals the queue still uses) plus the harvests
        and fertilizer collects queued after its last drop. Kept in the shed: per product, the reserve not covered by
        those goods (from reserve_release_hour the market sells the reserve that the night's goods replace)."""
        carry = {}
        for u, pos in enumerate(positions):
            inv = invs[u] if u < len(invs) else {}
            q = self.queues.get(u) or []
            last_drop = max((i for i, it in enumerate(q) if it[1][0] == "DROP"), default=-1)
            if last_drop < 0:
                use = {}
                for _t, a, _v in q:
                    it = "WHEAT" if a[0] == "FEED" else ("FERTILIZER" if a[0] == "FERTILIZE" else (a[1] if a[0] == "PLACE" and len(a) > 1 else None))
                    if it:
                        use[it] = use.get(it, 0) + 1
                for k, x in inv.items():
                    carry[k] = carry.get(k, 0) + max(0, int(x) - use.get(k, 0))
            for i, (tgt, a, v) in enumerate(q):
                if i <= last_drop:
                    continue
                if a[0] == "HARVEST":
                    t = tiles[tgt[1]][tgt[0]]
                    if isinstance(t, dict) and int(t.get("yield_units", 0) or 0) > 0:
                        p = _GC_ANIM[t["animal"]]["prod"] if "animal" in t else t.get("crop")
                        carry[p] = carry.get(p, 0) + int(t["yield_units"])
                elif a[0] == "COLLECT_FERTILIZER":
                    carry["FERTILIZER"] = carry.get("FERTILIZER", 0) + 1
        kept = sum(min(int(shed.get(p, 0)), max(0, int(r) - carry.get(p, 0))) for p, r in self.reserve.items())
        return kept + sum(carry.values()) - 100

    def _shed_keeps(self, t, day):
        """shed_skip: True when the tile keeps its harvestable units until tomorrow without losing any (engine rules:
        animal production is capped at max_held, ongoing crops at max_yield, finished plants decay from
        max_lifespan_step, a plant unwatered two nights running becomes a weed)."""
        if not isinstance(t, dict) or int(t.get("yield_units", 0) or 0) <= 0:
            return False
        y = int(t["yield_units"]); cls = GC_P.get("shed_skip_cls", ("A", "O", "G"))
        if "animal" in t:
            a = _GC_ANIM[t["animal"]]
            if GC_P.get("d28feed_fix") and int(t.get("consecutive_unfed", 0) or 0) >= 1 and not t.get("fed_today"):
                return False   # escapes tonight: its units go with it
            k = day + 1 - int(t.get("placed_day", 0)) - a["fy"]
            add = (1 + (int(t.get("pending_care_bonus", 0) or 0) if t.get("fed_today") else 0)) if (k >= 0 and k % a["iv"] == 0) else 0
            return "A" in cls and y + add <= a["held"]
        if t.get("kind") != "PLANT" or t.get("crop") not in _GC_CROPS:
            return False
        cd = _GC_CROPS[t["crop"]]; age = day - int(t["planted_day"])
        if age < cd["fy"] or not (t.get("watered_today") or int(t.get("consecutive_unwatered", 1)) == 0):
            return False
        if cd["on"]:
            k = age + 1 - cd["fy"]
            eve = k >= 0 and k % cd["iv"] == 0 and k // cd["iv"] + 1 <= cd["mx"]
            add = (2 if (t.get("watered_today") and int(t.get("fertilized_until_day", -1)) >= day) else 1) if eve else 0
            mls = int(t.get("max_lifespan_step", -1))
            return "O" in cls and y + add <= cd["mx"] and (mls < 0 or mls >= (day + 2) * 24)
        return "G" in cls and age < cd["my"]

    def _step_unit(self, u, pos, tiles, inv, seeds, planting, sim, shed, room, hour=0):
        q = self.queues.get(u)
        if q and hour >= GC_P["trim_hour"]:
            self._trim_queue(q, pos, (24 - hour) if (GC_P.get("trim_fix") and not self.final) else (23 - hour))
        while q:
            tgt, act, _v = q[0]
            if GC_P["shed_any"] and act[0] in ("PICKUP", "DROP"):
                # any shed-access tile serves: use the one we stand on, else the nearest
                tgt = tuple(pos) if tuple(pos) in _GC_ACCESS_SET else _gc_near_access(pos)
            if tuple(pos) != tuple(tgt):
                dx = tgt[0] - pos[0]; dy = tgt[1] - pos[1]
                if dx:
                    return ["EAST"] if dx > 0 else ["WEST"]
                return ["SOUTH"] if dy > 0 else ["NORTH"]
            key = (pos[0], pos[1])
            tile = sim[key] if key in sim else tiles[pos[1]][pos[0]]
            if act[0] == "DROP" and sum(int(x) for x in inv.values()) > room[0]:
                # the shed cannot take the load yet: wait a turn for the sale that makes room
                self._drop_wait = getattr(self, "_drop_wait", 0) + sum(int(x) for x in inv.values())
                return ["PASS"]
            if (act[0] == "HARVEST" and getattr(self, "_skip_over", 0) > GC_P.get("shed_skip_margin", 0)
                    and not any(a2[0] == "DROP" or (a2[0] in ("PLANT", "DIG") and tuple(t2) == tuple(tgt)) for t2, a2, _v2 in q[1:])
                    and self._shed_keeps(tile, self.day)):
                # shed_skip: tonight's drop would discard units; this tile keeps them for tomorrow (not when the same
                # visit replants or digs the tile: the harvest frees it)
                q.pop(0)
                self._skip_over -= int(tile.get("yield_units", 0) or 0)
                _GC_REPORT["gc_shed_skip"] = _GC_REPORT.get("gc_shed_skip", 0) + 1
                _GC_REPORT["gc_shed_skip_u"] = _GC_REPORT.get("gc_shed_skip_u", 0) + int(tile.get("yield_units", 0) or 0)
                continue
            if (act[0] == "PLANT" and GC_P.get("plant23_fix") and hour >= (22 if self.final else 23)
                    and self._useful(act, tile, inv, seeds, planting, shed, room)):
                # plant23_fix: no turn left to water the new plant today (it would turn weed tonight)
                q.pop(0)
                if q and q[0][1][0] == "WATER" and tuple(q[0][0]) == tuple(tgt):
                    q.pop(0)
                _GC_REPORT["gc_plant23"] = _GC_REPORT.get("gc_plant23", 0) + 1
                continue
            if self._useful(act, tile, inv, seeds, planting, shed, room):
                q.pop(0)
                if act[0] == "PLANT":
                    planting[act[1]] = planting.get(act[1], 0) + 1
                if act[0] == "PICKUP":
                    n = int(act[2]) if len(act) >= 3 else 1
                    shed[act[1]] = max(0, shed.get(act[1], 0) - n)
                if act[0] == "DROP":
                    n = sum(int(x) for x in inv.values())
                    room[0] -= n
                    for k2, n2 in inv.items():
                        shed[k2] = shed.get(k2, 0) + int(n2)
                    if GC_P.get("drop_refill") and q:
                        self._drop_refill(q, pos, inv)
                return act
            q.pop(0)
            _GC_REPORT["gc_noops"] += 1
        return ["PASS"]

    @staticmethod
    def _drop_refill(q, pos, inv):
        """drop_refill: after a DROP, queue PICKUPs (same shed tile, next turns) of the inputs just dropped that the
        rest of the queue still uses: WHEAT per FEED, FERTILIZER per FERTILIZE, the animal per PLACE, less any PICKUP
        already queued, at most what the unit held."""
        need = {}
        for _t, a, _v in q:
            it = "WHEAT" if a[0] == "FEED" else ("FERTILIZER" if a[0] == "FERTILIZE" else (a[1] if a[0] == "PLACE" and len(a) > 1 else None))
            if it:
                need[it] = need.get(it, 0) + 1
            elif a[0] == "PICKUP" and len(a) > 1:
                need[a[1]] = need.get(a[1], 0) - (int(a[2]) if len(a) >= 3 else 1)
        for it in ("GOOSE", "SHEEP", "COW", "FERTILIZER", "WHEAT"):
            k = min(need.get(it, 0), int(inv.get(it, 0)))
            if k > 0:
                q.insert(0, (tuple(pos), ["PICKUP", it, k], None))
                _GC_REPORT["gc_refill"] = _GC_REPORT.get("gc_refill", 0) + k

    def act(self, obs):
        hour = int(obs["hour"]); day = int(obs["day"])
        if GC_P["sell_timing"]:
            try:
                self._mk_track(obs)
            except Exception:
                _GC_REPORT["gc_mk_errors"] = _GC_REPORT.get("gc_mk_errors", 0) + 1
        me = self.me
        farm = obs["farms"][me]
        priv = obs["private"]
        if self.day_plan != day:
            self.plan_day(obs)
            self.day_plan = day
            self.queues = {u: q for u, q in enumerate(self._compile(self.routes, self.spawns))}
        tiles = farm["tiles"]
        self._tiles_now = tiles
        self._drop_wait = 0
        if GC_P["rematch"] and hour == 2 and not getattr(self, "_rematched", None) == day:
            self._rematched = day
            self._rematch(farm)
        self._mid_orders = []
        if self._open_on(day) and hour in self.open["replan_hours"]:
            try:
                self._mid_orders = self._open_midday(obs, hour)
            except Exception as e:
                _GC_REPORT["gc_open_mid_err"] = repr(e)[:160]
        seeds = dict(priv["seeds"])
        shed = {k: int(v) for k, v in dict(priv["shed"]).items()}
        room = [100 - sum(shed.values())]
        invs = list(priv["inventories"])
        planting = {}
        sim = {}
        positions = [farm["farmer"]] + list(farm["hands"])
        if GC_P["courier"] and hour >= GC_P["courier_hour"] and not self.final:
            self._courier(positions, invs, tiles, shed, hour)
        self._skip_over = 0
        if GC_P.get("shed_skip") and not self.final and hour >= GC_P.get("shed_skip_hour", 0) and (day < 28 or GC_P.get("shed_skip_d28", True)):
            self._skip_over = self._shed_over(positions, invs, tiles, shed)
        units = []
        claimed = {tgt for qq in self.queues.values() for tgt, _a, _v in (qq or [])}
        for u, pos in enumerate(positions):
            inv = dict(invs[u]) if u < len(invs) else {}
            if GC_P["final_flush"] and self.final and not self.queues.get(u) and sum(int(x) for x in inv.values()) > 0 and hour <= 22:
                # final day: anything carried is lost unless dropped by step 718
                self.queues[u] = [(_gc_near_access(tuple(pos)), ["DROP"], None)]
            if GC_P["dispatch"] and not self.queues.get(u) and hour >= 1 and not (self.final and hour >= 18):
                nq = self._dispatch(u, pos, inv, 23 - hour + 1, tiles, sim, seeds, shed, claimed, day, hour)
                if nq:
                    if GC_P["final_flush"] and self.final:
                        last = nq[-1][0]
                        nq = nq + [(_gc_near_access(tuple(last)), ["DROP"], None)]
                    self.queues[u] = nq
                    claimed.update(tgt for tgt, _a, _v in nq)
            a = self._step_unit(u, pos, tiles, inv, seeds, planting, sim, shed, room, hour)
            key = (pos[0], pos[1])
            if a[0] in ("WATER", "CARE", "FEED", "HARVEST", "COLLECT_FERTILIZER") and isinstance(tiles[pos[1]][pos[0]], dict):
                t2 = dict(sim[key] if key in sim else tiles[pos[1]][pos[0]])
                if a[0] == "WATER": t2["watered_today"] = True
                elif a[0] == "CARE": t2["cared_today"] = True
                elif a[0] == "FEED": t2["fed_today"] = True
                elif a[0] == "HARVEST": t2["yield_units"] = 0
                elif a[0] == "COLLECT_FERTILIZER": t2["fertilizer_available"] = False
                sim[key] = t2
            units.append(a)
        if GC_P.get("pick_fix"):
            n_exp = len(positions) + int((getattr(self, "hires_planned", 0) if hour == 0 else getattr(self, "hires_left", 0)) or 0)
            pend = {}
            for u, q in self.queues.items():
                if u >= n_exp or not q:
                    continue
                for _t, a2, _v in q:
                    if a2[0] == "PICKUP" and len(a2) > 1:
                        pend[a2[1]] = pend.get(a2[1], 0) + (int(a2[2]) if len(a2) >= 3 else 1)
            self._pend_pick = pend
        carried = 0
        self.carried_items = {}
        for u in range(len(positions)):
            if units[u][0] == "DROP":
                continue
            inv = dict(invs[u]) if u < len(invs) else {}
            carried += sum(int(x) for x in inv.values())
            for k2, n2 in inv.items():
                self.carried_items[k2] = self.carried_items.get(k2, 0) + int(n2)
        market = self._market(obs, shed, carried, hour, day)[:10]
        if GC_P["sell_timing"]:
            try:
                self._mk_store(obs, shed, market)
            except Exception:
                _GC_REPORT["gc_mk_errors"] = _GC_REPORT.get("gc_mk_errors", 0) + 1
        if hour == 23:
            left = [(u, len(q), sum(1 for _, a, _v in q if a[0] not in ("DROP",))) for u, q in self.queues.items() if q]
            _GC_REPORT["gc_unfinished_units"] = _GC_REPORT.get("gc_unfinished_units", 0) + len(left)
            _GC_REPORT["gc_unfinished_acts"] = _GC_REPORT.get("gc_unfinished_acts", 0) + sum(x[2] for x in left)
            _GC_REPORT["gc_units_seen"] = _GC_REPORT.get("gc_units_seen", 0) + len(positions)
            _GC_REPORT["gc_units_planned"] = _GC_REPORT.get("gc_units_planned", 0) + len(self.routes)
        return {"farmer": units[0], "hands": units[1:], "market": market[:10]}

    # ------------------------------------------------------------------ rival sale timing
    @staticmethod
    def _town_draw(shops, step):
        """Units the town removes after `step`'s market: each shop every 4 turns (2 for single-product shops),
        the town centre one of each product every 24 turns."""
        draw = {}
        if step % 4 == 0:
            for sh in shops:
                items = _GC_SHOPS.get(sh, [])
                for it in items:
                    draw[it] = draw.get(it, 0) + (2 if len(items) == 1 else 1)
        if step % 24 == 0:
            for it in _GC_PRODUCTS:
                if it != "FERTILIZER":
                    draw[it] = draw.get(it, 0) + 1
        return draw

    def _mk_track(self, obs):
        """Rival sales of the last turn = inventory change + town drain - our own fills (+ our buys)."""
        step = int(obs["step"])
        inv = obs["market"]["inventory"]
        prev = self._mk_prev
        if prev is None or prev["step"] != step - 1:
            return
        draw = self._town_draw(prev["shops"], step - 1)
        for p in _GC_PRODUCTS:
            if prev["px"].get(p, 0) <= 1:
                continue
            resid = int(inv[p]) - int(prev["inv"][p]) + draw.get(p, 0) - prev["sold"].get(p, 0) + prev["bought"].get(p, 0)
            if resid >= GC_P["rival_min_lot"]:
                self.rival_sales.setdefault(p, []).append(((step - 1) // 24, (step - 1) % 24, resid))

    def _mk_store(self, obs, shed, market):
        sold = {}; bought = {}
        for o in market:
            if not o or len(o) < 3:
                continue
            if o[0] == "SELL":
                sold[o[1]] = sold.get(o[1], 0) + int(o[2])
            elif o[0] == "BUY_PRODUCT":
                bought[o[1]] = bought.get(o[1], 0) + int(o[2])
        for p in list(sold):
            sold[p] = min(sold[p], max(0, int(shed.get(p, 0))))
        m = obs["market"]
        self._mk_prev = {"step": int(obs["step"]), "inv": {p: int(m["inventory"][p]) for p in _GC_PRODUCTS},
                         "px": {p: int(m["prices"][p]) for p in _GC_PRODUCTS},
                         "shops": list(_gc_get(obs["town"], "unlocked_shops", []) or []), "sold": sold, "bought": bought}

    def _floor_recovers(self, obs, p, fl, day):
        """Holding below the floor pays only if the town drains the book back above it soon: units to drain until the
        quote reaches the floor vs the town's daily draw of p times the allowed wait."""
        if not GC_P["floor_drain_aware"]:
            return True
        inv = int(obs["market"]["inventory"][p])
        k = 0
        while k < 400 and _gc_price(p, inv - k) < fl:
            k += 1
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        per_day = (0 if p == "FERTILIZER" else 1)
        for sh in shops:
            items = _GC_SHOPS.get(sh, [])
            if p in items:
                per_day += 6 * (2 if len(items) == 1 else 1)
        if GC_P["floor_rival_aware"]:
            # the rival's own supply of p over the last day offsets the town's drain
            step = int(obs["step"])
            per_day -= sum(q for d, h, q in self.rival_sales.get(p, ()) if d * 24 + h >= step - 24)
        return per_day > 0 and k <= per_day * GC_P["floor_wait_days"]

    def _rival_wait(self, p, day, hour):
        """Turns to wait so our lot of p sells one turn before the rival's next predicted sale (hours at which it
        sold p on recent days). None when the rival has no recent sales of p."""
        lo = day - GC_P["rival_days"]
        hours = sorted({h for d, h, q in self.rival_sales.get(p, ()) if d >= lo})
        if not hours:
            return None
        cur = day * 24 + hour
        cands = [day * 24 + h for h in hours if day * 24 + h >= cur + 1] + [(day + 1) * 24 + h for h in hours]
        return max(0, min(cands) - 1 - cur)

    # ------------------------------------------------------------------ market
    def _arb_buys(self, obs, shed, carried, hour, day, sells):
        """Glut arbitrage: buy units of a crashed product while the next unit's quote is <= arb_buy_max, provided
        the town's drain of that product brings the book back to the target quote well before the end."""
        if not GC_P["arb_on"] or day > GC_P["arb_last_day"] or hour < 1 or hour > 20:
            return []
        inv = obs["market"]["inventory"]
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        held = sum(int(v) for v in self.arb.values())
        total = sum(int(v) for v in shed.values()) - sum(int(o[2]) for o in sells) + (carried if hour >= 18 else 0)
        room = 100 - total - GC_P["arb_room"]
        out = []
        for p in GC_P["arb_prods"]:
            if held >= GC_P["arb_cap"] or room <= 0:
                break
            i0 = int(inv[p])
            if _gc_price(p, i0) > GC_P["arb_buy_max"]:
                continue
            drain = 1.0
            for sh in shops:
                items = _GC_SHOPS.get(sh, [])
                if p in items:
                    drain += 6.0 * (2 if len(items) == 1 else 1)
            tgt = GC_P["arb_target"].get(p, 150)
            k_t = 0
            while k_t < 600 and _gc_price(p, i0 - k_t) < tgt:
                k_t += 1
            days_left = 28 - day
            if drain <= 1.0 or k_t / drain > GC_P["arb_recover_frac"] * days_left:
                continue
            k = 0
            while (k < GC_P["arb_step_max"] and held + k < GC_P["arb_cap"] and k < room
                   and _gc_price(p, i0 - k) <= GC_P["arb_buy_max"]):
                k += 1
            if k > 0:
                out.append(["BUY_PRODUCT", p, k])
                self.arb[p] = self.arb.get(p, 0) + k
                held += k; room -= k
                _GC_REPORT["gc_arb_bought"] = _GC_REPORT.get("gc_arb_bought", 0) + k
        return out

    def _unit_cap(self, obs, p, n, before=0):
        """Units of a lot of n whose own marginal quote stays at or above the unit floor (a glutted book recovers at
        the town's next purchase; a unit sold at $1 is thrown away)."""
        fr = GC_P["unit_floor_frac"]
        if fr <= 0 or p not in GC_P["unit_floor_items"] or int(obs["step"]) >= GC_P["unit_floor_step"] or n <= 0:
            return n
        fl = fr * _GC_MKT[p][0]
        i0 = int(obs["market"]["inventory"][p]) + before
        k = 0
        while k < n and _gc_price(p, i0 + k) >= fl:
            k += 1
        if k < n:
            _GC_REPORT["gc_unit_floor"] = _GC_REPORT.get("gc_unit_floor", 0) + (n - k)
        return k

    def _market(self, obs, shed, carried, hour, day):
        orders = self._market0(obs, shed, carried, hour, day)
        if GC_P["sells_first"]:
            orders = _gc_sells_first(orders, obs["market"]["inventory"], shed, set(getattr(self, "_due", set()) or set()))
        return orders

    def _market0(self, obs, shed, carried, hour, day):
        step = int(obs["step"])
        sells = self._sell_orders(obs, shed, carried, hour, day, step)
        if GC_P["tick_defer"] and hour % 4 == 0 and hour > 0 and day < GC_P["tick_last_day"]:
            # the town buys right after the market at hours 0, 4, ..., 20: a lot sold an hour later meets the
            # restocked book and goes first in the next window
            # (lots due now to go one turn ahead of the rival's predicted sale stay: beating the rival's lot is
            # worth more than the town's restock)
            sells = [o for o in sells if o[0] != "SELL" or (GC_P["tick_keep_due"] and o[1] in self._due)]
        if GC_P["arb_on"]:
            buys = self._arb_buys(obs, shed, carried, hour, day, sells)
            if buys:
                sells = sells + buys
        prem = [o for o in sells if o[1] in _GC_PREMIUM]
        rest = [o for o in sells if o[1] not in _GC_PREMIUM]
        if self.open is not None and hour == self.open["feed_buy_hour"] and day <= 27:
            # tomorrow's feed, bought once the day's sales are in (the morning purchase would find an empty purse)
            need = self.n_animals + sum(int(shed.get(an, 0)) for an in ("COW", "SHEEP", "GOOSE"))
            have = int(shed.get("WHEAT", 0)) + int(self.carried_items.get("WHEAT", 0)) - sum(int(o[2]) for o in sells if o[0] == "SELL" and o[1] == "WHEAT")
            short = need - have
            if short > 0:
                px = _gc_price("WHEAT", obs["market"]["inventory"]["WHEAT"] - short)
                money = float(obs["farms"][self.me]["money"])
                k = min(short, int(max(0.0, money - 30.0) // max(1, px)))
                if k > 0:
                    rest = rest + [["BUY_PRODUCT", "WHEAT", k]]
                    _GC_REPORT["gc_open_feedbuy"] = _GC_REPORT.get("gc_open_feedbuy", 0) + k
        if hour == 0:
            fixed = list(self.orders0)
            due = []
            if GC_P["sell_timing"] and not (GC_P["tick_defer0"] and day < GC_P["tick_last_day"]):
                have = {o[1] for o in fixed if o and o[0] == "SELL"}
                due = [o for o in prem if o[1] not in have and o[1] in self._due]
            if GC_P["fert_h0"] and not any(o and o[0] == "SELL" and o[1] == "FERTILIZER" for o in fixed + due):
                have = int(shed.get("FERTILIZER", 0)) + sum(int(o[2]) for o in fixed if o and o[0] == "BUY_PRODUCT" and o[1] == "FERTILIZER")
                ex = have - int(getattr(self, "_fert_need_day", 0)) - int(self.reserve.get("FERTILIZER", 0))
                if ex > 0 and not any(o and o[0] == "BUY_PRODUCT" and o[1] == "FERTILIZER" for o in fixed):
                    due = due + [["SELL", "FERTILIZER", ex]]
                    _GC_REPORT["gc_fert_h0"] = _GC_REPORT.get("gc_fert_h0", 0) + ex
            room = 10 - len(fixed) - (len(due) if GC_P["sells_first_slots"] else 0)
            h0 = max(0, min(self.hires_planned, room))
            self.hires_left = self.hires_planned - h0
            if GC_P["sells_first_slots"] and due:
                _GC_REPORT["gc_due0"] = _GC_REPORT.get("gc_due0", 0) + len(due)
            orders = fixed + [["HIRE"]] * h0 + due
            return orders[:10]
        mid = list(getattr(self, "_mid_orders", []) or [])
        if mid:
            return (mid + prem + rest)[:10]
        if hour == 1:
            ps = [o for o in prem if o and o[0] == "SELL"] if GC_P["sells_first_slots1"] else []
            h1 = max(0, min(self.hires_left, 10 - len(self.orders1) - len(ps)))
            self.hires_left -= h1
            return ([["HIRE"]] * h1 + list(self.orders1) + prem + rest)[:10]
        if self.hires_left and hour == 2:
            h2 = min(self.hires_left, 10)
            self.hires_left = 0
            return ([["HIRE"]] * h2 + prem + rest)[:10]
        return prem + rest

    def _copy_plan(self, obs, p, step, last):
        """A copy rival's planned sales of p at market steps step..last: our own tape's SELL orders (the copy runs the
        same route), each moved a step early where the chassis's one-step lead applies (no tick crossed, no shop
        unlock), capped in sequence by the ripe units of p visible on its farm now. Returns {step: units} or None."""
        impl = globals().get("_IMPL"); ch = getattr(impl, "chassis", None)
        if ch is None:
            return None
        st = ch.players.get(self.me)
        if not st or st.get("route") not in ch.routes:
            return None
        tape = ch.routes[st["route"]]
        rf = obs["farms"][1 - self.me]
        ripe = 0
        for row in rf["tiles"]:
            for t in row:
                if not isinstance(t, dict):
                    continue
                if t.get("crop") == p or (t.get("animal") and _GC_ANIM.get(t["animal"], {}).get("prod") == p):
                    ripe += int(t.get("yield_units", 0) or 0)
        plan = {}
        for t in range(max(step, 1), min(last, len(tape) - 1) + 1):
            a = tape[t]
            if not isinstance(a, dict):
                continue
            q = sum(max(0, int(o[2])) for o in (a.get("market") or []) if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == p)
            if q <= 0:
                continue
            u = t - 1
            s_at = u if (u % 4 != 0 and t % 72 != 0 and u >= step) else t
            plan[s_at] = plan.get(s_at, 0) + q
        out = {}
        for s_at in sorted(plan):
            q = min(plan[s_at], ripe)
            if q <= 0:
                break
            out[s_at] = q; ripe -= q
        return out

    def _copy_plan_ok(self, obs, p, step, day):
        """Trust the tape forecast only while it explained the copy's sales over the last day."""
        key = (p, day)
        cache = getattr(self, "_cp_ok", None)
        if cache is None:
            cache = self._cp_ok = {}
        if key in cache:
            return cache[key]
        plan = self._copy_plan(obs, p, max(0, step - 24), step - 1)
        ok = False
        if plan is not None:
            seen = {(d * 24 + h) for d, h, q in self.rival_sales.get(p, ()) if d * 24 + h >= step - 24}
            hit = sum(1 for s in plan if s in seen or (s + 1) in seen or (s - 1) in seen)
            ok = len(plan) >= 2 and hit >= GC_P["mkt_dp_copy_hit"] * len(plan)
            _GC_REPORT["gc_cp_planned"] = _GC_REPORT.get("gc_cp_planned", 0) + len(plan)
            _GC_REPORT["gc_cp_hit"] = _GC_REPORT.get("gc_cp_hit", 0) + hit
        cache[key] = ok
        return ok

    def _dp_sell(self, obs, p, n, step, day, hour, shops, cap_night=None):
        """Units of p to sell this turn (None: not a decision turn, hold). A dynamic programme over the next post-tick
        turns on the exact price curve: exogenous inventory = now - town draws + the rival's forecast sales (its hourly
        pattern over the last days), our stock grows by tonight's carried units at the day boundary."""
        cap = int(GC_P["mkt_dp_cap"]); K = int(GC_P["mkt_dp_periods"])
        if n > cap + 30:
            return n - cap   # far beyond what the programme may hold: sell the excess now, plan the rest next turn
        rd = int(GC_P["mkt_dp_rival_days"])
        byh = {}
        for d, h, q in self.rival_sales.get(p, ()):
            if day - rd <= d < day or (d == day and h < hour):
                byh[h] = byh.get(h, 0.0) + q
        ndays = float(max(1, min(rd, day)))
        rival_h = {h: v / ndays for h, v in byh.items()}
        if GC_P["mkt_dp_fresh"] and not byh:
            _GC_REPORT["gc_dp_fresh"] = _GC_REPORT.get("gc_dp_fresh", 0) + n
            return n
        rv = lambda s2: rival_h.get((s2 + 1) % 24, 0.0)   # forecast rival sales at the market of step s2 + 1
        if GC_P["mkt_dp_farm"]:
            ripe = 0
            for row in obs["farms"][1 - self.me]["tiles"]:
                for t in row:
                    if isinstance(t, dict) and (t.get("crop") == p or (t.get("animal") and _GC_ANIM.get(t["animal"], {}).get("prod") == p)):
                        ripe += int(t.get("yield_units", 0) or 0)
            if ripe > 0:
                H = max(1, int(GC_P["mkt_dp_farm_h"])); per = ripe / float(H)
                farm_fc = {s2: per for s2 in range(step, step + H)}
                rv = lambda s2, _f=farm_fc, _h=rival_h: max(_h.get((s2 + 1) % 24, 0.0), _f.get(s2, 0.0))
                _GC_REPORT["gc_dp_farm"] = _GC_REPORT.get("gc_dp_farm", 0) + 1
        ad = globals().get("_AD_STATE")
        if GC_P["mkt_dp_copy_plan"] and not (isinstance(ad, dict) and ad.get("off")) and self._copy_plan_ok(obs, p, step, day):
            K0 = int(GC_P["mkt_dp_periods"])
            plan = self._copy_plan(obs, p, step, min(718, step + 4 * K0 + 4))
            if plan is not None:
                rv = lambda s2, _pl=plan: float(_pl.get(s2 + 1, 0))
                _GC_REPORT["gc_cp_used"] = _GC_REPORT.get("gc_cp_used", 0) + 1
        try:
            self._dp_rv_now[p] = float(rv(step - 1))
        except Exception:
            pass
        if step % 4 != 1 and step > 0:
            if not GC_P["mkt_dp_every"]:
                return None
            nxt = step + ((1 - step) % 4)   # the next post-tick decision
            if sum(rv(s2) for s2 in range(step, nxt)) < float(GC_P["mkt_dp_every_min"]):
                return None
            _GC_REPORT["gc_dp_ahead"] = _GC_REPORT.get("gc_dp_ahead", 0) + 1
        inv0 = int(obs["market"]["inventory"][p])
        dsteps = [step + 4 * k for k in range(K + 1) if step + 4 * k <= 718]
        carried = int(getattr(self, "carried_items", {}).get(p, 0))
        exo = []; stock = []; rq = []; I = float(inv0); cum = n
        for k, t in enumerate(dsteps):
            if k > 0:
                for s2 in range(dsteps[k - 1], t):
                    I -= self._town_draw(shops, s2).get(p, 0)
                    I += rv(s2)
                if (dsteps[k - 1] // 24) < (t // 24):
                    cum += carried
            exo.append(I); stock.append(cum)
            # the rival's forecast sales in the period after this decision (priced at the book our decision leaves)
            rq.append(int(round(sum(rv(s2) for s2 in range(t, min(t + 4, 719))))))
        U = stock[-1]
        # the decision before the day boundary may hold only what the shed takes tonight
        caps = [cap] * len(dsteps)
        if cap_night is not None:
            for k in range(len(dsteps) - 1):
                if (dsteps[k] // 24) < (dsteps[k + 1] // 24):
                    caps[k] = max(0, min(cap, int(cap_night)))
        rmax = max(rq) if rq else 0
        imin = int(min(exo)) - 2; imax = int(max(exo)) + U + rmax + 2
        pr = [0.0]
        for i in range(imin, imax + 1):
            pr.append(pr[-1] + _gc_price(p, i))
        w = float(GC_P["mkt_dp_rival_w"])
        if (GC_P["mkt_dp_w_behind"] is not None or GC_P["mkt_dp_w_ahead"] is not None) and day >= int(GC_P["mkt_dp_w_day"]):
            try:
                gap = float(obs["farms"][1 - self.me]["money"]) - float(obs["farms"][self.me]["money"])
            except Exception:
                gap = 0.0
            if GC_P["mkt_dp_w_behind"] is not None and gap > float(GC_P["mkt_dp_w_gap"]):
                w = float(GC_P["mkt_dp_w_behind"]); _GC_REPORT["gc_dp_wb"] = _GC_REPORT.get("gc_dp_wb", 0) + 1
            elif GC_P["mkt_dp_w_ahead"] is not None and -gap > float(GC_P["mkt_dp_w_gap_ahead"]):
                w = float(GC_P["mkt_dp_w_ahead"]); _GC_REPORT["gc_dp_wa"] = _GC_REPORT.get("gc_dp_wa", 0) + 1
        NEG = -1e18; Kd = len(dsteps)
        V = [0.0] * (U + 1); best0 = 0
        for k in range(Kd - 1, -1, -1):
            Vn = [NEG] * (U + 1); base = int(exo[k]) - imin; r = rq[k]
            for c in range(min(stock[k], U) + 1):
                avail = stock[k] - c
                best = NEG; bx = 0
                lo_x = avail if k == Kd - 1 else max(0, avail - caps[k])
                for x in range(lo_x, avail + 1):
                    a = base + c
                    v = pr[a + x] - pr[a] + V[c + x]
                    if w and r:
                        v -= w * (pr[a + x + r] - pr[a + x])
                    if v > best:
                        best = v; bx = x
                Vn[c] = best
                if k == 0 and c == 0:
                    best0 = bx
            V = Vn
        return int(best0)

    def _dp_room(self, obs, shed, carried):
        """Shed room the market programme may fill with held lots tonight: mkt_dp_room minus what else lands in the
        shed unsold by the end of the day: reserves kept, and per unit the goods it still carries after its last
        queued drop (its load now when no drop is queued, plus harvests and collections queued after that drop)."""
        tiles = obs["farms"][self.me]["tiles"]
        invs = list(obs["private"].get("inventories", []) or [])
        eod = 0
        for u, q in self.queues.items():
            q = q or []
            last_drop = max((i for i, it in enumerate(q) if it[1][0] == "DROP"), default=-1)
            if last_drop < 0 and u < len(invs):
                eod += sum(int(x) for x in dict(invs[u]).values())
            for i, (tgt, a, _v) in enumerate(q):
                if i <= last_drop:
                    continue
                if a[0] == "HARVEST":
                    t = tiles[tgt[1]][tgt[0]]
                    eod += int(t.get("yield_units", 0) or 0) if isinstance(t, dict) else 0
                elif a[0] == "COLLECT_FERTILIZER":
                    eod += 1
        for u in range(len(invs)):
            if u not in self.queues:
                eod += sum(int(x) for x in dict(invs[u]).values())
        kept = sum(min(int(shed.get(p, 0)), int(self.reserve.get(p, 0))) for p in _GC_PRODUCTS if p not in GC_P["mkt_dp_prods"])
        kept += sum(int(self.arb.get(p, 0)) for p in _GC_PRODUCTS) if (GC_P["arb_on"] or GC_P["arb_chassis"]) else 0
        return int(GC_P["mkt_dp_room"]) - kept - eod

    def _sell_orders(self, obs, shed, carried, hour, day, step):
        inv = obs["market"]["inventory"]
        out = []
        reserve = self.reserve
        last = step >= 716 or day >= 29
        ci = getattr(self, "carried_items", {})
        total_shed = sum(int(v) for v in shed.values())
        pressure = total_shed + carried > GC_P["drip_room"]
        held = {}
        dp_budget = None
        if GC_P["mkt_dp"] and GC_P["mkt_dp_room"] > 0 and not last:
            try:
                dp_budget = self._dp_room(obs, shed, carried)
            except Exception as e:
                dp_budget = None; _GC_REPORT["gc_mkt_dp_err"] = repr(e)[:120]
            if dp_budget is not None:
                _GC_REPORT["gc_dp_room_min"] = min(_GC_REPORT.get("gc_dp_room_min", 999), dp_budget)
        self._due = set()
        self._dp_rv_now = {}
        val_now = {q: _gc_price(q, inv[q]) for q in _GC_PRODUCTS}
        urgent = self.open is not None and self._open_on(day) and bool(getattr(self, "_open_urgent", False))
        pend = {}
        if GC_P.get("market_fix1") and not last:
            # inputs still to be picked up today (hands hired at hours 1-2, second PICKUPs, refills, dispatches)
            for _u, _q in (self.queues or {}).items():
                for _t, _a, _v in (_q or []):
                    if _a[0] == "PICKUP" and len(_a) > 1 and _a[1] in ("WHEAT", "FERTILIZER"):
                        pend[_a[1]] = pend.get(_a[1], 0) + (int(_a[2]) if len(_a) >= 3 else 1)
        for p in _GC_PRODUCTS:
            n = int(shed.get(p, 0))
            a = int(self.arb.get(p, 0)) if (GC_P["arb_on"] or GC_P["arb_chassis"]) else 0
            if a > 0:
                a = min(a, n)
                if last or val_now.get(p, 0) >= GC_P["arb_target"].get(p, 150):
                    # the bought lot is released at its target (or at the end): stop tracking it
                    self.arb[p] = 0
                    _GC_REPORT["gc_arb_sold"] = _GC_REPORT.get("gc_arb_sold", 0) + a
                else:
                    n -= a
            if not last:
                keep = int(reserve.get(p, 0))
                if hour >= GC_P["reserve_release_hour"]:
                    # what units carry now lands in the shed tonight and covers tomorrow's needs
                    keep = max(0, keep - int(ci.get(p, 0)))
                if pend.get(p, 0) > keep:
                    _GC_REPORT["gc_mfix1"] = _GC_REPORT.get("gc_mfix1", 0) + 1
                    keep = pend[p]
                n -= keep
            if n <= 0:
                continue
            lot = GC_P["drip"].get(p) if GC_P["drip_on"] else None
            if lot and not last and not pressure and day < 29:
                n = min(n, lot)
            if urgent:
                # the opening's scheduled purchases wait for this cash: no holds
                _GC_REPORT["gc_open_urgent_sold"] = _GC_REPORT.get("gc_open_urgent_sold", 0) + n
                out.append(["SELL", p, n])
                continue
            d29 = GC_P["mkt_dp_d29"] and day == 29 and step < 716
            if GC_P["mkt_dp"] and (p in GC_P["mkt_dp_prods"] or (d29 and p in GC_P["mkt_dp_d29_prods"])) and day >= GC_P["mkt_dp_from_day"] and (
                    (not last and day <= 28) or d29):
                try:
                    x = self._dp_sell(obs, p, n, step, day, hour, list(_gc_get(obs["town"], "unlocked_shops", []) or []),
                                      cap_night=(None if dp_budget is None else max(0, dp_budget)))
                except Exception as e:
                    x = n; _GC_REPORT["gc_mkt_dp_err"] = repr(e)[:120]
                if GC_P["sells_first_dp_due"] and self._dp_rv_now.get(p, 0.0) >= 1.0:
                    self._due.add(p)
                if x is None:
                    held[p] = held.get(p, 0) + n; _GC_REPORT["gc_dp_wait"] = _GC_REPORT.get("gc_dp_wait", 0) + n
                    continue
                if x < n:
                    held[p] = held.get(p, 0) + (n - x); _GC_REPORT["gc_dp_held"] = _GC_REPORT.get("gc_dp_held", 0) + (n - x)
                    if dp_budget is not None:
                        dp_budget -= (n - x)
                    n = x
                if n <= 0:
                    continue
                _GC_REPORT["gc_dp_sold"] = _GC_REPORT.get("gc_dp_sold", 0) + n
                out.append(["SELL", p, n])
                continue
            fl = GC_P["sell_floor"].get(p) if GC_P["sell_floor"] else None
            if fl and not last and day <= GC_P["floor_last_day"] and val_now.get(p, 0) < fl and self._floor_recovers(obs, p, fl, day):
                held[p] = n
                _GC_REPORT["gc_floor_held"] = _GC_REPORT.get("gc_floor_held", 0) + n
                continue
            if fl and GC_P["floor_marginal"] and not last and day <= GC_P["floor_last_day"] and self._floor_recovers(obs, p, fl, day):
                # sell only the units whose own marginal quote stays at or above the floor (convex gluts
                # absorb a handful of units before collapsing to $1)
                k = 0; i0 = int(inv[p])
                while k < n and _gc_price(p, i0 + k) >= fl:
                    k += 1
                if k < n:
                    held[p] = n - k
                    _GC_REPORT["gc_floor_marg"] = _GC_REPORT.get("gc_floor_marg", 0) + (n - k)
                    n = k
                    if n <= 0:
                        continue
            if GC_P["lot_frac"] > 0 and p in GC_P["timed"] and not last and n > 1:
                # never crash our own book: stop the lot where the next unit would sell below lot_frac of the quote
                i0 = int(inv[p]); p0 = _gc_price(p, i0); k = 0
                while k < n and _gc_price(p, i0 + k) >= GC_P["lot_frac"] * p0:
                    k += 1
                k = max(1, k)
                if k < n:
                    held[p] = held.get(p, 0) + (n - k)
                    _GC_REPORT["gc_lot_cut"] = _GC_REPORT.get("gc_lot_cut", 0) + (n - k)
                    n = k
            if GC_P["sell_timing"] and p in GC_P["timed"] and not last and day >= GC_P["timing_from_day"]:
                w = self._rival_wait(p, day, hour)
                if w is not None and 0 < w <= GC_P["hold_max"]:
                    held[p] = held.get(p, 0) + n
                    _GC_REPORT["gc_held"] = _GC_REPORT.get("gc_held", 0) + n
                    continue
                if w == 0:
                    self._due.add(p)
            if GC_P["unit_floor_frac"] > 0:
                k = self._unit_cap(obs, p, n)
                if k < n:
                    held[p] = held.get(p, 0) + (n - k)
                    n = k
                    if n <= 0:
                        continue
            out.append(["SELL", p, n])
        # shed room: the end-of-day drop (and any drop) must fit; release held lots first when it would not
        if held:
            total = sum(int(v) for v in shed.values()) - sum(int(o[2]) for o in out)
            # pick_fix: the stock queued pickups take next turn needs no room for the held lots
            pend_ = sum(min(int(shed.get(p_, 0)), int(x)) for p_, x in getattr(self, "_pend_pick", {}).items()) if GC_P.get("pick_fix") else 0
            over = max(total - pend_ + (carried if hour >= 20 else 0) - (100 if hour >= 20 else GC_P["hold_room"]),
                       total + getattr(self, "_drop_wait", 0) - 100)
            if GC_P["room_v3"] and over > 0:
                # unit by unit, release where the marginal quote gives up least against the product's floor
                # (spreads the dump over several books instead of crashing one)
                rel = {}
                for _k in range(min(over, sum(held.values()))):
                    best = None
                    for p, hq in held.items():
                        if rel.get(p, 0) >= hq:
                            continue
                        sold_p = sum(int(o[2]) for o in out if o[1] == p) + rel.get(p, 0)
                        px = _gc_price(p, int(inv[p]) + sold_p)
                        fv = (GC_P["sell_floor"] or {}).get(p) or val_now.get(p, 0)
                        sc = px - fv
                        if best is None or sc > best[0]:
                            best = (sc, p)
                    if best is None:
                        break
                    rel[best[1]] = rel.get(best[1], 0) + 1
                for p, k in rel.items():
                    out.append(["SELL", p, k]); held[p] -= k
                    _GC_REPORT["gc_held_released"] = _GC_REPORT.get("gc_held_released", 0) + k
                over = 0
            # release what sells closest to its normal price first (never dump a crashed book to make room first)
            for p in sorted(held, key=lambda q: -val_now.get(q, 0) / float(_GC_MKT[q][0])):
                if over <= 0:
                    break
                k = min(over, held[p])
                out.append(["SELL", p, k]); over -= k
                held[p] -= k
                _GC_REPORT["gc_held_released"] = _GC_REPORT.get("gc_held_released", 0) + k
        self._held_now = {p: q for p, q in held.items() if q > 0}
        # end-of-day room for carried goods: sell reserves too if the auto-drop would overflow
        if hour == 23 and not last:
            total = sum(int(v) for v in shed.values()) - sum(int(o[2]) for o in out)
            over = total + carried - 100
            if over > 0:
                _GC_REPORT["gc_room_sells"] += over
                for p in ("FERTILIZER", "WHEAT"):
                    k = min(over, int(shed.get(p, 0)) - sum(int(o[2]) for o in out if o[1] == p))
                    if k > 0:
                        out.append(["SELL", p, k]); over -= k
        return out


_GC = GoldCtl()


def _gc_router_wrap(router0):
    def _gc_router(observation, step, state):
        r = router0(observation, step, state)
        try:
            if GC_P["div_route"] is not None and step >= 144 and not state.get("gc_div_route"):
                state["gc_div_route"] = True   # decided once, at the day-6 route pick
                ad = globals().get("_AD_STATE")
                if step <= 150 and isinstance(ad, dict) and ad.get("off"):
                    state["route"] = int(GC_P["div_route"]); r = state["route"]
                    _GC_REPORT["gc_div_route"] = r
        except Exception as e:
            _GC_REPORT["gc_div_route_err"] = repr(e)[:120]
        return r
    return _gc_router


try:
    _IMPL.chassis.router = _gc_router_wrap(_IMPL.chassis.router)
except Exception:
    pass
_GC_DIV_SAVED = {}
_GC_RICH = {}
# ---------------------------------------------------------------------------------------------------------------
# Chassis-phase glut arbitrage (arb_chassis): while the chassis plays, buy a crashed product the town will drain back
# (wool at $1 after the early sheep glut, milk, strawberry), keep the chassis from selling the bought units, and let
# them go once the quote is back at the target. The controller inherits the position at takeover (GoldCtl.arb).
_ARB_STATE = {}


def _arb_chassis(obs, action):
    step = int(obs["step"]); day = step // 24; hour = step % 24
    me = int(obs["player"])
    st = _ARB_STATE.get(me)
    if st is None or step <= st.get("step", -1):
        st = _ARB_STATE[me] = {"held": {}, "step": -1}
    st["step"] = step
    inv = obs["market"]["inventory"]
    shed = {k: int(v) for k, v in dict(obs["private"]["shed"]).items()}
    market = [list(o) for o in (action.get("market") or [])]
    held = st["held"]
    # release lots whose quote is back at the target; protect the rest from the chassis's own sell orders
    for p in list(held):
        if held[p] <= 0 or _gc_price(p, int(inv[p])) >= GC_P["arb_target"].get(p, 150) or step >= 700:
            _GC_REPORT["gc_arbc_released"] = _GC_REPORT.get("gc_arbc_released", 0) + held.pop(p)
    for p, h in held.items():
        free = max(0, shed.get(p, 0) - h)
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] == p:
                q = min(int(o[2]), free)
                free -= q
                o[2] = q
        market = [o for o in market if not (o and o[0] == "SELL" and len(o) >= 3 and int(o[2]) <= 0)]
    # buy
    if GC_P["arb_first"] <= day <= GC_P["arb_last_day"] and 1 <= hour <= 20 and len(market) < 10:
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        carried = sum(int(n) for inv_u in obs["private"]["inventories"] for n in inv_u.values())
        total = sum(shed.values()) + carried
        room = 100 - total - GC_P["arb_room_chassis"]
        tot_held = sum(held.values())
        for p in GC_P["arb_prods"]:
            if room <= 0 or tot_held >= GC_P["arb_cap"] or len(market) >= 10:
                break
            i0 = int(inv[p])
            if _gc_price(p, i0) > GC_P["arb_buy_max"]:
                continue
            drain = 1.0
            for sh in shops:
                items = _GC_SHOPS.get(sh, [])
                if p in items:
                    drain += 6.0 * (2 if len(items) == 1 else 1)
            tgt = GC_P["arb_target"].get(p, 150)
            k_t = 0
            while k_t < 600 and _gc_price(p, i0 - k_t) < tgt:
                k_t += 1
            if drain <= 1.0 or k_t / drain > GC_P["arb_recover_frac"] * (28 - day):
                continue
            k = 0
            while (k < GC_P["arb_step_max"] and tot_held + k < GC_P["arb_cap"] and k < room
                   and _gc_price(p, i0 - k) <= GC_P["arb_buy_max"]):
                k += 1
            if k > 0:
                market.append(["BUY_PRODUCT", p, k])
                held[p] = held.get(p, 0) + k
                tot_held += k; room -= k
                _GC_REPORT["gc_arbc_bought"] = _GC_REPORT.get("gc_arbc_bought", 0) + k
    action = dict(action); action["market"] = market
    return action


# ---------------------------------------------------------------------------------------------------------------
# SANX: strawberry annex while the chassis plays. In a strawberry-rich town (same trigger as the controller's rich
# rule) buy the SE quadrant at day 12, hire dedicated workers after the tape's own hires (the V219 protocol) and let
# them plant, water, fertilize and harvest SE strawberries; the chassis keeps the rest of the farm. The controller
# inherits the plants at its usual takeover.
_SANX = {}
_SANX_TILES = sorted([(x, y) for y in range(5, 10) for x in range(5, 10)], key=lambda p: (abs(p[0] - 4.5) + abs(p[1] - 4.5), p[1], p[0]))


def _sanx_walk(pos, tgt):
    x, y = pos; tx, ty = tgt
    if x != tx:
        return ["EAST" if x < tx else "WEST"]
    if y != ty:
        return ["SOUTH" if y < ty else "NORTH"]
    return None


def _sanx_count(obs, day):
    shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
    _GC._values(obs)
    fert = _GC.pnow.get("FERTILIZER", 50)
    cost = 100 + 3 * fert + GC_P["straw_labor"]
    base = _GC._straw_value(obs, day, 0, shops)
    best_n, best_v = 0, 0.0
    for n in range(2, 26):
        v = _GC._straw_value(obs, day, n, shops) - base - n * cost
        if v > best_v:
            best_n, best_v = n, v
    return best_n, best_v


def _sanx_worker(obs, st, actor, role):
    step = int(obs["step"]); day = step // 24
    farm = obs["farms"][int(obs["player"])]
    pos = tuple(farm["hands"][actor - 1]) if actor >= 1 else tuple(farm["farmer"])
    inv = obs["private"]["inventories"][actor] if actor < len(obs["private"]["inventories"]) else {}
    seeds = int(obs["private"]["seeds"].get("STRAWBERRY", 0))
    home = min(((4, 4), (5, 4), (4, 5), (5, 5)), key=lambda p: abs(pos[0] - p[0]) + abs(pos[1] - p[1]))
    if not role.get("loaded"):
        role["loaded"] = True
        want = len(role["targets"])
        have = int(obs["private"]["shed"].get("FERTILIZER", 0))
        if GC_P["sanx_fert"] and have > 0 and int(inv.get("FERTILIZER", 0)) < want:
            role["pick"] = min(want, have)
    if role.get("pick"):
        w = _sanx_walk(pos, home)
        if w:
            return w
        q = role.pop("pick")
        return ["PICKUP", "FERTILIZER", q]
    todo = []
    for t in role["targets"]:
        x, y = t
        tile = farm["tiles"][y][x]
        cmd = None
        if tile is None:
            if seeds > 0 and day <= GC_P["sanx_plant_last"]:
                cmd = ["PLANT", "STRAWBERRY"]
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            if day <= GC_P["sanx_plant_last"]:
                cmd = ["DIG"]
        elif isinstance(tile, dict) and tile.get("crop") == "STRAWBERRY":
            if not tile.get("watered_today"):
                cmd = ["WATER"]
            elif int(tile.get("fertilized_until_day", -1)) < day and int(inv.get("FERTILIZER", 0)) > 0:
                cmd = ["FERTILIZE"]
            elif int(tile.get("yield_units", 0) or 0) > 0:
                cmd = ["HARVEST"]
        if cmd:
            todo.append((t, cmd))
    carrying = int(inv.get("STRAWBERRY", 0))
    hour = step % 24
    dist_home = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
    if carrying and (not todo or hour + dist_home >= 22):
        w = _sanx_walk(pos, home)
        if w:
            return w
        st["drops"] = st.get("drops", 0) + carrying
        return ["DROP"]
    if todo:
        t, cmd = min(todo, key=lambda v: (abs(pos[0] - v[0][0]) + abs(pos[1] - v[0][1]), role["targets"].index(v[0])))
        return _sanx_walk(pos, t) or cmd
    return ["PASS"]


def _sanx(obs, action):
    step = int(obs["step"]); day = step // 24; hour = step % 24
    me = int(obs["player"])
    st = _SANX.get(me)
    if st is None or step <= st.get("step", -1):
        st = _SANX[me] = {"step": -1, "committed": False, "workers": {}, "pending": None, "req_day": -1, "day": -1}
        _SANX_MASK["on"] = False
    st["step"] = step
    farm = obs["farms"][me]
    if step == GC_P["sanx_step"] and not st["committed"] and not st.get("checked"):
        st["checked"] = True
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])[:4]
        k = sum(1 for s in shops if s in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
        quads = set(farm["unlocked_quadrants"])
        if k >= GC_P["rich_min"] and "SE" not in quads and {"NE", "SW"} <= quads:
            _GC.me = me
            ev = _GC.rich_eval(obs)
            _GC_REPORT["gc_sanx_eval"] = int(ev) if ev > -1e8 else None
            if ev > GC_P["se_straw_margin"]:
                n, v = _sanx_count(obs, day)
                if n >= 4:
                    st.update(committed=True, n=n, targets=_SANX_TILES[:n], bought=False)
                    _SANX_MASK["on"] = True
                    _GC_REPORT["gc_sanx_n"] = n
    if not st["committed"]:
        return action
    if st["day"] != day:
        st["day"] = day; st["workers"] = {}
    native = _IMPL.chassis.players.get(me)
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    tape = _IMPL.chassis.routes[native["route"]]
    planned = tape[day * 24:min((day + 1) * 24, len(tape))]
    market = [list(o) for o in (action.get("market") or [])]
    # confirm yesterday's (this morning's) hire request
    pend = st.get("pending")
    if pend and step == pend["step"] + 1:
        st["pending"] = None
        if len(farm["hands"]) + 1 >= pend["first"] + pend["count"] and "SE" in farm["unlocked_quadrants"]:
            groups = [st["targets"][i::pend["count"]] for i in range(pend["count"])]
            for i in range(pend["count"]):
                st["workers"][pend["first"] + i] = {"targets": sorted(groups[i], key=lambda p: (p[1], p[0]))}
            _GC_REPORT["gc_sanx_workers"] = _GC_REPORT.get("gc_sanx_workers", 0) + pend["count"]
        else:
            _GC_REPORT["gc_sanx_short"] = _GC_REPORT.get("gc_sanx_short", 0) + 1
    # request today's workers once the tape's own hires are done
    if st["req_day"] != day and hour <= 6:
        latest = max((i for i, a in enumerate(planned) if any(o and o[0] == "HIRE" for o in a.get("market", []))), default=-1)
        remaining = planned[hour + 1:]
        more = any(o and o[0] == "HIRE" for a in remaining for o in a.get("market", []))
        parent_hires = sum(1 for o in market if o and o[0] == "HIRE")
        expected = max((len(a.get("hands", [])) for a in planned), default=0)
        if not more and len(farm["hands"]) + parent_hires == expected and hour >= max(0, latest):
            alive = sum(1 for (x, y) in st["targets"] if isinstance(farm["tiles"][y][x], dict) and farm["tiles"][y][x].get("crop") == "STRAWBERRY")
            need = alive if st.get("bought") else st["n"]
            count = min(GC_P["sanx_max_workers"], max(1, -(-need // GC_P["sanx_per_worker"])))
            extra = []
            if not st.get("bought"):
                extra += [["BUY_LAND"], ["BUY_SEED", "STRAWBERRY", st["n"]]]
            extra += [["HIRE"]] * count
            wage = sum(_gc_fib(k) for k in range(int(farm.get("hires_today", 0)) + parent_hires, int(farm.get("hires_today", 0)) + parent_hires + count))
            budget = wage + (4000 + 100 * st["n"] if not st.get("bought") else 0)
            if len(market) + len(extra) <= 10 and float(farm["money"]) >= budget + GC_P["sanx_reserve"] and (need > 0):
                market += extra
                st["bought"] = True
                st["req_day"] = day
                st["pending"] = {"step": step, "first": expected + 1, "count": count}
            elif hour >= 6:
                st["req_day"] = day
    # drive the workers
    if st["workers"]:
        commands = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        commands += [["PASS"] for _ in range(len(farm["hands"]) + 1 - len(commands))]
        for actor, role in st["workers"].items():
            if actor >= len(commands):
                continue
            commands[actor] = _sanx_worker(obs, st, actor, role)
        action = dict(action); action["farmer"], action["hands"] = commands[0], commands[1:]
    # sell what the workers delivered
    d = st.pop("drops", 0)
    st["to_sell"] = st.get("to_sell", 0) + d
    if st.get("to_sell", 0) > 0 and len(market) < 10:
        market.append(["SELL", "STRAWBERRY", st["to_sell"]])
        st["to_sell"] = 0
    action = dict(action); action["market"] = market
    return action


_SANX_MASK = {"on": False}
_AD_SIG_ORIG = globals().get("_ad_sig")


def _ad_sig(farm):
    """ADAPT's farm signature with the SE quadrant masked while our strawberry annex runs (the annex must not read
    as a divergent rival)."""
    out = _AD_SIG_ORIG(farm)
    if _SANX_MASK["on"] and GC_P["sanx_mask_adapt"] and len(out) == 100:
        out = list(out)
        for y in range(5, 10):
            for x in range(5, 10):
                out[y * 10 + x] = "#"
    return out


_SANX_PARENT = agent


def agent(observation, configuration=None):
    action = _SANX_PARENT(observation, configuration)
    if GC_P["sanx_on"]:
        try:
            action = _sanx(observation, action)
        except Exception as e:
            _GC_REPORT["gc_sanx_errors"] = _GC_REPORT.get("gc_sanx_errors", 0) + 1
            _GC_REPORT["gc_sanx_last_error"] = repr(e)[:160]
    return action


_ARB_PARENT = agent


def agent(observation, configuration=None):
    action = _ARB_PARENT(observation, configuration)
    if GC_P["arb_chassis"]:
        try:
            action = _arb_chassis(observation, action)
        except Exception as e:
            _GC_REPORT["gc_arbc_errors"] = _GC_REPORT.get("gc_arbc_errors", 0) + 1
            _GC_REPORT["gc_arbc_last_error"] = repr(e)[:160]
    return action


_GC_PARENT = agent


_STRAW_CAP_STATE = {}


def _straw_cap(obs, action):
    """Chassis days: skip strawberry plantings beyond a demand-keyed cap (lockstep-safe: PASS keeps the unit's position)."""
    if not isinstance(action, dict):
        return action
    me = int(obs["player"]); step = int(obs["step"])
    st = _STRAW_CAP_STATE.setdefault(me, {"skipped": 0, "seeds_dropped": 0, "step": -1})
    if step == 0:
        st.update(skipped=0, seeds_dropped=0)
    shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
    if step < 24 * int(GC_P["straw_cap"].get("from_day", 6)):
        return action   # too few shops known to judge the strawberry market
    if GC_P["straw_cap"].get("div_only"):
        ad = globals().get("_AD_STATE")
        if not (isinstance(ad, dict) and ad.get("off")):
            return action   # a copy rival floods the strawberry market anyway; our flood then mostly denies it
    dem = sum(6 for s in shops if s in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
    cap = GC_P["straw_cap"].get(str(dem))
    if cap is None:
        return action   # no cap at this demand
    farm = obs["farms"][me]
    n = 0
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                n += 1
    units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    planting = sum(1 for u in units if isinstance(u, list) and len(u) >= 2 and u[0] == "PLANT" and u[1] == "STRAWBERRY")
    room = max(0, cap - n)
    changed = False
    if planting > room:
        keep = room
        for i, u in enumerate(units):
            if isinstance(u, list) and len(u) >= 2 and u[0] == "PLANT" and u[1] == "STRAWBERRY":
                if keep > 0:
                    keep -= 1
                else:
                    units[i] = ["PASS"]; st["skipped"] += 1; changed = True
    market = list(action.get("market") or [])
    if n + planting >= cap:
        m2 = [o for o in market if not (isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY")]
        if len(m2) != len(market):
            st["seeds_dropped"] += sum(int(o[2]) for o in market if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY")
            market = m2; changed = True
    if changed:
        _GC_REPORT["gc_straw_cap_skipped"] = st["skipped"]; _GC_REPORT["gc_straw_cap_seeds"] = st["seeds_dropped"]; _GC_REPORT["gc_straw_cap"] = cap
        return {"farmer": units[0], "hands": units[1:], "market": market}
    return action


def _fert_idle(obs, action):
    """Chassis days: idle units standing on an animal tile with fertilizer available collect it instead of PASSing.
    The unit does not move, so the scripted route stays in lockstep; the carried fertilizer drops into the shed at
    the end of the day (or is used by a scripted FERTILIZE)."""
    if not isinstance(action, dict):
        return action
    me = int(obs["player"])
    farm = obs["farms"][me]
    priv = obs["private"]
    shed = priv.get("shed") or {}
    load = sum(int(v) for v in shed.values()) + sum(int(n) for inv in (priv.get("inventories") or []) for n in inv.values())
    if load >= GC_P["fert_idle_room"]:
        return action
    tiles = farm["tiles"]
    positions = [farm["farmer"]] + list(farm.get("hands") or [])
    units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    changed = 0
    for i, pos in enumerate(positions):
        if i >= len(units):
            break
        a = units[i]
        if not (isinstance(a, list) and a and a[0] == "PASS"):
            continue
        x, y = int(pos[0]), int(pos[1])
        t = tiles[y][x] if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]) else None
        if isinstance(t, dict) and t.get("animal") and t.get("fertilizer_available"):
            units[i] = ["COLLECT_FERTILIZER"]; changed += 1
            load += 1
            if load >= GC_P["fert_idle_room"]:
                break
    if changed:
        _GC_REPORT["gc_fert_idle"] = _GC_REPORT.get("gc_fert_idle", 0) + changed
        return {"farmer": units[0], "hands": units[1:], "market": action.get("market") or []}
    return action


def _v219x_size(obs):
    """Plants for the chassis's day-18 SE tomato block: our share of the proceeds of every tomato arriving on days
    26-29 (2 a plant a day when fertilized, sold on arrival, lockstep with the rival's) against the town's drain
    (tomato shops now and expected), net of seeds, fertilizer and the extra hands."""
    me = int(obs["player"])
    inv0 = float(obs["market"]["inventory"]["TOMATO"])
    shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
    k_now = sum(1 for sh in shops if sh in ("PIZZA_SHOP", "FARMERS_MARKET"))
    n_shops = len(shops)
    u = GC_P["v219x_units"]
    rsup = {}
    n_opp = 0
    for row in obs["farms"][1 - me]["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("crop") == "TOMATO":
                n_opp += 1
                pd = int(t["planted_day"])
                for a in range(8, 12):
                    if 18 <= pd + a <= 29:
                        rsup[pd + a] = rsup.get(pd + a, 0.0) + u * GC_P["v219x_opp_w"]
    if n_opp == 0 and GC_P["v219x_copy_n"] > 0:
        for d in range(26, 30):
            rsup[d] = rsup.get(d, 0.0) + u * GC_P["v219x_copy_n"]
    fert = float(obs["market"]["prices"]["FERTILIZER"])
    vals = {}
    P = int(obs["step"]) // 24
    for n in GC_P["v219x_sizes"]:
        inv = inv0; rev = 0.0
        for d in range(P, 30):
            unl = min(8, d // 3) - n_shops
            inv -= 6.0 * (k_now + max(0, unl) * 0.25 * GC_P["future_shop_w"]) + 1.0
            q_us = u * n if P + 8 <= d <= min(29, P + 11) else 0.0
            q_r = rsup.get(d, 0.0)
            tot = q_us + q_r
            if tot <= 0:
                continue
            if q_us > 0:
                sm = sum(_gc_price("TOMATO", inv + i) for i in range(int(round(tot))))
                rev += sm * q_us / tot
            inv += tot
        extra_days = max(0, -(-n // 5) - 2) + 3 * max(0, -(-n // 8) - 1)
        vals[n] = rev - n * (50.0 + 2.0 * fert) - extra_days * GC_P["v219x_worker_cost"]
    if GC_P["v219x_margins"]:
        best = 10
        if GC_P["v219x_skip_below"] is not None and vals.get(10, 0.0) < GC_P["v219x_skip_below"]:
            return 0, vals
        for n, m in sorted((int(k), float(v)) for k, v in GC_P["v219x_margins"].items()):
            if n in vals and vals[n] - vals.get(10, 0.0) >= m:
                best = n
        return best, vals
    best = max(vals, key=lambda n: vals[n])
    if best != 10 and vals[best] - vals.get(10, 0.0) < GC_P["v219x_margin"]:
        best = 10
    return best, vals


_DIV2 = {}


def _div2_check(obs):
    """Day-0 rival classification: a chassis copy runs the same opening and holds $1,034-1,059 at step 2; elites and
    other divergent rivals hold something else (12 to 1,571 in the recordings)."""
    step = int(obs["step"])
    if step == 0:
        _DIV2.clear()
    if step == 2 and "on" not in _DIV2:
        me = int(obs["player"]); rm = float(obs["farms"][1 - me]["money"])
        lo, hi = GC_P["div2_band"]
        _DIV2["on"] = not (lo <= rm <= hi)
        _GC_REPORT["gc_div2"] = int(_DIV2["on"]); _GC_REPORT["gc_div2_money"] = int(rm)


_STRAW_SHOPS = ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")


_ES = {}


def _early_straw(obs, action):
    """Early strawberries on the tape: on es_days, the tape's PLANT WHEAT on an NW tile becomes PLANT STRAWBERRY (up to
    es_n tiles) and its wheat seed purchases become strawberry seed purchases; the cow purchases of es_skip_cows are
    dropped to pay for them. The tape keeps watering those tiles and harvests whatever they hold on its wheat cadence."""
    step = int(obs["step"]); day = step // 24; hour = step % 24
    if step == 0:
        _ES.clear(); _ES["tiles"] = set(); _ES["n"] = 0; _ES["owed"] = 0
    me = int(obs["player"]); farm = obs["farms"][me]
    money = float(farm["money"])
    shed = dict(obs["private"]["shed"])
    if _ES.get("owed", 0) > 0 or shed.get("COW", 0) > 0:
        # cows bought back: one per listed day at hour 0 when the cash is there
        if day in GC_P["es_cow_days"] and hour == 0 and _ES["owed"] > 0 and money >= 400 + GC_P["es_cow_reserve"]:
            action["market"] = [["BUY_ANIMAL", "COW", 1]] + list(action.get("market") or [])
            _ES["owed"] -= 1; money -= 400
            _GC_REPORT["gc_es_cows_back"] = _GC_REPORT.get("gc_es_cows_back", 0) + 1
        # a unit picking up cows takes the extra ones along; on an empty pasture where the tape's action is a no-op it places one
        positions = [farm["farmer"]] + list(farm["hands"])
        invs = list(obs["private"]["inventories"])
        units = [action.get("farmer", ["PASS"])] + list(action.get("hands") or [])
        extra = int(shed.get("COW", 0))
        for u, a in enumerate(units):
            if not isinstance(a, list) or not a or u >= len(positions):
                continue
            x, y = int(positions[u][0]), int(positions[u][1])
            t = farm["tiles"][y][x]
            inv = invs[u] if u < len(invs) else {}
            if a[0] == "PICKUP" and len(a) >= 2 and a[1] == "COW" and extra > 0:
                n0 = int(a[2]) if len(a) >= 3 else 1
                units[u] = ["PICKUP", "COW", n0 + extra]; extra = 0
                _GC_REPORT["gc_es_cow_carry"] = _GC_REPORT.get("gc_es_cow_carry", 0) + 1
            elif (a[0] in ("FEED", "CARE", "COLLECT_FERTILIZER", "HARVEST", "PASS") and int(inv.get("COW", 0)) > 0
                  and isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" not in t):
                units[u] = ["PLACE", "COW"]
                _GC_REPORT["gc_es_cow_placed"] = _GC_REPORT.get("gc_es_cow_placed", 0) + 1
        action["farmer"] = units[0]; action["hands"] = units[1:]
    waves = [dict(days=GC_P["es_days"], quads=GC_P["es_quads"], n=GC_P["es_n"], key="n")] if GC_P["es_days"] else []
    for i, w in enumerate(GC_P["es_waves"] or ()):
        waves.append(dict(days=tuple(w.get("days", ())), quads=tuple(w.get("quads", ("NE",))), n=int(w.get("n", 8)), key="n%d" % i))
    wave = next((w for w in waves if day in w["days"]), None)
    if wave is None and day not in GC_P["es_skip_cows"]:
        return action
    seeds = dict(obs["private"]["seeds"])
    mk = list(action.get("market") or [])
    out_mk = []
    for o in mk:
        if o and o[0] == "BUY_ANIMAL" and o[1] == "COW" and day in GC_P["es_skip_cows"]:
            _GC_REPORT["gc_es_cows_skipped"] = _GC_REPORT.get("gc_es_cows_skipped", 0) + int(o[2])
            _ES["owed"] = _ES.get("owed", 0) + int(o[2])
            continue
        if o and o[0] == "BUY_SEED" and o[1] == "WHEAT" and wave is not None:
            # the wheat seeds stay (the tape's other replants need them); strawberry seeds are bought on top
            k = int(o[2]); room = wave["n"] - _ES.get(wave["key"], 0) - int(seeds.get("STRAWBERRY", 0))
            a = max(0, min(k, room, int((money - 10 * k) // GC_P["es_min_cash"])))
            out_mk.append(o)
            if a > 0:
                out_mk.append(["BUY_SEED", "STRAWBERRY", a]); money -= 100 * a
                _GC_REPORT["gc_es_seeds"] = _GC_REPORT.get("gc_es_seeds", 0) + a
            continue
        out_mk.append(o)
    action["market"] = out_mk
    if wave is not None:
        positions = [farm["farmer"]] + list(farm["hands"])
        avail = int(seeds.get("STRAWBERRY", 0))
        units = [action.get("farmer", ["PASS"])] + list(action.get("hands") or [])
        for u, a in enumerate(units):
            if not (isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT" and a[1] == "WHEAT") or u >= len(positions):
                continue
            x, y = int(positions[u][0]), int(positions[u][1])
            if _gc_quad(x, y) not in wave["quads"] or _ES.get(wave["key"], 0) >= wave["n"] or avail <= 0:
                continue
            if farm["tiles"][y][x] is not None:
                continue
            units[u] = ["PLANT", "STRAWBERRY"]; avail -= 1; _ES[wave["key"]] = _ES.get(wave["key"], 0) + 1; _ES["tiles"].add((x, y))
            _GC_REPORT["gc_es_planted"] = _GC_REPORT.get("gc_es_planted", 0) + 1
        action["farmer"] = units[0]; action["hands"] = units[1:]
    return action


_HG = {}
_HG_MOV = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def _hg_tape_events(tape, day0, day1, board=10):
    """Replay the tape's unit moves on days day0..day1 (every unit respawns at the shed each day; a HIRE spawns its hand
    on the least-occupied shed-access tile, NWSE order, as the engine does) and list (step, kind, pos, item) events:
    BUILD_PASTURE / BUILD_COOP / PLACE of an animal / BUY_ANIMAL."""
    half = board // 2
    acc = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    ev = []
    for day in range(day0, day1 + 1):
        pos = [list(acc[0])]
        for t in range(24 * day, min(len(tape), 24 * day + 24)):
            a = tape[t] if isinstance(tape[t], dict) else {}
            units = [a.get("farmer")] + list(a.get("hands") or [])
            for u, c in enumerate(units):
                if u >= len(pos) or not isinstance(c, (list, tuple)) or not c:
                    continue
                if c[0] in _HG_MOV:
                    dx, dy = _HG_MOV[c[0]]
                    nx, ny = pos[u][0] + dx, pos[u][1] + dy
                    if 0 <= nx < board and 0 <= ny < board:
                        pos[u] = [nx, ny]
                elif c[0] in ("BUILD_PASTURE", "BUILD_COOP"):
                    ev.append((t, c[0], tuple(pos[u]), None))
                elif c[0] == "PLACE" and len(c) >= 2 and c[1] in ("SHEEP", "COW", "GOOSE"):
                    ev.append((t, "PLACE", tuple(pos[u]), c[1]))
            for o in a.get("market") or []:
                if not (isinstance(o, (list, tuple)) and o):
                    continue
                if o[0] == "HIRE":
                    occ = {p: 0 for p in acc}
                    for p in pos:
                        if tuple(p) in occ:
                            occ[tuple(p)] += 1
                    pos.append(list(sorted(occ.items(), key=lambda kv: (kv[1], acc.index(kv[0])))[0][0]))
                elif o[0] == "BUY_ANIMAL" and len(o) >= 3:
                    ev.append((t, "BUY", None, (o[1], int(o[2]))))
    return ev


def _hg_plan(obs, tape, days):
    """The tape's sheep bought on `days` and the tiles they are placed on (placements in order, after the sheep bought
    earlier from day 6 on). A placement converts when its tile is empty now and the tape builds its pasture before the
    placement. Returns (coop tiles, flags in placement order)."""
    ev = _hg_tape_events(tape, 6, 11)
    d0 = min(days)
    skip = sum(x[1] for t, k, p, x in ev if k == "BUY" and x[0] == "SHEEP" and 6 <= t // 24 < d0)
    n = sum(x[1] for t, k, p, x in ev if k == "BUY" and x[0] == "SHEEP" and t // 24 in days)
    places = [(t, p) for t, k, p, x in ev if k == "PLACE" and x == "SHEEP"]
    builds = [(t, p) for t, k, p, x in ev if k == "BUILD_PASTURE"]
    tiles = obs["farms"][int(obs["player"])]["tiles"]
    step = int(obs["step"])
    coops = []; flags = []
    for t, p in places[skip:skip + n]:
        ok = (p not in coops and not isinstance(tiles[p[1]][p[0]], dict)   # empty, or land the tape buys first
              and any(step <= tb < t and pb == p for tb, pb in builds))
        if ok:
            coops.append(p)
        flags.append(bool(ok))
    return coops, flags


def _hg_target(tape, step, u, pos):
    """Where unit u's next PLACE SHEEP of the day happens on the tape, walking its moves from `pos`."""
    x, y = int(pos[0]), int(pos[1])
    for t in range(step + 1, min(len(tape), 24 * (step // 24 + 1))):
        a = tape[t] if isinstance(tape[t], dict) else {}
        units = [a.get("farmer")] + list(a.get("hands") or [])
        if u >= len(units) or not isinstance(units[u], (list, tuple)) or not units[u]:
            continue
        c = units[u]
        if c[0] in _HG_MOV:
            dx, dy = _HG_MOV[c[0]]
            if 0 <= x + dx < 10 and 0 <= y + dy < 10:
                x, y = x + dx, y + dy
        elif c[0] == "PLACE" and len(c) >= 2 and c[1] == "SHEEP":
            return (x, y)
        elif c[0] == "PICKUP":
            return None
    return None


def _hg_hd2_decide(obs, action, st):
    """HD2 (the chassis's day-10 goose/cow/sheep choice) skips when the farm has a coop: our converted coops must not
    switch it off, so they are shown to it as pastures (animals kept)."""
    orig = _HG_HD2_ORIG
    cfg = GC_P.get("herd_goose")
    mode = cfg.get("hd2", "base") if isinstance(cfg, dict) else "base"
    if not (_HG.get("on") and _HG.get("coops")) or mode == "skip":
        return orig(obs, action, st)
    farm = obs["farms"][int(obs["player"])]
    saved = []
    try:
        for (x, y) in _HG["coops"]:
            t = farm["tiles"][y][x]
            if isinstance(t, dict) and t.get("kind") == "COOP":
                saved.append((x, y, t))
                if mode == "see":
                    t2 = dict(t); t2["kind"] = "PASTURE"   # our geese count as egg supply in its forecast
                else:
                    t2 = {"kind": "PASTURE"}               # "base": the choice the tape would have made without them
                farm["tiles"][y][x] = t2
        return orig(obs, action, st)
    finally:
        for x, y, t in saved:
            farm["tiles"][y][x] = t


_HG_HD2_ORIG = globals().get("_hd2_decide")
if _HG_HD2_ORIG is not None and GC_P.get("herd_goose"):
    _hd2_decide = _hg_hd2_decide


def _herd_goose(obs, action):
    """HERD track: the tape's day-8/9 sheep become geese against divergent rivals in towns without a yarn store."""
    cfg = GC_P["herd_goose"]
    if not isinstance(cfg, dict):
        cfg = {}
    step = int(obs["step"]); day = step // 24
    if step == 0:
        _HG.clear()
    if step < 144 or not isinstance(action, dict):
        return action
    me = int(obs["player"]); farm = obs["farms"][me]
    if "on" not in _HG:
        _HG["on"] = False
        ad = globals().get("_AD_STATE"); adr = globals().get("_AD_REPORT") or {}
        div2 = bool(_DIV2.get("on")) and cfg.get("div2", True)
        ad143 = isinstance(ad, dict) and bool(ad.get("off")) and adr.get("ad_step") == 143 and cfg.get("ad143", True)
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        impl = globals().get("_IMPL"); ch = getattr(impl, "chassis", None)
        native = ch.players.get(me) if ch is not None else None
        why = "div" if (div2 or ad143) else "copy"
        if (div2 or ad143) and "YARN_STORE" not in shops and native and native.get("route") in ch.routes:
            coops, flags = _hg_plan(obs, ch.routes[native["route"]], list(cfg.get("days", [8, 9])))
            why = "r%s:%d/%d" % (native.get("route"), len(coops), len(flags))
            if coops:
                _HG.update(on=True, coops=set(coops), flags=flags, k=0, n=len(coops), route=native["route"], bought=0,
                           built=0, picked=0, placed=0, fail=0, credit=0, sold=0, sites={})
        elif "YARN_STORE" in shops:
            why = "yarn"
        _GC_REPORT["gc_hg"] = why
    if not _HG.get("on"):
        return action
    tiles = farm["tiles"]
    shed = {k: int(v) for k, v in dict(obs["private"]["shed"]).items()}
    invs = list(obs["private"].get("inventories") or [])
    positions = [farm["farmer"]] + list(farm["hands"])
    units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    market = [list(o) if isinstance(o, (list, tuple)) else o for o in (action.get("market") or [])]
    last = int(cfg.get("last_day", 11))
    changed = False
    # geese placed on our coops: their eggs are sold on top of the tape's planned egg sales
    for (x, y) in _HG["coops"]:
        t = tiles[y][x]
        if isinstance(t, dict) and t.get("animal") == "GOOSE" and (x, y) not in _HG["sites"]:
            _HG["sites"][(x, y)] = int(t.get("placed_day", day))
            _HG["placed"] += 1
    if day <= last:
        tape = _IMPL.chassis.routes[_HG["route"]]
        ta = tape[step] if step < len(tape) and isinstance(tape[step], dict) else {}
        tape_sheep = sum(int(o[2]) for o in (ta.get("market") or []) if isinstance(o, (list, tuple)) and len(o) >= 3
                         and o[0] == "BUY_ANIMAL" and o[1] == "SHEEP")
        # purchases: the tape's sheep (or the cows a chassis layer made of them) whose placement tile is a coop of ours
        if day in cfg.get("days", [8, 9]):
            add = []
            for o in market:
                if not (isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL"):
                    continue
                if not (o[1] == "SHEEP" or (o[1] == "COW" and tape_sheep > 0)):
                    continue
                q = int(o[2])
                if o[1] == "COW":
                    q = min(q, tape_sheep); tape_sheep -= q
                g = 0
                for _i in range(q):
                    fl = _HG["flags"]; k = _HG["k"]
                    if k < len(fl) and fl[k]:
                        g += 1
                    _HG["k"] = k + 1
                if g <= 0:
                    continue
                if g < int(o[2]):
                    o[2] = int(o[2]) - g
                    add.append(["BUY_ANIMAL", "GOOSE", g])
                else:
                    o[1] = "GOOSE"
                _HG["bought"] += g; changed = True
            market.extend(add)
        taken = set()
        g_shed = int(shed.get("GOOSE", 0))
        for u, c in enumerate(units):
            if u >= len(positions) or not isinstance(c, (list, tuple)) or not c:
                continue
            x, y = int(positions[u][0]), int(positions[u][1]); tile = tiles[y][x]
            inv = invs[u] if u < len(invs) else {}
            if c[0] == "BUILD_PASTURE" and (x, y) in _HG["coops"] and tile is None:
                units[u] = ["BUILD_COOP"]; _HG["built"] += 1; changed = True
            elif (c[0] == "PICKUP" and len(c) >= 2 and c[1] == "SHEEP" and (len(c) < 3 or int(c[2]) == 1)
                    and _HG["picked"] < _HG["bought"] and g_shed >= 1
                    and not any(int(inv.get(a_, 0)) for a_ in ("COW", "SHEEP", "GOOSE"))):
                tgt = _hg_target(tape, step, u, (x, y))
                if tgt is not None and tgt in _HG["coops"]:
                    units[u] = ["PICKUP", "GOOSE"] + list(c[2:]); g_shed -= 1; _HG["picked"] += 1; changed = True
            elif (c[0] == "PLACE" and len(c) >= 2 and c[1] == "SHEEP" and int(inv.get("GOOSE", 0)) > 0
                    and int(inv.get("SHEEP", 0)) <= 0):
                if isinstance(tile, dict) and tile.get("kind") == "COOP" and "animal" not in tile and (x, y) not in taken:
                    units[u] = ["PLACE", "GOOSE"]; taken.add((x, y)); changed = True
                else:
                    _HG["fail"] += 1
    # egg credit: harvests on our geese's coops
    for u, c in enumerate(units):
        if u >= len(positions) or not (isinstance(c, (list, tuple)) and c and c[0] == "HARVEST"):
            continue
        x, y = int(positions[u][0]), int(positions[u][1]); tile = tiles[y][x]
        if (x, y) in _HG["sites"] and isinstance(tile, dict) and tile.get("animal") == "GOOSE":
            _HG["credit"] += max(0, int(tile.get("yield_units", 0) or 0))
    if _HG["credit"] > 0 and cfg.get("sell", True):
        act2 = dict(action); act2["farmer"] = units[0]; act2["hands"] = units[1:]; act2["market"] = []
        try:
            stock = projected_shed(act2, FarmView(obs))
        except Exception:
            stock = dict(shed)
        planned = sum(max(0, int(o[2])) for o in market if isinstance(o, list) and len(o) >= 3 and o[:2] == ["SELL", "EGG"])
        extra = min(_HG["credit"], max(0, int(stock.get("EGG", 0)) - planned))
        if extra > 0:
            for o in market:
                if isinstance(o, list) and len(o) >= 3 and o[:2] == ["SELL", "EGG"]:
                    o[2] = int(o[2]) + extra
                    break
            else:
                if len(market) < 10:
                    market.insert(0, ["SELL", "EGG", extra])
                else:
                    extra = 0
            if extra > 0:
                _HG["credit"] -= extra; _HG["sold"] += extra; changed = True
    if changed:
        action = dict(action); action["farmer"] = units[0]; action["hands"] = units[1:]; action["market"] = market
    _GC_REPORT["gc_hg_n"] = "%d/%d/%d/%d/%d f%d s%d" % (_HG["n"], _HG["built"], _HG["bought"], _HG["picked"],
                                                       _HG["placed"], _HG["fail"], _HG["sold"])
    return action


_S2TX = {}


def _s2tx_book(obs, day, prod, n, me):
    """Forecast (our revenue, the rival's revenue) of `prod` from today to day 29 when we add n plots today, selling
    on arrival into the book drained by the town (current shops + expected future ones) and supplied by every visible
    plant of both farms (units per production as the controller's forecasts count them)."""
    shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
    if prod == "STRAWBERRY":
        buyers = _STRAW_SHOPS; fw = 0.5 * GC_P["future_shop_w"] * GC_P["straw_future_w"]
        ages = [10 + 2 * k + int(GC_P["straw_lag"]) for k in range(4)]; u = float(GC_P["straw_units"])
        w_us, w_op = GC_P["straw_our_w"], GC_P["straw_opp_w"]
    else:
        buyers = ("PIZZA_SHOP", "FARMERS_MARKET"); fw = 0.25 * GC_P["future_shop_w"]
        ages = [9, 11]; u = float(GC_P.get("tomato_units_fc", 8.0)) / 2.0
        w_us, w_op = 1.0, GC_P["opp_tomato_w"]
    k_now = sum(1 for x in shops if x in buyers); n_shops = len(shops)
    sup = [{}, {}]
    for side, w in ((me, w_us), (1 - me, w_op)):
        for row in obs["farms"][side]["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("crop") == prod:
                    pd = int(t["planted_day"])
                    for a in ages:
                        if pd + a >= day:
                            sup[side == me][pd + a] = sup[side == me].get(pd + a, 0.0) + u * w
    inv = float(obs["market"]["inventory"][prod]); rev = [0.0, 0.0]
    for d in range(day, 30):
        unl = min(8, d // 3) - n_shops
        inv -= 6.0 * (k_now + max(0, unl) * fw) + 1.0
        q = sup[0].get(d, 0.0)       # the rival's units
        if q > 0:
            rev[1] += q * 0.5 * (_gc_price(prod, int(inv)) + _gc_price(prod, int(inv + q))); inv += q
        q = sup[1].get(d, 0.0) + (u * n if (d - day) in ages else 0.0)
        if q > 0:
            rev[0] += q * 0.5 * (_gc_price(prod, int(inv)) + _gc_price(prod, int(inv + q))); inv += q
    return rev


def _s2tx_eval(obs, day, n):
    """Margin forecast of converting n of today's strawberry plantings to tomatoes: tomato revenue + the tile freed
    ~6 days earlier (wheat at today's value) + seeds/fertilizer saved - the strawberries' revenue - what the rival's
    strawberries gain from our missing ones + what its tomatoes lose to ours."""
    me = int(obs["player"])
    val = {p_: float(_gc_price(p_, obs["market"]["inventory"][p_])) for p_ in _GC_PRODUCTS}
    fert = val.get("FERTILIZER", 50.0)
    s1 = _s2tx_book(obs, day, "STRAWBERRY", n, me); s0 = _s2tx_book(obs, day, "STRAWBERRY", 0, me)
    t1 = _s2tx_book(obs, day, "TOMATO", n, me); t0 = _s2tx_book(obs, day, "TOMATO", 0, me)
    S = s1[0] - s0[0]; Ds = s0[1] - s1[1]          # rival strawberry revenue our plots take away
    T = t1[0] - t0[0]; Dt = t0[1] - t1[1]          # rival tomato revenue our plots take away
    v_w = (6 * val["WHEAT"] - 10 - fert) / 4.0 + GC_P["wheat_feed_bonus"]
    F = n * float(GC_P.get("s2tx_free_days", 6.0)) * max(0.0, v_w)
    C = n * (50.0 + fert)
    w = float(GC_P.get("s2tx_denial_w", 1.0))
    return T + F + C - S + w * (Dt - Ds), (int(S), int(T), int(F), int(C), int(Ds), int(Dt))


def _straw_to_tom(obs, action):
    day = int(obs["step"]) // 24
    if int(obs["step"]) == 0:
        _S2TX.clear()
    if day not in GC_P["s2t_days"] or not (_DIV2.get("on") or GC_P["s2t_all"]):
        return action
    shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
    ext_n = None
    if GC_P["s2t_max_shops"] is not None and sum(1 for s in shops if s in _STRAW_SHOPS) > GC_P["s2t_max_shops"]:
        ext = GC_P.get("s2t_ext")
        if not ext:
            return action
        n_s = sum(1 for s in shops if s in _STRAW_SHOPS); n_t = sum(1 for s in shops if s in ("PIZZA_SHOP", "FARMERS_MARKET"))
        if n_s > int(ext.get("straw", 1)) or n_t < int(ext.get("tom", 1)) or day not in ext.get("days", GC_P["s2t_days"]):
            return action
        ext_n = int(ext.get("max_n", 99))
        stx0 = _S2TX.setdefault(day, {"seed": 0, "plant": 0})
        if "fc" not in stx0:
            try:
                nb = int(ext.get("fc_n", 13))
                v, parts = _s2tx_eval(obs, day, nb)
                stx0["fc"] = v
                _GC_REPORT["gc_s2tx_fc"] = "%d %d:%s" % (day, int(v), ",".join(str(x) for x in parts))
            except Exception as e:
                stx0["fc"] = None
                _GC_REPORT["gc_s2tx_fc_err"] = repr(e)[:120]
        if ext.get("fc_margin") is not None and (stx0["fc"] is None or stx0["fc"] < float(ext["fc_margin"])):
            return action
        _GC_REPORT["gc_s2t_ext"] = 1
    if GC_P["s2t_max_sim"] is not None and not GC_P["s2t_all"]:
        me = int(obs["player"]); same = 0; n = 0
        for ra, rb in zip(obs["farms"][me]["tiles"], obs["farms"][1 - me]["tiles"]):
            for ta, tb in zip(ra, rb):
                ka = ta if not isinstance(ta, dict) else (ta.get("crop") or ta.get("animal") or ta.get("kind"))
                kb = tb if not isinstance(tb, dict) else (tb.get("crop") or tb.get("animal") or tb.get("kind"))
                same += (ka == kb); n += 1
        sim = same / float(max(1, n))
        _GC_REPORT["gc_s2t_sim"] = round(sim, 3)
        if sim > GC_P["s2t_max_sim"]:
            return action
    if ext_n is None and int(GC_P["s2t_max_n"]) < 99:
        ext_n = int(GC_P["s2t_max_n"])   # TOMATO track: partial conversion in the base (no strawberry shop) towns too
    crop = GC_P["s2t_crop"]
    if GC_P["s2t_by_town"]:
        crop = "TOMATO" if ("PIZZA_SHOP" in shops or "FARMERS_MARKET" in shops) else ("CARROT" if "PET_CAFE" in shops else "WHEAT")
        _GC_REPORT["gc_s2t_crop"] = crop
    cmds = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    changed = 0; new = []
    if ext_n is not None:
        # partial conversion: the seeds bought for the batch are split (tomato seeds for at most ext_n plantings);
        # a PLANT turns into tomato only while the converted seeds cover every tomato PLANT of the turn
        stx = _S2TX.setdefault(day, {"seed": 0, "plant": 0})
        market = []; seed_add = 0   # counters are committed only after the market-size guard below
        for o in action.get("market") or []:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY" and stx["seed"] + seed_add < ext_n:
                k = min(int(o[2]), ext_n - stx["seed"] - seed_add); seed_add += k; changed += 1
                market.append(["BUY_SEED", crop, k])
                if int(o[2]) - k > 0:
                    market.append(["BUY_SEED", "STRAWBERRY", int(o[2]) - k])
                continue
            market.append(o)
        have = int(dict(obs["private"]["seeds"]).get(crop, 0) or 0)
        t_now = sum(1 for c in cmds if isinstance(c, list) and len(c) >= 2 and c[0] == "PLANT" and c[1] == crop)
        conv = 0
        for c in cmds:
            if (isinstance(c, list) and len(c) >= 2 and c[0] == "PLANT" and c[1] == "STRAWBERRY"
                    and stx["plant"] + conv < ext_n and t_now + conv + 1 <= have):
                c = ["PLANT", crop]; conv += 1
            new.append(c)
        if len(market) > 10:
            return action
        stx["seed"] += seed_add; stx["plant"] += conv; changed += conv
        if changed:
            action = dict(action); action["farmer"] = new[0]; action["hands"] = new[1:]; action["market"] = market
            _GC_REPORT["gc_s2t"] = _GC_REPORT.get("gc_s2t", 0) + changed
            _GC_REPORT["gc_s2tx"] = _GC_REPORT.get("gc_s2tx", 0) + conv
        return action
    for c in cmds:
        if isinstance(c, list) and len(c) >= 2 and c[0] == "PLANT" and c[1] == "STRAWBERRY":
            c = ["PLANT", crop]; changed += 1
        new.append(c)
    market = []
    for o in action.get("market") or []:
        if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
            o = ["BUY_SEED", crop, o[2]]; changed += 1
        market.append(o)
    if changed:
        action = dict(action); action["farmer"] = new[0]; action["hands"] = new[1:]; action["market"] = market
        _GC_REPORT["gc_s2t"] = _GC_REPORT.get("gc_s2t", 0) + changed
    return action


_W2T = {}


def _wheat_to_tom(obs, action):
    """TOMATO track: on w2t_days the tape's wheat replants become tomatoes (seeds bought first: the engine drops every
    PLANT of a crop in a turn when the seeds do not cover all of them, and market orders settle after unit actions)."""
    step = int(obs["step"]); day = step // 24
    if step == 0:
        _W2T.clear()
    if day not in GC_P["w2t_days"] or not (_DIV2.get("on") or GC_P["s2t_all"]):
        return action
    if GC_P["w2t_adapt"]:
        ad = globals().get("_AD_STATE")
        if not (isinstance(ad, dict) and ad.get("off")):
            return action
    st = _W2T.setdefault(day, {"bought": 0, "done": 0, "ok": None})
    me = int(obs["player"]); farm = obs["farms"][me]
    if st["ok"] is None:
        shops = list(_gc_get(obs["town"], "unlocked_shops", []) or [])
        dem = 6 * sum(1 for x in shops if x in ("PIZZA_SHOP", "FARMERS_MARKET"))
        ok = dem >= GC_P["w2t_min_dem"]
        if ok and GC_P["s2t_max_sim"] is not None and not GC_P["s2t_all"]:
            same = 0; n = 0
            for ra, rb in zip(obs["farms"][me]["tiles"], obs["farms"][1 - me]["tiles"]):
                for ta, tb in zip(ra, rb):
                    ka = ta if not isinstance(ta, dict) else (ta.get("crop") or ta.get("animal") or ta.get("kind"))
                    kb = tb if not isinstance(tb, dict) else (tb.get("crop") or tb.get("animal") or tb.get("kind"))
                    same += (ka == kb); n += 1
            ok = same / float(max(1, n)) <= GC_P["s2t_max_sim"]
        if ok and GC_P["s2t_days"] and day in GC_P["s2t_days"] and _GC_REPORT.get("gc_s2t"):
            ok = False   # s2t converts this day's strawberry batch: its seeds are the tomato seeds in the shed
        st["ok"] = ok
    if not st["ok"]:
        return action
    seeds_t = int(dict(obs["private"]["seeds"]).get("TOMATO", 0) or 0)
    n_tom = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "TOMATO")
    action = dict(action)
    if st["bought"] == 0 and not st.get("tried_buy_done"):
        k = min(int(GC_P["w2t_n"]), int(GC_P["w2t_total"]) - n_tom - seeds_t)
        mk = list(action.get("market") or [])
        if k <= 0 or float(farm["money"]) < GC_P["w2t_cash"] + 50 * k:
            st["tried_buy_done"] = True
            if k <= 0:
                st["ok"] = seeds_t > 0   # seeds already there (a previous day's leftovers) may still be used
            return action
        if len(mk) < 10:
            mk.append(["BUY_SEED", "TOMATO", k]); action["market"] = mk
            st["bought"] = k; st["buy_step"] = step
            _GC_REPORT["gc_w2t_seed"] = _GC_REPORT.get("gc_w2t_seed", 0) + k
        return action
    if st.get("buy_step") == step:
        return action
    cmds = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    t_now = sum(1 for c in cmds if isinstance(c, list) and len(c) >= 2 and c[0] == "PLANT" and c[1] == "TOMATO")
    lim = int(GC_P["w2t_total"]) - n_tom
    new = []; conv = 0
    for c in cmds:
        if (isinstance(c, list) and len(c) >= 2 and c[0] == "PLANT" and c[1] == "WHEAT" and st["done"] < max(st["bought"], 0) + 99
                and t_now + conv + 1 <= seeds_t and conv < lim and st["done"] + conv < int(GC_P["w2t_n"])):
            c = ["PLANT", "TOMATO"]; conv += 1
        new.append(c)
    if conv:
        st["done"] += conv
        action["farmer"] = new[0]; action["hands"] = new[1:]
        _GC_REPORT["gc_w2t"] = _GC_REPORT.get("gc_w2t", 0) + conv
    return action


def _lead2(obs, action):
    """Chassis days: the market settles both players' order lists index by index in per-unit lockstep, and the town
    only drains after the market of steps 0 mod 4. The chassis (and every copy of it) already sells next step's
    lots one step early when that crosses no tick. Here every premium lot the tape plans at any later step inside
    the current tick window (up to and including the next step 0 mod 4) is sold now, from what the shed holds after
    this step's drops: a copy's lead of the same lot lands one step later, so ours is first, and against any rival
    the book can only be worse later in the window."""
    step = int(obs["step"]); r = step % 4
    if r == 0 or step >= 716:
        return action
    impl = globals().get("_IMPL"); ch = getattr(impl, "chassis", None)
    if ch is None:
        return action
    me = int(obs["player"]); st = ch.players.get(me)
    if not st or st.get("route") not in ch.routes:
        return action
    tape = ch.routes[st["route"]]
    last = step + (4 - r)          # the next step 0 mod 4: its sale precedes that tick, so it is inside the window
    planned = {}
    for t in range(step + 2, last + 1):
        if t % 72 == 0 or t >= len(tape) or not isinstance(tape[t], dict):
            continue
        for o in tape[t].get("market") or []:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] in GC_P["lead2_items"]:
                planned[o[1]] = planned.get(o[1], 0) + max(0, int(o[2]))
    if not planned:
        return action
    market = list(action.get("market") or [])
    if len(market) >= 10:
        return action
    # what the shed holds after this step's drops, net of what this step already sells
    shed = {k: int(v) for k, v in dict(obs["private"]["shed"]).items()}
    positions = [obs["farms"][me]["farmer"]] + list(obs["farms"][me]["hands"])
    invs = list(obs["private"].get("inventories", []) or [])
    cmds = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    for i, cmd in enumerate(cmds):
        if i < len(positions) and isinstance(cmd, list) and cmd and cmd[0] in ("DROP", "PLACE") and tuple(positions[i]) in _GC_ACCESS_SET and i < len(invs):
            if cmd[0] == "DROP":
                for k, v in dict(invs[i]).items():
                    shed[k] = shed.get(k, 0) + int(v)
            elif len(cmd) >= 2 and cmd[1] in _GC_PRODUCTS:
                shed[cmd[1]] = shed.get(cmd[1], 0) + int(cmd[2]) if len(cmd) >= 3 else shed.get(cmd[1], 0) + 1
    selling = {}
    for o in market:
        if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
            selling[o[1]] = selling.get(o[1], 0) + max(0, int(o[2]))
    prices = obs["market"]["prices"]
    added = 0
    for item, q in planned.items():
        avail = shed.get(item, 0) - selling.get(item, 0)
        qty = min(avail, q)
        if qty <= 0 or int(prices.get(item, 0)) < GC_P["lead2_min_price"]:
            continue
        if len(market) >= 10:
            break
        market.insert(0, ["SELL", item, int(qty)])   # first in the list: settles at index 0
        added += qty
    if added:
        action = dict(action); action["market"] = market
        _GC_REPORT["gc_lead2"] = _GC_REPORT.get("gc_lead2", 0) + added
    return action


def _gc_chassis_floor(obs, act):
    """Chassis phase: cut each SELL lot where the next unit would sell below chassis_unit_floor of the base price,
    while the shed keeps room for tonight's drop (units carry plus a margin)."""
    if not isinstance(act, dict) or not act.get("market"):
        return act
    priv = obs["private"]
    shed_tot = sum(int(v) for v in dict(priv["shed"]).values())
    carried = sum(int(v) for inv in priv.get("inventories", []) for v in dict(inv).values())
    sold = sum(int(o[2]) for o in act["market"] if o and o[0] == "SELL" and len(o) > 2)
    room = 100 - GC_P["chassis_floor_room"] - (shed_tot - sold + carried)
    if room <= 0:
        return act
    fr = GC_P["chassis_unit_floor"]
    out = []
    for o in act["market"]:
        if o and o[0] == "SELL" and len(o) > 2 and o[1] in (GC_P["chassis_floor_items"] or GC_P["unit_floor_items"]) and room > 0:
            p, n = o[1], int(o[2])
            i0 = int(obs["market"]["inventory"][p]); k = 0
            while k < n and _gc_price(p, i0 + k) >= fr * _GC_MKT[p][0]:
                k += 1
            k = max(k, n - room)
            if k < n:
                room -= n - k
                _GC_REPORT["gc_cfloor"] = _GC_REPORT.get("gc_cfloor", 0) + (n - k)
                if k <= 0:
                    continue
                o = ["SELL", p, k]
        out.append(o)
    act = dict(act); act["market"] = out
    return act


def _v219x_melons(obs, n_tom):
    """Melons for the block's free SE tiles: our 6 units a plant on the harvest day (age 10), sold on arrival into a
    book the town centre drains one unit a day and every visible melon plot supplies, net of seeds, time and the
    extra hands the bigger block needs."""
    kmax = max(0, min(int(GC_P["v219x_melon"]), 25 - int(n_tom)))
    if kmax <= 0 or n_tom <= 0:
        return 0, {}
    P = int(obs["step"]) // 24
    age = int(GC_P["v219x_melon_age"])
    hd = min(29, P + age)
    sup = {}
    for farm in obs["farms"]:
        for row in farm["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("crop") == "MELON":
                    d = int(t["planted_day"]) + age
                    if P <= d <= 29:
                        sup[d] = sup.get(d, 0) + 6
    def xd(n):
        return max(0, -(-n // 5) - 2) + 3 * max(0, -(-n // 8) - 1)
    vals = {}
    for k in range(0, kmax + 1):
        inv = float(obs["market"]["inventory"]["MELON"]); rev = 0.0
        for d in range(P, 30):
            inv -= 1.0
            inv += sup.get(d, 0)
            if d == hd and k > 0:
                rev += sum(_gc_price("MELON", int(inv) + i) for i in range(6 * k))
                inv += 6 * k
        wc = GC_P["v219x_melon_wc"] if GC_P["v219x_melon_wc"] is not None else GC_P["v219x_worker_cost"]
        vals[k] = rev - k * (80.0 + GC_P["v219x_melon_cost"]) - (xd(n_tom + k) - xd(n_tom)) * wc
    best = max(vals, key=lambda k: vals[k])
    if vals[best] < GC_P["v219x_melon_margin"]:
        best = 0
    return best, vals


def _v219x_set_melons(obs, n):
    if not isinstance(globals().get("_V219_MELON"), list):
        return
    k, mv = 0, {}
    if GC_P["v219x_melon"] and n > 0:
        try:
            k, mv = _v219x_melons(obs, n)
        except Exception as e:
            _GC_REPORT["gc_v219x_merr"] = repr(e)[:120]
    _V219_MELON[0] = k
    _GC_REPORT["gc_v219x_melon"] = k
    if mv:
        _GC_REPORT["gc_v219x_mvals"] = " ".join("%d:%d" % (a, b) for a, b in sorted(mv.items()))


def _v233_worker_wool_first(obs, actor, targets):
    """V233's two-hand SE sheep crew with the wool delivered as soon as no target holds wool (the 2600+ copies'
    crews drop it two to three hours before ours and take the day's wool book); fertilizer is collected after."""
    farm = obs['farms'][obs['player']]; private = obs['private']; step = int(obs['step'])
    pos = tuple(farm['hands'][actor - 1]); inv = private['inventories'][actor]
    access = ((4, 4), (5, 4), (4, 5), (5, 5))
    home = min(access, key=lambda p: (abs(pos[0] - p[0]) + abs(pos[1] - p[1]), p))
    distance = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
    cargo = [item for item in ('WOOL', 'FERTILIZER') if inv.get(item, 0)]
    if cargo and step % 24 >= (22 if step // 24 == 29 else 23) - distance:
        return _v219_walk(pos, home) or ['PLACE', cargo[0], inv[cargo[0]]]
    missing = sum(not (isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('animal') == 'SHEEP') for x, y in targets)
    if missing and not inv.get('SHEEP', 0) and private['shed'].get('SHEEP', 0):
        return _v219_walk(pos, home) or ['PICKUP', 'SHEEP', min(missing, private['shed']['SHEEP'])]
    hungry = sum(not (isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('fed_today')) for x, y in targets)
    if hungry and not inv.get('WHEAT', 0) and private['shed'].get('WHEAT', 0):
        return _v219_walk(pos, home) or ['PICKUP', 'WHEAT', min(hungry, private['shed']['WHEAT'])]
    wool_left = any(isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('animal') == 'SHEEP'
                    and int(farm['tiles'][y][x].get('yield_units', 0) or 0) > 0 for x, y in targets)
    busy = wool_left or inv.get('WOOL', 0) > 0
    tasks = []
    for target in targets:
        x, y = target; tile = farm['tiles'][y][x]; command = None
        if tile is None: command = ['BUILD_PASTURE']
        elif isinstance(tile, dict) and tile.get('kind') == 'WEED': command = ['DIG']
        elif isinstance(tile, dict) and tile.get('kind') == 'PASTURE' and not tile.get('animal'):
            if inv.get('SHEEP', 0): command = ['PLACE', 'SHEEP']
        elif isinstance(tile, dict) and tile.get('animal') == 'SHEEP':
            if not tile['fed_today'] and inv.get('WHEAT', 0): command = ['FEED']
            elif not tile['cared_today']: command = ['CARE']
            elif tile['yield_units']: command = ['HARVEST']
            elif tile['fertilizer_available'] and not busy: command = ['COLLECT_FERTILIZER']
        if command: tasks.append((abs(pos[0] - x) + abs(pos[1] - y), targets.index(target), target, command))
    if inv.get('WOOL', 0) and not wool_left and not any(c[0] in ('FEED', 'CARE', 'BUILD_PASTURE', 'PLACE', 'DIG') for _d, _i, _t, c in tasks):
        _GC_REPORT["gc_v233_wool_first"] = _GC_REPORT.get("gc_v233_wool_first", 0) + 1
        return _v219_walk(pos, home) or ['PLACE', 'WOOL', inv['WOOL']]
    if tasks:
        _, _, target, command = min(tasks)
        return _v219_walk(pos, target) or command
    if cargo: return _v219_walk(pos, home) or ['PLACE', cargo[0], inv[cargo[0]]]
    return ['PASS']


if GC_P.get("v233_wool_first") and "_SL_WORKER" in globals():
    _SL_WORKER = _v233_worker_wool_first


def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _GC.reset()
    _GC.me = int(observation["player"])
    if step == 0 and _GC_DIV_SAVED:
        GC_P.update(_GC_DIV_SAVED); _GC_DIV_SAVED.clear()
    if step == 0 and GC_P.get("handover_fix2"):
        _ad0 = globals().get("_AD_STATE")
        if isinstance(_ad0, dict) and (_ad0.get("off") or _ad0.get("saved")) and callable(globals().get("_ad_restore")):
            _ad_restore()
            _GC_REPORT["gc_hfix2"] = _GC_REPORT.get("gc_hfix2", 0) + 1
        if isinstance(globals().get("_AD_REPORT"), dict):
            _AD_REPORT.update(ad_divergent=0, ad_step=-1, ad_sim=-1.0)
    if step == 0:
        _GC_RICH.clear()
    start = GC_P["start"]
    if GC_P.get("tom_debug") and step == 288 and not _GC_RICH.get("tdbg"):
        _GC_RICH["tdbg"] = True
        pl = []
        for side in (_GC.me, 1 - _GC.me):
            for row in observation["farms"][side]["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "TOMATO":
                        pl.append("%s%d/%d" % ("u" if side == _GC.me else "r", int(t["planted_day"]), int(t.get("yield_units", 0) or 0)))
        _GC_REPORT["gc_tom_plants"] = " ".join(pl)
        _GC_REPORT["gc_tom_inv0"] = int(observation["market"]["inventory"]["TOMATO"])
    steps = GC_P["rich_steps"] or ((GC_P["rich_start"],) if GC_P["rich_start"] is not None else ())
    due = [s for s in steps if s <= step and s not in _GC_RICH.get("done", ())]
    if due and not _GC_RICH.get("rich") and not _GC_RICH.get("taken"):
        _GC_RICH.setdefault("done", set()).update(due)
        _GC_RICH["checked"] = True
        shops = list(_gc_get(observation["town"], "unlocked_shops", []) or [])[:max(4, len(_gc_get(observation["town"], "unlocked_shops", []) or [])) if GC_P["rich_steps"] else 4]
        k = sum(1 for s in shops if s in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
        _GC_RICH["rich"] = k >= GC_P["rich_min"]
        if _GC_RICH["rich"] and GC_P["rich_eval"]:
            try:
                ev = _GC.rich_eval(observation)
            except Exception as e:
                ev = -1e9
                _GC_REPORT["gc_rich_err"] = repr(e)[:120]
            _GC_REPORT["gc_rich_eval"] = int(ev) if ev > -1e8 else None
            _mg = GC_P["se_straw_margin"]
            _ad = globals().get("_AD_STATE")
            if GC_P["rich_div_margin"] is not None and isinstance(_ad, dict) and _ad.get("off"):
                _mg = GC_P["rich_div_margin"]
            _GC_RICH["rich"] = ev > _mg
        if not _GC_RICH["rich"] and GC_P["rich_tom_min"] > 0:
            kt = sum(1 for s in shops[:4] if s in ("PIZZA_SHOP", "FARMERS_MARKET"))
            if kt >= GC_P["rich_tom_min"]:
                try:
                    evt = _GC.rich_eval_tom(observation)
                except Exception as e:
                    evt = -1e9
                    _GC_REPORT["gc_rich_err"] = repr(e)[:120]
                _GC_REPORT["gc_rich_tom_eval"] = int(evt) if evt > -1e8 else None
                if evt > GC_P["rich_tom_margin"]:
                    _GC_RICH["rich"] = True
                    _GC_RICH["tom"] = True
                    _GC_REPORT["gc_rich_tom"] = 1
                    for kk, v in GC_P["rich_tom_over"].items():
                        if kk not in _GC_DIV_SAVED:
                            _GC_DIV_SAVED[kk] = GC_P.get(kk)
                    GC_P.update(GC_P["rich_tom_over"])
        if not _GC_RICH["rich"] and GC_P["rich_tom_dem"] > 0:
            kd = sum(6 for s in shops[:4] if s in ("PIZZA_SHOP", "FARMERS_MARKET"))
            _GC_REPORT["gc_tom_dem"] = kd
            if kd >= GC_P["rich_tom_dem"]:
                _GC_RICH["rich"] = True
                _GC_RICH["tomdem"] = True
                _GC_REPORT["gc_rich_tomdem"] = 1
                for kk, v in GC_P["rich_tom_dem_over"].items():
                    if kk not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[kk] = GC_P.get(kk)
                GC_P.update(GC_P["rich_tom_dem_over"])
        if not _GC_RICH["rich"] and GC_P["rich_car_min"] > 0:
            kc = sum(2 if s == "PET_CAFE" else (1 if s == "FARMERS_MARKET" else 0) for s in shops[:4])
            if kc >= GC_P["rich_car_min"]:
                _GC_RICH["rich"] = True
                _GC_RICH["car"] = True
                _GC_REPORT["gc_rich_car"] = 1
                for kk, v in GC_P["rich_car_over"].items():
                    if kk not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[kk] = GC_P.get(kk)
                GC_P.update(GC_P["rich_car_over"])
        if not _GC_RICH["rich"] and GC_P["herd_rich_margin"] is not None:
            try:
                me = int(observation["player"]); _GC.me = me
                farm = observation["farms"][me]
                quads = list(farm["unlocked_quadrants"])
                n_empty = sum(1 for row in farm["tiles"] for t in row if t is None)
                se_open = "SE" not in quads and "NE" in quads and "SW" in quads
                allshops = list(_gc_get(observation["town"], "unlocked_shops", []) or [])
                hk, hn, hv, _hs = _GC._herd_plan(observation, step // 24, allshops, max(0, n_empty - GC_P["herd_keep_free"]),
                                                   se_open, float(farm["money"]) - GC_P["rich_hire_budget"],
                                                   kinds=GC_P["herd_rich_over"].get("herd_kinds"))
            except Exception as e:
                hk, hn, hv = None, 0, -1e9
                _GC_REPORT["gc_rich_err"] = repr(e)[:120]
            _GC_REPORT["gc_herd_rich_eval"] = "%s%d:%d" % ((hk or "-")[0], hn, int(hv)) if hv > -1e8 else None
            if hk and hv > GC_P["herd_rich_margin"]:
                _GC_RICH["rich"] = True
                _GC_RICH["herd"] = True
                _GC_REPORT["gc_rich_herd"] = 1
                for kk, v in GC_P["herd_rich_over"].items():
                    if kk not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[kk] = GC_P.get(kk)
                GC_P.update(GC_P["herd_rich_over"])
        _GC_REPORT["gc_rich"] = int(_GC_RICH["rich"])
        if _GC_RICH["rich"] and GC_P["rich_over"] and not _GC_RICH.get("tom") and not _GC_RICH.get("car") and not _GC_RICH.get("herd") and not _GC_RICH.get("tomdem"):
            for kk, v in GC_P["rich_over"].items():
                if kk not in _GC_DIV_SAVED:
                    _GC_DIV_SAVED[kk] = GC_P.get(kk)
            GC_P.update(GC_P["rich_over"])
    if GC_P["start_div2"] is not None and step >= 2:
        # the step-2 cash rule (see _div2_check) classed the rival divergent: take over at start_div2
        if not _DIV2 and step <= 2:
            try:
                _div2_check(observation)
            except Exception as e:
                _GC_REPORT["gc_div2_err"] = repr(e)[:120]
        if _DIV2.get("on"):
            start = min(start, GC_P["start_div2"])
            _GC_REPORT["gc_start"] = start
            if GC_P["div_over"] and not _GC_RICH.get("div_applied"):
                _GC_RICH["div_applied"] = True
                for k, v in GC_P["div_over"].items():
                    if k not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[k] = GC_P.get(k)
                GC_P.update(GC_P["div_over"])
    if GC_P["start_div"] is not None:
        # ADAPT (chassis layer) flags a rival whose farm diverged from ours by step 143/359: take over earlier
        ad = globals().get("_AD_STATE")
        if isinstance(ad, dict) and ad.get("off"):
            start = min(start, GC_P["start_div"]) if GC_P["start_div2"] is not None else GC_P["start_div"]
            adr = globals().get("_AD_REPORT") or {}
            if GC_P["start_div143"] is not None and adr.get("ad_step") == 143:
                # the rival had diverged by day 5 already: take over at start_div143 instead
                start = GC_P["start_div143"]
            _GC_REPORT["gc_start"] = start
            _GC_REPORT["gc_ad_step"] = adr.get("ad_step", -1)
            if GC_P["div_over"] and not _GC_RICH.get("div_applied"):
                _GC_RICH["div_applied"] = True
                for k, v in GC_P["div_over"].items():
                    if k not in _GC_DIV_SAVED:
                        _GC_DIV_SAVED[k] = GC_P.get(k)
                GC_P.update(GC_P["div_over"])
    if _GC_RICH.get("rich"):
        if "at" not in _GC_RICH:
            _GC_RICH["at"] = step
        start = min(start, _GC_RICH["at"])
        _GC_REPORT["gc_start"] = start
    _rb = GC_P.get("hg_rebuy")
    if _rb and _rb.get("takeover") and _HG.get("on") and _HG.get("bought", 0) > 0 and step >= 288:
        # HERD track: the yarn store the converted sheep were missing arrives as shop 4 (day 12) or 5 (day 15): take over
        # that day so the controller can buy sheep while they still pay
        _sh = list(_gc_get(observation["town"], "unlocked_shops", []) or [])
        for _i, _d in ((3, 12), (4, 15)):
            if (_i < int(_rb.get("upto", 5)) and len(_sh) > _i and _sh[_i] == "YARN_STORE" and "YARN_STORE" not in _sh[:_i]
                    and step >= 24 * _d):
                if 24 * _d < start:
                    start = 24 * _d
                    _GC_REPORT["gc_start"] = start
                    _GC_REPORT["gc_hg_take"] = _d
                break
    if GC_P["open"] is not None:
        od = GC_P["open"].get("from_day", _OPEN_DEFAULT["from_day"]) if isinstance(GC_P["open"], dict) else _OPEN_DEFAULT["from_day"]
        start = min(start, 24 * int(od))   # the scheduled opening starts on its day whatever the rival is classed as
    if step >= start:
        _GC_RICH["taken"] = True
    if step == 0 and GC_P["chassis_globals"]:
        for kk, vv in GC_P["chassis_globals"].items():
            if kk in globals():
                globals()[kk] = vv
    if step == 0 and GC_P["ad_thresh"] and isinstance(globals().get("_AD_CFG"), dict):
        for kk, vv in GC_P["ad_thresh"].items():
            _AD_CFG["thresh"][int(kk)] = float(vv)
    if GC_P["v219e"] and isinstance(globals().get("_V219_DAY"), list):
        if step == 0:
            for _nm, _v in (("_V219_MIN_SHOPS", 2), ("_V219_CASH", globals().get("_K_V219_CASH", 14969)), ("_V219_MIN_PRICE", globals().get("CROP_MIN_PRICE", 70))):
                if isinstance(globals().get(_nm), list):
                    globals()[_nm][0] = _v
        elif step == 288:
            e = GC_P["v219e"]
            sh = list(_gc_get(observation["town"], "unlocked_shops", []) or [])[:4]
            kd = sum(6 for s in sh if s in ("PIZZA_SHOP", "FARMERS_MARKET"))
            _GC_REPORT["gc_v219e_dem"] = kd
            ad = globals().get("_AD_STATE")
            div_ok = (not e.get("div_only")) or (isinstance(ad, dict) and bool(ad.get("off")))
            if kd >= e.get("min_dem", 6) and div_ok:
                size = 10
                for k, v in sorted(((int(k), v) for k, v in e.get("sizes", {}).items())):
                    if kd >= k: size = v
                _V219_DAY[0] = int(e.get("day", 13))
                for _nm, _v in (("_V219_MIN_SHOPS", int(e.get("min_shops", 1))), ("_V219_CASH", float(e.get("cash", 9000))), ("_V219_MIN_PRICE", float(e.get("min_price", 55)))):
                    if isinstance(globals().get(_nm), list):
                        globals()[_nm][0] = _v
                if isinstance(globals().get("_V219_N"), list):
                    _V219_N[0] = size
                _GC_REPORT["gc_v219e"] = "d%d:%d" % (_V219_DAY[0], size)
        if step >= 700 and isinstance(globals().get("_V219_REPORT"), dict):
            _GC_REPORT["gc_v219_rep"] = " ".join("%s=%s" % (k[:12], v) for k, v in _V219_REPORT.items() if v)
    if step < start and GC_P["v219x"] and isinstance(globals().get("_V219_N"), list):
        if step == 0:
            _V219_N[0] = 10
            if isinstance(globals().get("_V219_DAY"), list):
                _V219_DAY[0] = int(GC_P["v219x_day"])
            if isinstance(globals().get("_V219_THIRST"), list):
                _V219_THIRST[0] = bool(GC_P["v219x_thirst"])
            if isinstance(globals().get("_V219_MELON"), list):
                _V219_MELON[0] = 0
        elif (GC_P["v219x_early_n"] and step == 24 * GC_P["v219x_early_day"]
              and isinstance(globals().get("_V219_DAY"), list) and _V219_DAY[0] == 18):
            # a big block planted a day before the copy's day-18 block sells ahead of it on days 25-28
            try:
                n, vals = _v219x_size(observation)
            except Exception as e:
                n, vals = 10, {}
                _GC_REPORT["gc_v219x_err"] = repr(e)[:120]
            _GC_REPORT["gc_v219x_early_vals"] = " ".join("%d:%d" % (k, v) for k, v in sorted(vals.items()))
            if n >= GC_P["v219x_early_n"]:
                _V219_DAY[0] = GC_P["v219x_early_day"]
                _V219_N[0] = n
                _GC_REPORT["gc_v219x_n"] = n
                _GC_REPORT["gc_v219x_day"] = GC_P["v219x_early_day"]
                _v219x_set_melons(observation, n)
        elif step == 24 * (_V219_DAY[0] if isinstance(globals().get("_V219_DAY"), list) else 18):
            try:
                n, vals = _v219x_size(observation)
            except Exception as e:
                n, vals = 10, {}
                _GC_REPORT["gc_v219x_err"] = repr(e)[:120]
            _V219_N[0] = n
            _GC_REPORT["gc_v219x_n"] = n
            _GC_REPORT["gc_v219x_vals"] = " ".join("%d:%d" % (k, v) for k, v in sorted(vals.items()))
            _v219x_set_melons(observation, n)
    if step < start:
        action = _GC_PARENT(observation, configuration)
        if GC_P["es_days"] or GC_P["es_waves"]:
            try:
                action = _early_straw(observation, action)
            except Exception as e:
                _GC_REPORT["gc_es_err"] = repr(e)[:120]
        if GC_P["s2t_days"]:
            try:
                _div2_check(observation)
                action = _straw_to_tom(observation, action)
            except Exception as e:
                _GC_REPORT["gc_s2t_err"] = repr(e)[:120]
        if GC_P["w2t_days"]:
            try:
                _div2_check(observation)
                action = _wheat_to_tom(observation, action)
            except Exception as e:
                _GC_REPORT["gc_w2t_err"] = repr(e)[:120]
        if GC_P.get("herd_goose"):
            try:
                _div2_check(observation)
                action = _herd_goose(observation, action)
            except Exception as e:
                _GC_REPORT["gc_hg_err"] = repr(e)[:120]
        if GC_P["lead2"]:
            try:
                action = _lead2(observation, action)
            except Exception as e:
                _GC_REPORT["gc_lead2_err"] = repr(e)[:120]
        if GC_P["sells_first_chassis"] and isinstance(action, dict) and action.get("market"):
            try:
                action = dict(action)
                ad = globals().get("_AD_STATE")
                if GC_P["sells_first_div_sort"] and isinstance(ad, dict) and ad.get("off"):
                    action["market"] = _gc_sells_first(action["market"], observation["market"]["inventory"])
                else:
                    action["market"] = _gc_sells_first(action["market"])   # a copy runs this same list: keep its sell order
            except Exception as e:
                _GC_REPORT["gc_sf_err"] = repr(e)[:120]
        if GC_P["cash_guard_min"] > 0 and step < 24 and isinstance(action, dict) and action.get("market"):
            try:
                action = _gc_cash_guard(observation, action)
            except Exception as e:
                _GC_REPORT["gc_cg_err"] = repr(e)[:120]
        if GC_P["chassis_unit_floor"] > 0 and step >= 24 * GC_P["chassis_floor_from"]:
            try:
                action = _gc_chassis_floor(observation, action)
            except Exception as e:
                _GC_REPORT["gc_cfloor_err"] = repr(e)[:120]
        if GC_P["straw_cap"]:
            try:
                action = _straw_cap(observation, action)
            except Exception as e:
                _GC_REPORT["gc_straw_cap_err"] = repr(e)[:120]
        if GC_P["fert_idle"]:
            try:
                action = _fert_idle(observation, action)
            except Exception as e:
                _GC_REPORT["gc_fert_idle_err"] = repr(e)[:120]
        if GC_P.get("handover_fix1") and GC_P["sell_timing"] and isinstance(action, dict):
            try:
                _GC._mk_track(observation)
                # the shed our SELLs draw on this turn: units that DROP now land in it before the market runs (the
                # chassis sells goods in the turn they are dropped; the pre-drop shed would credit those sales to the rival)
                shed_ = {k: int(v) for k, v in dict(observation["private"]["shed"]).items()}
                invs_ = list(observation["private"].get("inventories") or [])
                for u_, a_ in enumerate([action.get("farmer")] + list(action.get("hands") or [])):
                    if not (isinstance(a_, (list, tuple)) and a_ and u_ < len(invs_)):
                        continue
                    if a_[0] == "DROP":
                        for k2, n2 in dict(invs_[u_]).items():
                            shed_[k2] = shed_.get(k2, 0) + int(n2)
                    elif a_[0] == "PLACE" and len(a_) >= 2 and a_[1] in _GC_PRODUCTS:
                        # the chassis's partial delivery ["PLACE", item, n] on a shed-access tile
                        n2 = min(int(a_[2]) if len(a_) >= 3 else 1, int(dict(invs_[u_]).get(a_[1], 0)))
                        if n2 > 0:
                            shed_[a_[1]] = shed_.get(a_[1], 0) + n2
                    elif a_[0] == "PICKUP" and len(a_) >= 2:
                        n2 = int(a_[2]) if len(a_) >= 3 else 1
                        shed_[a_[1]] = max(0, shed_.get(a_[1], 0) - max(0, n2))
                _GC._mk_store(observation, shed_, [o for o in (action.get("market") or []) if isinstance(o, list)])
                _GC_REPORT["gc_hfix1"] = sum(len(v) for v in _GC.rival_sales.values())
            except Exception as e:
                _GC_REPORT["gc_hfix1_err"] = repr(e)[:120]
        return action
    if GC_P["arb_chassis"] and not _GC_RICH.get("arb_handed"):
        _GC_RICH["arb_handed"] = True
        st = _ARB_STATE.get(int(observation["player"]))
        if st:
            for p, h in st.get("held", {}).items():
                _GC.arb[p] = _GC.arb.get(p, 0) + h
            st["held"] = {}
    try:
        return _GC.act(observation)
    except Exception as e:  # never forfeit a turn
        _GC_REPORT["gc_errors"] += 1
        _GC_REPORT["gc_last_error"] = repr(e)[:200]
        return {"farmer": ["PASS"], "hands": [], "market": []}


agent.telemetry = _GC_REPORT
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
