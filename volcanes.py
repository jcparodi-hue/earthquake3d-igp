import json
import urllib.request
import re
from html.parser import HTMLParser
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('docs')
OUT.mkdir(exist_ok=True)
USGS_GEOJSON = 'https://volcanoes.usgs.gov/vsc/api/volcanoApi/geojson'
USGS_WORLD = 'https://volcanoes.usgs.gov/vsc/api/volcanoApi/volcanoesGVP'
CENVUL_BULLETINS = 'https://cenvul.igp.gob.pe/productos/boletines-vulcanologicos'
HEADERS = {'User-Agent': 'GEOPOWER-PULSE-VOLCANO/1.1'}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode('utf-8-sig'))



class TextLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.current_href = None
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current_href = dict(attrs).get('href')
    def handle_endtag(self, tag):
        if tag == 'a':
            self.current_href = None
    def handle_data(self, data):
        text = ' '.join(data.split())
        if text:
            self.parts.append((text, self.current_href))


def fetch_text(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read().decode('utf-8-sig', errors='replace')


def normalize_url(url):
    if not url:
        return ''
    if url.startswith('http'):
        return url
    return 'https://cenvul.igp.gob.pe/' + url.lstrip('/')


def load_cenvul():
    html = fetch_text(CENVUL_BULLETINS)
    parser = TextLinkParser()
    parser.feed(html)
    text = ' '.join(part for part, _ in parser.parts)
    pattern = re.compile(
        r'Volcán:\s*([^#]+?)\s+Código:\s*(IGP/CENVUL-[A-Z]+/BV\s+\d{4}-\d+)\s+'
        r'Fecha de publicación:\s*([^#]+?)\s+Alerta:\s*(Verde|Amarillo|Naranja|Rojo)',
        re.IGNORECASE
    )
    links = {}
    for label, href in parser.parts:
        if href and ('bolet' in label.lower() or 'ver bolet' in label.lower()):
            links.setdefault('next', []).append(normalize_url(href))
    results = []
    seen = set()
    urls = links.get('next', [])
    for idx, match in enumerate(pattern.finditer(text)):
        name = ' '.join(match.group(1).split())
        code = ' '.join(match.group(2).split())
        if code in seen:
            continue
        seen.add(code)
        results.append({
            'volcan': name,
            'codigo_boletin': code,
            'fecha_publicacion': ' '.join(match.group(3).split()),
            'nivel_alerta': match.group(4).capitalize(),
            'url_boletin': urls[idx] if idx < len(urls) else CENVUL_BULLETINS,
            'fuente': 'IGP/CENVUL',
        })
    return results

def normalize_world(data):
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get('volcanoes') or data.get('data') or data.get('features') or []
    else:
        rows = []
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        props = row.get('properties', row)
        geometry = row.get('geometry') or {}
        coordinates = geometry.get('coordinates') or []
        lat = props.get('latitude') or props.get('lat')
        lon = props.get('longitude') or props.get('lon')
        if len(coordinates) >= 2:
            lon, lat = coordinates[0], coordinates[1]
        result.append({
            'id_gvp': str(props.get('vnum') or props.get('volcanoNumber') or props.get('volcanoNum') or props.get('id') or ''),
            'nombre': props.get('volcanoName') or props.get('name') or props.get('volcano') or '',
            'pais': props.get('country') or props.get('state') or props.get('stateName') or '',
            'region': props.get('region') or props.get('volcanicRegion') or '',
            'latitud': lat,
            'longitud': lon,
            'elevacion_m': props.get('elevation') or props.get('summitElevM'),
            'fuente': 'USGS/GVP',
        })
    return result


def normalize_usgs(data):
    result = []
    for feature in data.get('features', []):
        props = feature.get('properties') or {}
        coords = (feature.get('geometry') or {}).get('coordinates') or []
        result.append({
            'id_gvp': str(props.get('vnum') or ''),
            'codigo_usgs': props.get('volcanoCd') or '',
            'nombre': props.get('volcanoName') or '',
            'latitud': coords[1] if len(coords) > 1 else None,
            'longitud': coords[0] if coords else None,
            'observatorio': props.get('obs') or '',
            'region': props.get('region') or '',
            'nivel_alerta': props.get('alertLevel') or 'UNASSIGNED',
            'codigo_aviacion': props.get('colorCode') or 'UNASSIGNED',
            'amenaza_nvews': props.get('nvewsThreat') or '',
            'fecha_alerta': props.get('alertDate'),
            'fecha_color': props.get('colorDate'),
            'resumen_aviso': props.get('noticeSynopsis'),
            'url_aviso': props.get('noticeUrl'),
            'url_volcan': props.get('volcanoUrl'),
            'fuente': 'USGS Volcano Hazards Program',
        })
    return result


def main():
    now = datetime.now(timezone.utc).isoformat()
    errors = []
    try:
        world = normalize_world(fetch_json(USGS_WORLD))
    except Exception as exc:
        world = []
        errors.append(f'Inventario mundial: {exc}')
    try:
        cenvul = load_cenvul()
    except Exception as exc:
        cenvul = []
        errors.append(f'CENVUL/IGP: {exc}')
    try:
        usgs = normalize_usgs(fetch_json(USGS_GEOJSON))
    except Exception as exc:
        usgs = []
        errors.append(f'Alertas USGS: {exc}')

    elevated = [v for v in usgs if v['nivel_alerta'] not in ('NORMAL', 'UNASSIGNED') or v['codigo_aviacion'] not in ('GREEN', 'UNASSIGNED')]
    state = {
        'actualizado_utc': now,
        'estado': 'OK' if world or usgs else 'ERROR',
        'volcanes_mundiales': len(world),
        'volcanes_usgs': len(usgs),
        'volcanes_usgs_elevados': len(elevated),
        'boletines_cenvul': len(cenvul),
        'alertas_cenvul_elevadas': len([v for v in cenvul if v['nivel_alerta'] != 'Verde']),
        'fuentes': {
            'inventario': 'USGS volcanoesGVP, basado en identificadores GVP',
            'alertas_usgs': 'USGS Volcano Hazards Program',
            'peru': 'IGP/CENVUL - boletines vulcanológicos oficiales',
            'ceniza': 'NOAA/VAAC pendiente de integración estructurada',
        },
        'errores': errors,
    }
    (OUT / 'volcanes_mundiales.json').write_text(json.dumps(world, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'boletines_volcanes_peru.json').write_text(json.dumps(cenvul, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'alertas_volcanes_usgs.json').write_text(json.dumps(usgs, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'alertas_volcanes_usgs_elevadas.json').write_text(json.dumps(elevated, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'estado_volcanes.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(state, ensure_ascii=False))
    if state['estado'] != 'OK':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
