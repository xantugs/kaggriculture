"""Stream a daily corpus (one game per line) and count, per team: PLANT orders by crop and day, SELL order units by product
and phase (requested units, capped by nothing: an upper bound on fills), animal purchases by day.
usage: scan_melons.py corpus.jsonl[.gz] out.json [max_games]"""
import sys, json, gzip, collections

TOP = ['DSM', 'Boey', 'Vadim Vasilenko', 'M & M & P & Q', 'Majkel1337', 'DECEM', 'KawattaTaido', 'Unknown Mother-Goose',
       'Fourth Quadrant', 'Azat Akhtyamov', 'offhand']


def main():
    path, out = sys.argv[1], sys.argv[2]
    mx = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9
    op = gzip.open if path.endswith('.gz') else open
    plant = collections.defaultdict(lambda: collections.Counter())  # team -> (crop, day) -> n
    sell = collections.defaultdict(lambda: collections.Counter())   # team -> (prod, day) -> units requested
    anim = collections.defaultdict(lambda: collections.Counter())
    seats = collections.Counter()
    ng = 0
    with op(path, 'rt', encoding='utf-8') as fh:
        for line in fh:
            ng += 1
            if ng > mx: break
            d = json.loads(line)
            names = d['info']['TeamNames']
            acts = d['acts']
            for s in (0, 1):
                team = names[s]
                if team not in TOP: continue
                seats[team] += 1
                for t in range(1, len(acts)):
                    a = acts[t][s] if isinstance(acts[t], list) and len(acts[t]) > s else None
                    if not isinstance(a, dict): continue
                    day = (t - 1) // 24
                    units = [a.get('farmer')] + list(a.get('hands') or [])
                    for u in units:
                        if isinstance(u, list) and len(u) >= 2 and u[0] == 'PLANT':
                            plant[team][(u[1], day)] += 1
                    for o in a.get('market') or []:
                        if isinstance(o, list) and len(o) >= 3:
                            if o[0] == 'SELL':
                                try: sell[team][(o[1], day)] += int(o[2])
                                except Exception: pass
                            elif o[0] == 'BUY_ANIMAL':
                                try: anim[team][(o[1], day)] += int(o[2])
                                except Exception: pass
            del d
    res = {team: dict(seats=seats[team],
                      plant={f"{k[0]}|{k[1]}": v for k, v in plant[team].items()},
                      sell={f"{k[0]}|{k[1]}": v for k, v in sell[team].items()},
                      anim={f"{k[0]}|{k[1]}": v for k, v in anim[team].items()}) for team in seats}
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(ng, 'games', dict(seats))


if __name__ == '__main__':
    main()
