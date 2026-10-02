import csv, io, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/IFC-Chalaco/peru-seismic-dashboard/main/seismic_bi_stream/exports/earthquakes_live_curated.csv"
OUT = Path("docs/igp_7dias_eq3d.csv")
HEADER = "YEAR, MON, DAY, HOUR, MIN, DEP, MAG, LAT, LONG, URL   // CSV Feed Source: IGP CENSIS Peru 7 Day"

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

def pick(row, names):
    lower={str(k).strip().lower(): v for k,v in row.items()}
    for n in names:
        v=lower.get(n)
        if v is not None and str(v).strip() != "": return str(v).strip()
    return ""

def number(s):
    return float(str(s).replace(",", ".").strip())

def parse_dt(row):
    raw=pick(row,ALIASES["time"])
    if not raw:
        raw=(pick(row,ALIASES["date"])+" "+pick(row,ALIASES["clock"])).strip()
    raw=raw.replace("Z","+00:00")
    for fn in (
        lambda: datetime.fromisoformat(raw),
        lambda: datetime.strptime(raw,"%Y-%m-%d %H:%M:%S"),
        lambda: datetime.strptime(raw,"%d/%m/%Y %H:%M:%S"),
        lambda: datetime.strptime(raw,"%Y-%m-%d %H:%M"),
        lambda: datetime.strptime(raw,"%d/%m/%Y %H:%M"),
    ):
        try:
            dt=fn()
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except Exception: pass
    raise ValueError("Fecha no reconocida: "+raw)

def main():
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"EQ3D-IGP/1.0"})
    text=urllib.request.urlopen(req,timeout=60).read().decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(text)))
    cutoff=datetime.now(timezone.utc)-timedelta(days=7)
    out=[]; errors=[]
    for row in rows:
        try:
            dt=parse_dt(row)
            if dt < cutoff: continue
            dep=number(pick(row,ALIASES["depth"]))
            mag=number(pick(row,ALIASES["mag"]))
            lat=number(pick(row,ALIASES["lat"]))
            lon=number(pick(row,ALIASES["lon"]))
            url=pick(row,ALIASES["url"])
            if not url:
                code=pick(row,ALIASES["code"])
                url=("https://ultimosismo.igp.gob.pe/evento/"+code) if code else "https://ultimosismo.igp.gob.pe/"
            out.append((dt,dep,mag,lat,lon,url))
        except Exception as e:
            errors.append(str(e))
    out.sort(key=lambda x:x[0],reverse=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:
        f.write(HEADER+"\n")
        w=csv.writer(f,lineterminator="\n")
        for dt,dep,mag,lat,lon,url in out:
            # EQ3D export contains the constant 10 before URL although the header omits it.
            w.writerow([dt.year,dt.month,dt.day,f"{dt.hour:02d}",f"{dt.minute:02d}",f"{dep:g}",f"{mag:g}",f"{lat:.6f}",f"{lon:.6f}",10,url])
    print(f"Generated {OUT} with {len(out)} events; skipped {len(errors)} rows")
    if rows and not out:
        print("Available columns:", list(rows[0].keys()))
        print("First errors:", errors[:5])
        raise SystemExit("No valid events generated")
if __name__=="__main__": main()
