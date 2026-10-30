"""Match schools.json to the Ofsted 'latest inspections' MI file and attach a compact Ofsted record."""
import csv, json, re, sys, difflib, os
HERE = os.path.dirname(os.path.abspath(__file__))
from datetime import datetime

OFSTED = sys.argv[1]
SCHOOLS = os.path.join(HERE, 'schools.json')
# Ofsted's local authority name for each borough in the data, where it isn't just '&' spelled out
LA_NAME = {'Richmond': 'Richmond upon Thames', 'Kingston': 'Kingston upon Thames'}
GRADE = {'1': 'Outstanding', '2': 'Good', '3': 'Requires improvement', '4': 'Inadequate'}
STOP = r"\b(the|primary|school|schools|academy|and|nursery|c ?of ?e|ce|church of england|rc|catholic|voluntary aided|va|of|st|saint|&)\b"

def norm(n):
    n = n.lower().replace("'", '').replace('’', '')
    n = re.sub(r'[^a-z ]', ' ', n)
    n = re.sub(r'\binfants\b', 'infant', n)
    return re.sub(r'\s+', ' ', re.sub(STOP, ' ', n)).strip()

def d(s):
    try: return datetime.strptime(s, '%d/%m/%Y')
    except Exception: return None

def iso(dt): return dt.strftime('%Y-%m-%d') if dt else None
def val(x): return None if x in ('', 'NULL', 'Not applicable', None) else x

rows = [r for r in csv.DictReader(open(OFSTED, encoding='utf-8-sig', errors='replace'))
        if r['Ofsted phase'] in ('Primary', 'All-through', 'Secondary')
        # a secondary-only school can't be a primary, however alike the names (Pimlico Primary vs Pimlico Academy)
        and not (r['Statutory lowest age'].isdigit() and int(r['Statutory lowest age']) >= 11)]
BY_URN = {r['URN']: r for r in rows}
# schools whose name has changed too much to match (renamed, or all-through schools listed by their primary phase)
URN_FOR = {
    'Eastbrook School (primary phase)': '101243',
    'Goresbrook School (primary phase)': '140962',
    'St Mary Magdalene CofE All Through School (Woolwich site)': '100171',
    'Grange Park School (formerly Grange Park Infant and Nursery)': '102432',
    'Whitehall Primary (formerly Whitehall Infant)': '102399',
    'Prendergast Primary (Prendergast Ladywell School)': '150318',
    'School 21': '138196',
    'School 360': '148623',
    # extra sites inspected with their main school
    'Manor Primary - Sandringham Road site (infants)': '101193',
    'Ripple Primary - Westbury site': '101198',
    'Valence Primary - St Georges Road site': '101222',
}

def record(r):
    out = {'urn': r['URN'], 'name': r['School name'], 'link': f"https://reports.ofsted.gov.uk/provider/21/{r['URN']}"}
    card_dt, oeif_dt, ung_dt = d(r['Inspection start date']), d(r['Inspection start date of latest OEIF graded inspection']), d(r['Date of latest ungraded inspection'])
    if card_dt and val(r['Curriculum and teaching']):
        areas = [('Inclusion', 'Inclusion'), ('Curriculum and teaching', 'Curriculum and teaching'), ('Achievement', 'Achievement'),
                 ('Attendance and behaviour', 'Attendance and behaviour'), ('Personal development and wellbeing', 'Personal development and wellbeing'),
                 ('Early years', 'Early years (where applicable)'), ('Leadership and governance', 'Leadership and governance')]
        out.update(kind='card', date=iso(card_dt), safeguarding=val(r['Safeguarding standards']),
                   areas=[[k, val(r[c])] for k, c in areas if val(r[c])])
    elif oeif_dt:
        oe = r['Latest OEIF overall effectiveness']
        sub = [('Quality of education', 'Latest OEIF quality of education'), ('Behaviour and attitudes', 'Latest OEIF behaviour and attitudes'),
               ('Personal development', 'Latest OEIF personal development'), ('Leadership and management', 'Latest OEIF effectiveness of leadership and management'),
               ('Early years', 'Latest OEIF early years provision (where applicable)')]
        out.update(date=iso(oeif_dt), areas=[[k, GRADE.get(r[c], None)] for k, c in sub if GRADE.get(r[c])],
                   safeguarding={'Yes': 'Effective', 'No': 'Not effective'}.get(r['Latest OEIF  safeguarding is effective?']))
        if oe in GRADE: out.update(kind='grade', grade=GRADE[oe])
        else: out.update(kind='areas')
    elif ung_dt and val(r['Ungraded inspection overall outcome']):
        out.update(kind='ungraded', date=iso(ung_dt))
    else:
        out.update(kind='none')
    base_dt = card_dt if out['kind'] == 'card' else oeif_dt
    if ung_dt and (not base_dt or ung_dt > base_dt) and val(r['Ungraded inspection overall outcome']):
        out['ungraded'] = {'date': iso(ung_dt), 'outcome': r['Ungraded inspection overall outcome']}
    if val(r['Most recent category of concern']): out['concern'] = r['Most recent category of concern']
    if r['Does the latest full inspection relate to the URN of the current school?'] == 'No' or \
       r['Does the latest OEIF graded inspection relate to the URN of the current school?'] == 'No':
        out['predecessor'] = True
    return out

