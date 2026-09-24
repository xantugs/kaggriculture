from kaggle_environments.envs.kaggriculture.kaggriculture import market_price, MARKET_PARAMS, SHOPS

I0 = 10000
print("=== Revenue from selling N units starting at inventory I0 (no opponent) ===")
print(f"{'item':11s} {'N=25':>8s} {'N=50':>8s} {'N=100':>8s} {'N=200':>8s} {'N=500':>8s} {'N=1000':>8s}  floor_at")
for item in MARKET_PARAMS:
    row = []
    for N in (25, 50, 100, 200, 500, 1000):
        rev, inv = 0, I0
        for _ in range(N):
            p = market_price(item, inv)
            rev += p
            if p > 1: inv += 1
        row.append(rev)
    inv = I0
    while market_price(item, inv) > 1 and inv < I0 + 20000:
        inv += 1
    fl = inv - I0 if inv < I0 + 20000 else None
    print(f"{item:11s} " + " ".join(f"{r:8d}" for r in row) + f"  {fl}")

print()
print("=== Price when inventory is x units BELOW I0 (scarcity from town demand) ===")
print(f"{'item':11s} " + " ".join(f"{'x='+str(x):>7s}" for x in (0, 25, 50, 100, 200, 400)))
for item in MARKET_PARAMS:
    print(f"{item:11s} " + " ".join(f"{market_price(item, I0 - x):7d}" for x in (0, 25, 50, 100, 200, 400)))

print()
print("=== Town demand per shop instance per day ===")
for s, prods in SHOPS.items():
    mult = 2 if len(prods) == 1 else 1
    print(f"{s:15s} " + ", ".join(f"{p} x{6*mult}" for p in prods))

# expected shop-days: shop k unlocks at start of day 3k
shop_days = [30 - 3*k for k in range(1, 9)]
print("\nshop-days per unlock slot:", shop_days, "total", sum(shop_days), "-> expected per shop TYPE:", sum(shop_days)/8)
demand = {}
for s, prods in SHOPS.items():
    mult = 2 if len(prods) == 1 else 1
    for p in prods:
        demand[p] = demand.get(p, 0) + 6 * mult * sum(shop_days) / 8
print("Expected season-total town demand by product (+30 from town center):")
for p, d in sorted(demand.items(), key=lambda kv: -kv[1] * MARKET_PARAMS[kv[0]]['base']):
    print(f"  {p:11s} {d:6.0f} units  ~${d * MARKET_PARAMS[p]['base']:8.0f} at base price")
