import csv, io, json, math, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DAYS = 10
MIN_MAG_GLOBAL = 2.5
IGP_SOURCE = "https://raw.githubusercontent.com/IFC-Chalaco/peru-seismic-dashboard/main/seismic_bi_stream/exports/earthquakes_live_curated.csv"
USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
EMSC_API = "https://www.seismicportal.eu/fdsnws/event/1/query"
OUT_COMBINED = Path("docs/igp_7dias_eq3d.csv")  # Same URL already configured in EQ3D
OUT_IGP_ONLY = Path("docs/igp_solo_10dias_eq3d.csv")
HEADER = "YEAR, MON, DAY, HOUR, MIN, DEP, MAG, LAT, LONG, URL   // IGP + EMSC + USGS, rolling 10 days"

ALIASES = {
    "time": ["event_ts_utc","datetime_utc","fecha_hora_utc","timestamp_utc","time","datetime","fecha_hora"],
    "date": ["event_date_utc","fecha_utc","date","fecha"],
    "clock": ["event_time_utc","hora_utc","hour","hora"],
    "depth": ["prof","depth_km","depth","profundidad_km"],
    "mag": ["magnitude","mag","magnitud"],
    "lat": ["latitude","lat","latitud"],
    "lon": ["longitude","lon","long","longitud"],
    "url": ["url","event_url","source_url","detail_url","enlace"],
    "code": ["event_code","code","codigo","codigo_reporte","id"],
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"EQ3D-IGP-World/2.0 (public educational feed)"})
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8-sig")

def pick(row, names):
    lower = {str(k).strip().lower(): v for k, v in row.items()}
    for n in names:
        v = lower.get(n)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return ""

def num(value):
    return float(str(value).replace(",", ".").strip())

def parse_dt(row):
    raw = pick(row, ALIASES["time"])
    if not raw:
        raw = (pick(row, ALIASES["date"]) + " " + pick(row, ALIASES["clock"])).strip()
    raw = raw.replace("Z", "+00:00")
    formats = [None, "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"]
    for fmt in formats:
        try:
            dt = datetime.fromisoformat(raw) if fmt is None else datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except Exception:
            pass
    raise ValueError("Fecha no reconocida: " + raw)

def event(dt, dep, mag, lat, lon, url, source, eid=""):
    return {"dt":dt, "dep":float(dep), "mag":float(mag), "lat":float(lat), "lon":float(lon),
            "url":url, "source":source, "id":eid}

def load_igp(cutoff):
    rows = csv.DictReader(io.StringIO(fetch(IGP_SOURCE)))
    out = []
    for row in rows:
        try:
            dt = parse_dt(row)
            if dt < cutoff: continue
            code = pick(row, ALIASES["code"])
            url = pick(row, ALIASES["url"]) or (("https://ultimosismo.igp.gob.pe/evento/" + code) if code else "https://ultimosismo.igp.gob.pe/")
            out.append(event(dt, num(pick(row,ALIASES["depth"])), num(pick(row,ALIASES["mag"])),
                             num(pick(row,ALIASES["lat"])), num(pick(row,ALIASES["lon"])), url, "IGP", code))
        except Exception as exc:
            print("IGP row skipped:", exc)
    return out

def api_url(base, cutoff):
    params = {"format":"geojson" if "usgs" in base else "json",
              "starttime":cutoff.strftime("%Y-%m-%dT%H:%M:%S"),
              "endtime":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
              "minmagnitude":MIN_MAG_GLOBAL, "orderby":"time", "limit":20000}
    return base + "?" + urllib.parse.urlencode(params)

def load_geojson(base, source, cutoff):
    data = json.loads(fetch(api_url(base, cutoff)))
    out = []
    for f in data.get("features", []):
        try:
            p = f.get("properties", {}) or {}
            coords = (f.get("geometry", {}) or {}).get("coordinates", [])
            lon, lat = float(coords[0]), float(coords[1])
            dep = p.get("depth")
            if dep is None:
                dep = coords[2]
                if source == "EMSC" and float(dep) < 0 and abs(float(dep)) > 1000:
                    dep = abs(float(dep))/1000.0
            mag = p.get("mag")
            raw_time = p.get("time")
            if isinstance(raw_time, (int,float)):
                dt = datetime.fromtimestamp(raw_time/1000.0, tz=timezone.utc)
            else:
                dt = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00")).astimezone(timezone.utc)
            if dt < cutoff or mag is None: continue
            eid = str(f.get("id") or p.get("unid") or p.get("source_id") or "")
            if source == "USGS":
                url = p.get("url") or ("https://earthquake.usgs.gov/earthquakes/eventpage/" + eid)
            else:
                url = p.get("url") or ("https://www.emsc-csem.org/Earthquake_information/earthquake.php?id=" + eid)
            out.append(event(dt, dep, mag, lat, lon, url, source, eid))
        except Exception as exc:
            print(source, "row skipped:", exc)
    return out

def haversine_km(a, b):
    r = 6371.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = math.radians(b["lat"]-a["lat"])
    dl = math.radians(b["lon"]-a["lon"])
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1, math.sqrt(h)))

def duplicate(a, b):
    return (abs((a["dt"]-b["dt"]).total_seconds()) <= 120
            and haversine_km(a,b) <= 50
            and abs(a["mag"]-b["mag"]) <= 0.5)

def dedupe(groups):
    kept = []
    # Priority: IGP first, then EMSC, then USGS. This favors Peru's official report and EMSC coverage.
    for group in groups:
        for ev in sorted(group, key=lambda x:x["dt"], reverse=True):
            if not any(duplicate(ev, old) for old in kept):
                kept.append(ev)
    return sorted(kept, key=lambda x:x["dt"], reverse=True)

def write_eq3d(path, events, header=HEADER):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(header + "\n")
        w = csv.writer(f, lineterminator="\n")
        for e in events:
            d=e["dt"]
            w.writerow([d.year,d.month,d.day,f"{d.hour:02d}",f"{d.minute:02d}",f'{e["dep"]:g}',f'{e["mag"]:g}',
                        f'{e["lat"]:.6f}',f'{e["lon"]:.6f}',10,e["url"]])

def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
    igp = load_igp(cutoff)
    emsc = load_geojson(EMSC_API, "EMSC", cutoff)
    usgs = load_geojson(USGS_API, "USGS", cutoff)
    combined = dedupe([igp, emsc, usgs])
    write_eq3d(OUT_COMBINED, combined)
    write_eq3d(OUT_IGP_ONLY, sorted(igp,key=lambda x:x["dt"],reverse=True),
               "YEAR, MON, DAY, HOUR, MIN, DEP, MAG, LAT, LONG, URL   // IGP Peru, rolling 10 days")
    print(f"IGP={len(igp)} EMSC={len(emsc)} USGS={len(usgs)} combined_after_dedup={len(combined)}")
    if not combined:
        raise SystemExit("No events generated")

if __name__ == "__main__":
    main()
