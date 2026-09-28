import json, sys
for l in open(sys.argv[1], encoding='utf-8'):
    r = json.loads(l)
    st = r['start'] // 24
    print('== gid', r['gid'], 'm', r['m'], 'takeover day', st)
    for h in r['hs'][:3]:
        print('   hire search d%d lo %d h %d h_lo0 %s last_hires %d nvis %d must %d' % (h['day'], h['lo'], h['h'], h['h_lo0'], h['last_hires'], h['n_vis'], h['n_must']))
    for d in range(st - 2, st + 2):
        dd = r['days'].get(str(d), {})
        print('   d%d ctl=%s money0 %s hands23 %s maxh %s shed0 %s seeds0 %s' % (d, dd.get('ctl', False), int(dd.get('money0', 0)), dd.get('hands23'), dd.get('maxhands'), dd.get('shed0'), dd.get('seeds0')))
        print('       census %s fp %s/%s rs_n %s orders0 %s orders1 %s' % (dd.get('census0'), dd.get('footprint_n'), dd.get('fp_bonus'), dd.get('rival_sales_n'), dd.get('orders0'), dd.get('orders1')))
