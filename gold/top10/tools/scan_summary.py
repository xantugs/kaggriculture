"""Aggregate scan.py rows into mechanical-loss categories.

usage: scan_summary.py scan.jsonl [games.csv=gold/top10/gates/live0926/games.csv] [--json out.json] [--top N]

For every category: $/game over all scanned games (zeros included), games affected ($ > 0), worst games
(episode id, opponent, $, margin), $ by day, $/game by opponent group (games.csv opp_group, and the livecmp.py
split copy/annex/own x <2600/2600+), and 'flip' = lost games whose category $ is at least the deficit.
Dollar values (all computed in scan.py at the engine hook, see its docstring):
  night_drop   units discarded at the night drop x that evening's price (animals at purchase cost)
  escape       (product held on the tile + base production events left through the end of day 28) x evening price
  thirst       potential units (held + remaining window waterings / production events, capped) x evening price
  rot          units decremented by _decay_plants from a positive yield x that step's price
  miss_water   yield-window water bonus missed by non-ongoing crops, realised at harvest and cap-aware
               (min(max_yield, harvested + bonuses missed) - harvested) x price at the harvest step; the per-night
               upper bound (mww_v, each miss x evening price) is printed separately
  anim_cap     animal production clipped at max_held x evening price
  plant_cap    ongoing-crop production clipped at max_yield x evening price
  care_fedmiss pending care bonus wiped by an unfed production day on which a unit DID care the animal x evening price
  care_lost    the same wipe on production days where the animal was neither fed nor cared x evening price
  drop_action  overflow discarded by a daytime DROP into a full shed x price at that step
  end_stock    shed + carried goods + harvestable yield left at the end, walked down the final book
  end_seeds    seeds bought and never planted x seed price"""
import sys, os, json, csv, collections, math

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
CATS = ['night_drop', 'escape', 'thirst', 'rot', 'miss_water', 'anim_cap', 'plant_cap', 'care_fedmiss', 'care_lost',
        'drop_action', 'end_stock', 'end_seeds']
ACOST = {'GOOSE': 300, 'COW': 400, 'SHEEP': 500}


def day_values(ev):
    """{category: $} for one day's event dict."""
    v = {}
    v['night_drop'] = ev.get('drop_v', 0)
    v['escape'] = sum(e[-1] for e in ev.get('esc', []))
    v['thirst'] = sum(e[-1] for e in ev.get('thirst', []))
    v['rot'] = ev.get('rot_v', 0)
    v['miss_water'] = ev.get('mwwh_v', 0)
    v['anim_cap'] = ev.get('acap_v', 0)
    v['plant_cap'] = ev.get('pcap_v', 0)
    v['care_fedmiss'] = ev.get('carelc_v', 0)
    v['care_lost'] = ev.get('carel_v', 0) - ev.get('carelc_v', 0)
    v['drop_action'] = ev.get('ddrop_v', 0)
    return v


def grp_of(meta, gid):
    m = meta.get(str(gid))
    if not m:
        return None, None
    g = m['opp_group']
    t = 'copy' if g.startswith('copy (identical') else 'annex' if 'annex' in g else 'own'
    try:
        band = '2600+' if float(m['opp_rating_before']) >= 2600 else '<2600'
    except ValueError:
        band = '?'
    return g, '%s %s' % (t, band)


