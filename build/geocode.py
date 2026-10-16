"""Add each school's postcode coordinates to schools.json as "ll": [lat, lng], so the page needn't look them up."""
import json, os, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
SCHOOLS = os.path.join(HERE, 'schools.json')
API = 'https://api.postcodes.io'


def get(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise


d = json.load(open(SCHOOLS))
pcs = sorted({s['postcode'] for s in d['schools'] if s.get('postcode')})
found = {}
for i in range(0, len(pcs), 100):
    for x in get(API + '/postcodes', {'postcodes': pcs[i:i + 100]})['result']:
        if x['result']:
            found[x['query']] = [round(x['result']['latitude'], 6), round(x['result']['longitude'], 6)]
# schools sometimes keep a terminated postcode
for p in [p for p in pcs if p not in found]:
    r = get(API + '/terminated_postcodes/' + urllib.request.quote(p)).get('result')
    if r:
        found[p] = [round(r['latitude'], 6), round(r['longitude'], 6)]

missing = []
for s in d['schools']:
    s['ll'] = found.get(s.get('postcode'))
    if not s['ll']:
        missing.append(s['name'])
json.dump(d, open(SCHOOLS, 'w'), separators=(',', ':'))
print(f'Located {len(d["schools"]) - len(missing)} of {len(d["schools"])} schools.')
for n in missing:
    print('  no location:', n)
