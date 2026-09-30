"""build_lg.py OUT BASE OVERRIDES_JSON : BASE (a final build) + GC_P['div_over'] updated with OVERRIDES (the controller's
divergent-rival settings, applied at its takeover), e.g. goose purchases in the day-16..18 herd window."""
import sys, json
out, base_p, over = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
base = open(base_p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in base else '\n'
section = '''
# >>> LG: controller divergent-rival overrides (div_over) %(over)r
GC_P["div_over"] = dict(GC_P["div_over"] or {}, **%(over)r)
''' % dict(over=over)
open(out, 'w', encoding='utf-8', newline='').write(base + section.replace('\n', nl))
print('wrote', out)