def main():
    args = [a for a in sys.argv[1:]]
    jout = None; top = 6
    if '--json' in args:
        i = args.index('--json'); jout = args[i + 1]; del args[i:i + 2]
    if '--top' in args:
        i = args.index('--top'); top = int(args[i + 1]); del args[i:i + 2]
    path = args[0]
    csvp = args[1] if len(args) > 1 else 'gold/top10/gates/live0926/games.csv'
    meta = {r['episode_id']: r for r in csv.DictReader(open(csvp, encoding='utf-8-sig'))} if os.path.exists(csvp) else {}
    rows = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
    bad = [r for r in rows if r.get('m') is None]
    rows = [r for r in rows if r.get('m') is not None]
    N = len(rows)
    print('games %d (dropped %d with no result)  wins %d  mean margin %+.0f  errors %d' % (
        N, len(bad), sum(r['m'] > 0 for r in rows), sum(r['m'] for r in rows) / max(1, N),
        sum(1 for r in rows if any(r.get('err') or []))))
    for r in bad:
        print('  no result:', r['gid'], r['opp'], (r.get('exc') or '')[-300:].replace('\n', ' | '))

    per = {}      # gid -> {cat: $}
    byday = {c: collections.Counter() for c in CATS}
    items = {c: collections.Counter() for c in CATS}      # units by item
    itemv = {c: collections.Counter() for c in CATS}      # $ by item
    counts = collections.Counter(); noop = collections.Counter(); mfail = collections.Counter()
    esc_kind = collections.Counter(); esc_kind_day = collections.Counter(); thirst_crop = collections.Counter()
    drop_room = collections.Counter(); drop_carry = []
    drop_walk = 0.0                                        # night drop valued by walking the evening book
    drop_min = 0.0; drop_chk = 0                           # cheapest possible discard of the same unit count; check
    mww_raw = 0.0
    thirst_age = collections.Counter(); thirst_age_v = collections.Counter()   # (crop, age) -> plants, $
    unfed_day = collections.Counter(); anim_day = collections.Counter()       # first strikes / animals owned, by day
    esc_list = []
    for r in rows:
        g = collections.Counter()
        for d, ev in r['days'].items():
            d = int(d)
            for c, v in day_values(ev).items():
                if v:
                    g[c] += v; byday[c][d] += v
            px = dict(zip(PRODUCTS, ev.get('px') or [0] * 9))
            for it, n in (ev.get('drop') or {}).items():
                items['night_drop'][it] += n
                itemv['night_drop'][it] += n * px.get(it, {'GOOSE': 300, 'COW': 400, 'SHEEP': 500}.get(it, 0))
            drop_walk += ev.get('drop_vw', 0); mww_raw += ev.get('mww_v', 0)
            if ev.get('drop'):
                units = sorted(px.get(it, ACOST.get(it, 0)) for _, inv in ev.get('carry', []) for it, n in inv.items()
                               for _ in range(n))
                nd = max(0, len(units) - ev.get('room23', 0))
                drop_min += sum(units[:nd]); drop_chk += nd != sum(ev['drop'].values())
            for k, n in (ev.get('unfed') or {}).items():
                unfed_day[d] += n
            anim_day[d] += sum((ev.get('anim') or {}).values())
            if ev.get('drop'):
                room = ev.get('room23', 0); tot = sum(ev['drop'].values())
                carried = sum(sum(x[1].values()) for x in ev.get('carry', []))
                drop_room['room>=80' if room >= 80 else 'room 20-79' if room >= 20 else 'room<20'] += ev.get('drop_v', 0)
                drop_carry.append((ev.get('drop_v', 0), r['gid'], r['opp'], d, room, carried, tot, ev.get('hands23')))
            for e in ev.get('esc', []):
                esc_list.append((round(e[-1]), r['gid'], r['opp'], d, e[0], 'placed d%d' % e[1], 'held %d' % e[2], 'fut %d' % e[3]))
                esc_kind[e[0]] += 1; esc_kind_day[(e[0], d)] += 1
                items['escape'][e[0]] += 1; itemv['escape'][e[0]] += e[-1]
            for e in ev.get('thirst', []):
                thirst_age[(e[0], e[1])] += 1; thirst_age_v[(e[0], e[1])] += e[-1]
                thirst_crop[e[0]] += 1; items['thirst'][e[0]] += 1; itemv['thirst'][e[0]] += e[-1]
            for key, cat in (('rot', 'rot'), ('acap', 'anim_cap'), ('pcap', 'plant_cap'), ('carelc', 'care_fedmiss'),
                             ('carel', 'care_lost'), ('ddrop', 'drop_action'), ('mwwh', 'miss_water')):
                for it, n in (ev.get(key) or {}).items():
                    items[cat][it] += n; itemv[cat][it] += n * px.get(it, 0)
                if key == 'carel':        # care_lost = carel minus its cared part
                    for it, n in (ev.get('carelc') or {}).items():
                        items[cat][it] -= n; itemv[cat][it] -= n * px.get(it, 0)
            for k in ('pass', 'blocked', 'idle', 'hires'):
                counts[k] += ev.get(k, 0)
            counts['hire_c'] += ev.get('hire_c', 0)
            noop.update(ev.get('noop') or {}); mfail.update(ev.get('mfail') or {})
        e = r.get('end') or {}
        if e:
            g['end_stock'] += e.get('v_shed', 0) + e.get('v_inv', 0) + e.get('v_tiles', 0)
            g['end_seeds'] += e.get('v_seeds', 0)
            fpx = dict(zip(PRODUCTS, e.get('px') or [0] * 9))
            for part in ('shed', 'inv', 'tiles'):
                for it, n in (e.get(part) or {}).items():
                    items['end_stock'][it] += n
                    itemv['end_stock'][it] += n * fpx.get(it, {'GOOSE': 300, 'COW': 400, 'SHEEP': 500}.get(it, 0))
            for it, n in (e.get('seeds') or {}).items():
                items['end_seeds'][it] += n; itemv['end_seeds'][it] += n * SEED[it]
        per[r['gid']] = g
    byid = {r['gid']: r for r in rows}
    for r in rows:        # the replay's team name; games.csv 'opponent' (display name) in brackets when it differs
        m_ = meta.get(str(r['gid']))
        if m_ and m_.get('opponent') and m_['opponent'] != r['opp']:
            r['opp'] = '%s [%s]' % (r['opp'], m_['opponent'])

    out = []
    for c in CATS:
        vals = [per[r['gid']][c] for r in rows]
        tot = sum(vals)
        aff = [r for r in rows if per[r['gid']][c] > 0]
        worst = sorted(aff, key=lambda r: -per[r['gid']][c])[:top]
        flips = [r for r in rows if r['m'] <= 0 and per[r['gid']][c] >= -r['m'] and per[r['gid']][c] > 0]
        groups = collections.defaultdict(list); groups2 = collections.defaultdict(list)
        for r in rows:
            g1, g2 = grp_of(meta, r['gid'])
            groups[g1].append(per[r['gid']][c]); groups2[g2].append(per[r['gid']][c])
        mean = tot / max(1, N)
        se = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(1, N - 1) / max(1, N)) if N > 1 else 0
        out.append(dict(
            name=c, dollars_per_game=round(mean, 1), se=round(se, 1), games_affected=len(aff), total=round(tot),
            days={d: round(v) for d, v in sorted(byday[c].items()) if v},
            items={k: [items[c][k], round(itemv[c][k])] for k in sorted(items[c], key=lambda k: -itemv[c][k] - items[c][k])},
            worst=[dict(gid=r['gid'], opp=r['opp'], usd=round(per[r['gid']][c]), margin=r['m'],
                        group=grp_of(meta, r['gid'])[1]) for r in worst],
            flips=[dict(gid=r['gid'], opp=r['opp'], usd=round(per[r['gid']][c]), margin=r['m']) for r in flips],
            by_group={str(k): [len(v), round(sum(v) / len(v), 1), sum(1 for x in v if x > 0)] for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))},
            by_group2={str(k): [len(v), round(sum(v) / len(v), 1), sum(1 for x in v if x > 0)] for k, v in sorted(groups2.items(), key=lambda kv: str(kv[0]))}))
    out.sort(key=lambda x: -x['dollars_per_game'])

    for x in out:
        print('\n== %-12s $%7.1f/game (se %.1f)  affected %3d/%d  total $%d' % (
            x['name'], x['dollars_per_game'], x['se'], x['games_affected'], N, x['total']))
        if not x['total'] and not x['items']:
            continue
        dd = sorted(x['days'].items(), key=lambda kv: -kv[1])
        print('   days ($):', ', '.join('d%d %d' % (d, v) for d, v in sorted(dd[:8])))
        print('   items [units, $]:', ', '.join('%s %d/$%d' % (k, u, v) for k, (u, v) in list(x['items'].items())[:9]))
        print('   worst:', '; '.join('%s %s $%d (m %+.0f, %s)' % (w['gid'], w['opp'], w['usd'], w['margin'], w['group']) for w in x['worst']))
        print('   by group ($/game, n, affected):', '; '.join('%s %.0f (%d, %d)' % (k, v[1], v[0], v[2]) for k, v in x['by_group2'].items()))
        print('   by opp_group:', '; '.join('%s %.0f (%d, %d)' % (k, v[1], v[0], v[2]) for k, v in x['by_group'].items()))
        if x['flips']:
            print('   losses where $ >= deficit: %d: %s' % (len(x['flips']), '; '.join('%s %s $%d vs m %+.0f' % (f['gid'], f['opp'], f['usd'], f['margin']) for f in x['flips'][:8])))

    print('\n== escapes by kind:', dict(esc_kind), ' by (kind, day):', dict(sorted(esc_kind_day.items(), key=lambda kv: (kv[0][1], kv[0][0]))))
    print('== escape events ($, gid, opp, day, kind, placed, held, future base events):')
    for t in sorted(esc_list, reverse=True)[:top * 2]:
        print('    ', t)
    print('== animals on tiles per game by day:', ', '.join('d%d %.1f' % (d, v / max(1, N)) for d, v in sorted(anim_day.items())))
    print('== unfed first strikes (no escape) per game by day:', ', '.join('d%d %.2f' % (d, v / max(1, N)) for d, v in sorted(unfed_day.items())))
    print('== thirst deaths by crop:', dict(thirst_crop))
    print('   by (crop, age at death): plants, $:', '; '.join('%s@%d %d $%d' % (k[0], k[1], v, round(thirst_age_v[k]))
                                                         for k, v in sorted(thirst_age.items())))
    print('== night drop per game: $%.1f at the evening price, $%.1f walking the evening book, $%.1f if the same number'
          ' of units had been the cheapest ones carried (engine drops farmer, hand 1, 2... in order; the rest is lost)'
          '  [unit-count mismatches %d]' % (sum(per[g]['night_drop'] for g in per) / max(1, N), drop_walk / max(1, N),
                                             drop_min / max(1, N), drop_chk))
    print('== missed window water per game: $%.1f realised at harvest (cap-aware) vs $%.1f per-night upper bound' % (
        sum(per[g]['miss_water'] for g in per) / max(1, N), mww_raw / max(1, N)))
    print('== night drop $ by shed room at hour 23:', {k: round(v) for k, v in drop_room.items()})
    print('   biggest night drops ($, gid, opp, day, room23, carried, discarded, hands):')
    for t in sorted(drop_carry, reverse=True)[:top]:
        print('    ', t)
    print('== unit-turns per game: pass %.1f  blocked %.2f  idle %.1f   hires %.1f  wage $%.0f' % tuple(
        counts[k] / max(1, N) for k in ('pass', 'blocked', 'idle', 'hires', 'hire_c')))
    print('== no-op actions per game:', ', '.join('%s %.2f' % (k, v / max(1, N)) for k, v in noop.most_common()))
    print('== failed market commits per game:', ', '.join('%s %.2f' % (k, v / max(1, N)) for k, v in mfail.most_common(12)))
    if jout:
        json.dump(dict(games=N, categories=out, night_drop_walked=drop_walk / max(1, N),
                       night_drop_cheapest=drop_min / max(1, N), miss_water_night_upper=mww_raw / max(1, N),
                       thirst_by_crop_age={'%s@%d' % k: [v, round(thirst_age_v[k])] for k, v in sorted(thirst_age.items())},
                       unfed_by_day={d: v / max(1, N) for d, v in sorted(unfed_day.items())}, counts={k: v / max(1, N) for k, v in counts.items()},
                       noop={k: v / max(1, N) for k, v in noop.items()}, mfail={k: v / max(1, N) for k, v in mfail.items()},
                       esc_kind_day={'%s@%d' % k: v for k, v in esc_kind_day.items()}, drop_room=dict(drop_room)),
                  open(jout, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
