import sys, json
tag, gid = sys.argv[1], int(sys.argv[2]); d0, d1 = int(sys.argv[3]), int(sys.argv[4])
role = sys.argv[5] if len(sys.argv) > 5 else 'ours'
for l in open('out/%s_days.jsonl' % tag, encoding='utf-8'):
    r = json.loads(l)
    if r['gid'] == gid and r['role'] == role and d0 <= r['d'] <= d1:
        print('d%d m0=%.0f hires=%d hire_h=%s land=%s herd=%s crops=%s shed=%s' % (r['d'], r['m0'], r['hires'], r['hire_h'], [(e['q'], e['h']) for e in r['land']], r.get('herd'), r.get('crops'), r.get('shed')))
        print('   fills', r['fills'])
        print('   ops', {k: v for k, v in r['ops'].items()}, 'fail', r['fail'], 'pas', r['pas'], 'move', r['move'])
