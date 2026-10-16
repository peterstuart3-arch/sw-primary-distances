"""Build index.html and schools.csv from template.html and schools.json."""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

data_txt = open(os.path.join(HERE, 'schools.json')).read()
tpl = open(os.path.join(HERE, 'template.html')).read()
assert '/*__DATA__*/null' in tpl
open(os.path.join(ROOT, 'index.html'), 'w').write(tpl.replace('/*__DATA__*/null', data_txt))

d = json.loads(data_txt)
lab = {'all_offered': 'all offered', 'not_published': 'not published', 'no_distance_offers': 'no distance offers'}
with open(os.path.join(ROOT, 'schools.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['school', 'borough', 'postcode', 'type', 'measured_by', 'places', '2026_last_distance_m', '2025_last_distance_m',
                '2024_last_distance_m', '2023_last_distance_m', 'ofsted_urn', 'ofsted_latest', 'ofsted_date', 'ofsted_areas',
                'ofsted_ungraded_check', 'notes', 'source'])
    years = sorted({r['y'] for s in d['schools'] for r in s['d']}, reverse=True)[:4]
    for s in d['schools']:
        by = {r['y']: (r['m'] if r['s'] == 'distance' else lab.get(r['s'], r['s'])) for r in s['d']}
        o = s.get('of') or {}
        latest = {'card': 'Report card', 'grade': o.get('grade'), 'areas': 'Area grades only',
                  'ungraded': (o.get('ungraded') or {}).get('outcome'), 'none': 'Not yet inspected'}.get(o.get('kind'), '')
        areas = '; '.join(f'{a}: {g}' for a, g in o.get('areas', []))
        ung = o.get('ungraded')
        ung = f"{ung['outcome']} ({ung['date']})" if ung and o.get('kind') != 'ungraded' else ''
        w.writerow([s['name'], s['borough'], s['postcode'], s['type'], s['method'].replace('_', ' '), s['pan'] or '',
                    *[by.get(y, '') for y in (2026, 2025, 2024, 2023)], o.get('urn', ''), latest, o.get('date', ''), areas, ung,
                    s['note'] or '', s['src'] or ''])
print('Wrote index.html and schools.csv with', len(d['schools']), 'schools')
