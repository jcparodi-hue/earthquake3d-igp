import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('docs')
OUT.mkdir(exist_ok=True)
USGS_GEOJSON = 'https://volcanoes.usgs.gov/vsc/api/volcanoApi/geojson'
USGS_WORLD = 'https://volcanoes.usgs.gov/vsc/api/volcanoApi/volcanoesGVP'
HEADERS = {'User-Agent': 'GEOPOWER-PULSE-VOLCANO/1.0'}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode('utf-8-sig'))


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
        'fuentes': {
            'inventario': 'USGS volcanoesGVP, basado en identificadores GVP',
            'alertas_usgs': 'USGS Volcano Hazards Program',
            'peru': 'CENVUL/IGP pendiente de integración estructurada',
            'ceniza': 'NOAA/VAAC pendiente de integración estructurada',
        },
        'errores': errors,
    }
    (OUT / 'volcanes_mundiales.json').write_text(json.dumps(world, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'alertas_volcanes_usgs.json').write_text(json.dumps(usgs, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'alertas_volcanes_usgs_elevadas.json').write_text(json.dumps(elevated, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'estado_volcanes.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(state, ensure_ascii=False))
    if state['estado'] != 'OK':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
