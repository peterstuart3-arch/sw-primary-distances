# SW London primary school distances

An interactive map that compares your home with the furthest distance each primary school offered a Reception place on national offer day. It covers Wandsworth, Merton, Lambeth, Richmond, Kingston, Sutton and Croydon.

Enter a postcode, use your location, or click the map. For each nearby school you get:

- your distance, measured the way that school measures it (straight line or walking route)
- the last distance offered in each recent year, and a verdict across all of them: Safe, Just inside, Mixed, Unlikely or Open
- the school's latest Ofsted outcome, in whichever format applies (overall grade, area grades or report card), with a link to the full reports

Live site: https://peterstuart3-arch.github.io/sw-primary-distances/

## What's in this repo

- `index.html` – the whole tool in one file, with the data built in. This is what GitHub Pages serves.
- `schools.csv` – the full index as a spreadsheet: 345 schools, last distance offered for 2024–2026 (Kingston to 2025; Richmond 2023 where 2024 is unpublished), measurement method, Ofsted outcome and the council source for each figure.
- `build/` – what's needed to rebuild `index.html` when the data changes:
  - `template.html` – the page, with a `/*__DATA__*/null` placeholder for the data
  - `schools.json` – the merged data, including Ofsted
  - `borough-data/` – the raw per-borough figures gathered from council documents
  - `merge.py` – merges the borough files into `schools.pre-ofsted.json`
  - `ofsted_match.py` – matches each school to Ofsted's "latest inspections" management information CSV and writes `schools.json`
  - `geocode.py` – adds each school's postcode coordinates to `schools.json`, so the page doesn't have to look them up
  - `build.py` – puts `schools.json` into `template.html` and writes `index.html` and `schools.csv`

## Yearly refresh

Allocation figures change after national offer day each April, and Ofsted publishes new management information monthly.

1. Update the files in `build/borough-data/` with the new year's figures from each council.
2. Run `python3 build/merge.py build/borough-data build/schools.pre-ofsted.json`.
3. Download the latest Ofsted "state-funded schools – latest inspections" CSV from https://www.gov.uk/government/statistics/monthly-management-information-ofsteds-school-inspections-outcomes and run `python3 build/ofsted_match.py path/to/that.csv`.
4. Run `python3 build/geocode.py` to add school locations.
5. Run `python3 build/build.py`, then commit and push.

## Caveats

"Last distance offered" is historical and changes every year. It is not a catchment boundary, and siblings, looked-after children, faith places and priority areas are offered before distance. The tool measures postcode centre to postcode centre, so treat anything within 100 m of a cut-off as uncertain. Always check the school's current admissions policy and the council's own figures before applying.

## Services used

- Map tiles: Esri static basemap tiles, using the ArcGIS Location Platform API key in `ESRI_KEY` in the template (restricted in the Esri dashboard to this site's address; 2 million tiles a month free). On any other address, or if the key is rejected (e.g. expired), Esri's keyless World Street Map is used instead.
- Postcode lookup: postcodes.io
- Walking routes: FOSSGIS OSRM foot routing (OpenStreetMap data)