data = json.load(open(os.path.join(HERE, 'schools.pre-ofsted.json')))
log, used = [], {}
for s in data['schools']:
    if s['name'] in URN_FOR:
        s['of'] = record(BY_URN[URN_FOR[s['name']]])
        used.setdefault(s['of']['urn'], []).append((s, True))
        continue
    cand = [r for r in rows if r['Local authority'] == LA_NAME.get(s['borough'], s['borough'].replace(' & ', ' and '))]
    target = norm(s['name'])
    scored = []
    for r in cand:
        if r['Ofsted phase'] == 'Secondary' and difflib.SequenceMatcher(None, target, norm(r['School name'])).ratio() < 0.8: continue
        ratio = difflib.SequenceMatcher(None, target, norm(r['School name'])).ratio()
        pc = (r['Postcode'].replace(' ', '') == (s['postcode'] or '').replace(' ', ''))
        if any((w in target) != (w in norm(r['School name'])) for w in ('infant', 'junior')): continue
        scored.append((ratio + (0.5 if pc else 0), ratio, pc, r))
    scored.sort(key=lambda x: -x[0])
    best = scored[0] if scored else None
    contains = best and (target in norm(best[3]['School name']) or norm(best[3]['School name']) in target) and len(target) > 3
    ok = best and (best[1] >= 0.8 or (contains and len(target) >= 8) or (best[2] and (best[1] >= 0.45 or contains)))
    if ok:
        s['of'] = record(best[3])
        used.setdefault(best[3]['URN'], []).append((s, best[2]))
        if best[1] < 0.95: log.append(f"~ {s['borough']}: {s['name']!r} -> {best[3]['School name']!r} ({best[1]:.2f}, pc={best[2]})")
    else:
        s['of'] = None
        log.append(f"X {s['borough']}: {s['name']!r} best {best[3]['School name']!r} ({best[1]:.2f}, pc={best[2]})" if best else f"X {s['name']}")

# one Ofsted record claimed by several schools (e.g. "St Mark's" vs "St Mary's", as "St" is ignored): keep the postcode match
for urn, claims in used.items():
    if len(claims) > 1 and any(pc for _, pc in claims):
        for s, pc in claims:
            if not pc:
                s['of'] = None
                log.append(f"X {s['borough']}: {s['name']!r} lost URN {urn} to a postcode match")

# split-site schools share one Ofsted record
for s in data['schools']:
    if s['of'] is None and 'site)' in s['name']:
        stem = s['name'].split('(')[0].strip()
        sib = next((t for t in data['schools'] if t is not s and t['of'] and t['name'].split('(')[0].strip() == stem), None)
        if sib: s['of'] = sib['of']; log.append(f"= {s['name']!r} shares {sib['name']!r}")
json.dump(data, open(SCHOOLS, 'w'), separators=(',', ':'))
print('\n'.join(log))
print('dupes:', {k: [s['name'] for s, _ in v] for k, v in used.items() if sum(s['of'] is not None for s, _ in v) > 1})
import collections
print(collections.Counter((s['of'] or {}).get('kind', 'unmatched') for s in data['schools']))
