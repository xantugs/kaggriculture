"""Summarise mkt_probe.py rows: market failures on controller days, input no-ops, hour-0 room sales, end stock.
usage: mkt_probe_sum.py probe.jsonl"""
import sys, json, collections

fails = collections.Counter(); fail_units = collections.Counter(); fail_games = collections.defaultdict(set)
noops = collections.Counter(); noop_games = collections.defaultdict(set); noop_ex = collections.defaultdict(list)
cut = collections.Counter(); hire_fail = 0
sell0_nobuy = []; sell0_buy = 0
end_seeds = collections.Counter(); end_shed = collections.Counter(); end_inv = collections.Counter(); n = 0
seed_games = collections.Counter()
for line in open(sys.argv[1], encoding='utf-8'):
    r = json.loads(line); n += 1
    st0 = int(r['rep'].get('gc_start', 576) or 576)
    for st, v in r['orders'].items():
        st = int(st)
        if st < st0:
            continue
        for op, item, q, f, why in v['o']:
            if why == 'cut':
                cut[(op, item)] += 1
            elif why == 'hire_cash':
                hire_fail += 1
            elif why and op != 'SELL':
                k = (op, item, why, 'h%d' % (st % 24) if st % 24 < 2 else 'h2+')
                fails[k] += 1; fail_units[k] += q - f; fail_games[k].add((r['gid'], st // 24))
    for st, v in r['noop'].items():
        st = int(st)
        if st < st0:
            continue
        for w in v:
            noops[w] += 1; noop_games[w].add(r['gid']); noop_ex[w].append((r['gid'], st // 24, st % 24))
    for d, h in r['h0'].items():
        if isinstance(h, str) or int(d) * 24 < st0:
            continue
        buys = [o for o in (h.get('orders0') or []) if o[0] in ('BUY_PRODUCT', 'BUY_ANIMAL')]
        if h.get('sell0'):
            if not buys:
                sell0_nobuy.append((r['gid'], int(d), h['sell0'], sum(h['shed'].values())))
            else:
                sell0_buy += 1
    e = r.get('end') or {}
    for k, v in (e.get('seeds') or {}).items():
        end_seeds[k] += v; seed_games[k] += 1
    for k, v in (e.get('shed') or {}).items():
        end_shed[k] += v
    for x in e.get('inv') or []:
        for k, v in x.items():
            end_inv[k] += v
print('games', n)
print('== market failures on controller days (op, item, why, hour): orders, units unfilled, game-days')
for k, c in fails.most_common():
    print('  ', k, c, fail_units[k], len(fail_games[k]), sorted(fail_games[k])[:6])
print('== orders cut beyond 10:', dict(cut), ' hires failed for cash:', hire_fail)
print('== input no-ops on controller days:')
for k, c in noops.most_common():
    print('  ', k, c, 'games', len(noop_games[k]), noop_ex[k][:8])
print('== hour-0 room sale with no purchase: %d days (with purchases: %d)' % (len(sell0_nobuy), sell0_buy))
by = collections.Counter()
for g, d, s0, tot in sell0_nobuy:
    for o in s0:
        by[o[1]] += o[2]
print('   units by item', dict(by), sell0_nobuy[:10])
print('== end: seeds', dict(end_seeds), 'games', dict(seed_games), ' shed', dict(end_shed), ' carried', dict(end_inv))
