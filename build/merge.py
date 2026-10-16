"""Merge borough JSON files into one normalised school index (distances in metres)."""
import json, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))

DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'borough-data')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'schools.pre-ofsted.json')

TO_M = {'metres': 1.0, 'meters': 1.0, 'm': 1.0, 'km': 1000.0, 'miles': 1609.344, 'mile': 1609.344}
CLOSED = {'goldfinch', "st anne's", 'oasis academy putney', 'christ church ce primary school', 'kings avenue'}

def norm_pc(pc):
    if not pc: return None
    pc = re.sub(r'\s+', '', pc.upper())
    return pc[:-3] + ' ' + pc[-3:] if len(pc) > 4 else pc

out, flags = [], []
boroughs = {}
for f in sorted(glob.glob(os.path.join(DATA, '*.json'))):
    d = json.load(open(f))
    b = d['borough']
    boroughs[b] = {k: d.get(k) for k in ('default_method', 'method_notes', 'method_source', 'years_found', 'sources', 'gaps')}
    latest_year = max(d['years_found'])
    for s in d['schools']:
        years = {x['year'] for x in s['distances']}
        if latest_year not in years and min(d['years_found']) in years and max(years) < latest_year:
            # appears only in older data -> closed / renamed
            flags.append(f"{b}: dropped '{s['name']}' (absent from {latest_year})")
            continue
        recs = []
        for x in sorted(s['distances'], key=lambda r: -r['year']):
            r = {'y': x['year'], 's': x['status']}
            if x['status'] == 'distance':
                unit = (x.get('unit') or '').lower()
                v = x.get('value')
                if v is None or unit not in TO_M:
                    r['s'] = 'not_published'
                    flags.append(f"{b}: {s['name']} {x['year']} unusable unit {unit!r} value {v}")
                else:
                    if unit.startswith('mile') and b == 'Lambeth' and v > 100:
                        flags.append(f"{b}: {s['name']} {x['year']} {v} labelled miles, treated as metres")
                        unit = 'metres'
                    r['m'] = round(v * TO_M[unit], 1)
            if x.get('criterion_note'):
                r['n'] = x['criterion_note']
            recs.append(r)
        out.append({
            'name': s['name'], 'borough': b, 'postcode': norm_pc(s.get('postcode')),
            'type': s.get('type'), 'method': s.get('method') or d['default_method'],
            'note': s.get('method_note'), 'pan': s.get('pan'),
            'src': s.get('source_url'), 'd': recs,
        })

json.dump({'boroughs': boroughs, 'schools': out}, open(OUT, 'w'), separators=(',', ':'))
print(len(out), 'schools written to', OUT)
print('\n'.join(flags))
