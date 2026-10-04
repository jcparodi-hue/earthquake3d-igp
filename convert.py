import csv, io, json, math, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DAYS = 10
MIN_MAG_GLOBAL = 2.5
IGP_SOURCE = "https://raw.githubusercontent.com/IFC-Chalaco/peru-seismic-dashboard/main/seismic_bi_stream/exports/earthquakes_live_curated.csv"
USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
EMSC_API = "https://www.seismicportal.eu/fdsnws/event/1/query"
OUT_COMBINED = Path("docs/igp_7dias_eq3d.csv")
OUT_IGP_ONLY = Path("docs/igp_solo_10dias_eq3d.csv")
OUT_STATUS = Path("docs/estado_fuentes.json")
OUT_LATEST = Path("docs/ultima_actualizacion.txt")
OUT_DUPLICATES = Path("docs/duplicados.csv")
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
    req = urllib.request.Request(url, headers={"User-Agent":"GEOPOWER-PULSE/3.0"})
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8-sig")

def pick(row, names):
    lower={str(k).strip().lower():v for k,v in row.items()}
    for name in names:
        v=lower.get(name)
        if v is not None and str(v).strip(): return str(v).strip()
    return ""

def num(v): return float(str(v).replace(",", ".").strip())

def parse_dt(row):
    raw=pick(row,ALIASES["time"]) or (pick(row,ALIASES["date"])+" "+pick(row,ALIASES["clock"])).strip()
    raw=raw.replace("Z","+00:00")
    for fmt in (None,"%Y-%m-%d %H:%M:%S","%d/%m/%Y %H:%M:%S","%Y-%m-%d %H:%M","%d/%m/%Y %H:%M"):
        try:
            dt=datetime.fromisoformat(raw) if fmt is None else datetime.strptime(raw,fmt)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except Exception: pass
    raise ValueError("Fecha no reconocida: "+raw)

def event(dt,dep,mag,lat,lon,url,source,eid=""):
    return {"dt":dt,"dep":float(dep),"mag":float(mag),"lat":float(lat),"lon":float(lon),"url":url,"source":source,"id":eid}

def load_igp(cutoff):
    out=[]
    for row in csv.DictReader(io.StringIO(fetch(IGP_SOURCE))):
        try:
            dt=parse_dt(row)
            if dt<cutoff: continue
            code=pick(row,ALIASES["code"])
            url=pick(row,ALIASES["url"]) or (("https://ultimosismo.igp.gob.pe/evento/"+code) if code else "https://ultimosismo.igp.gob.pe/")
            out.append(event(dt,num(pick(row,ALIASES["depth"])),num(pick(row,ALIASES["mag"])),num(pick(row,ALIASES["lat"])),num(pick(row,ALIASES["lon"])),url,"IGP",code))
        except Exception as exc: print("IGP row skipped:",exc)
    return out

def api_url(base,cutoff):
    params={"format":"geojson" if "usgs" in base else "json","starttime":cutoff.strftime("%Y-%m-%dT%H:%M:%S"),"endtime":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),"minmagnitude":MIN_MAG_GLOBAL,"orderby":"time","limit":20000}
    return base+"?"+urllib.parse.urlencode(params)

def load_geojson(base,source,cutoff):
    data=json.loads(fetch(api_url(base,cutoff))); out=[]
    for f in data.get("features",[]):
        try:
            props=f.get("properties",{}) or {}; coords=(f.get("geometry",{}) or {}).get("coordinates",[])
            lon,lat=float(coords[0]),float(coords[1]); dep=props.get("depth")
            if dep is None: dep=coords[2]
            mag=props.get("mag"); raw=props.get("time")
            dt=datetime.fromtimestamp(raw/1000.0,tz=timezone.utc) if isinstance(raw,(int,float)) else datetime.fromisoformat(str(raw).replace("Z","+00:00")).astimezone(timezone.utc)
            if dt<cutoff or mag is None: continue
            eid=str(f.get("id") or props.get("unid") or props.get("source_id") or "")
            url=props.get("url") or (("https://earthquake.usgs.gov/earthquakes/eventpage/"+eid) if source=="USGS" else "https://www.emsc-csem.org/Earthquake_information/earthquake.php?id="+eid)
            out.append(event(dt,dep,mag,lat,lon,url,source,eid))
        except Exception as exc: print(source,"row skipped:",exc)
    return out

def haversine_km(a,b):
    r=6371.0; p1,p2=math.radians(a["lat"]),math.radians(b["lat"]); dp=math.radians(b["lat"]-a["lat"]); dl=math.radians(b["lon"]-a["lon"])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1,math.sqrt(h)))

def valid_event(e,now):
    return -90<=e["lat"]<=90 and -180<=e["lon"]<=180 and 0<=e["dep"]<=800 and -1<=e["mag"]<=10 and e["dt"]<=now+timedelta(minutes=5)

def duplicate(a,b):
    return abs((a["dt"]-b["dt"]).total_seconds())<=120 and haversine_km(a,b)<=50 and abs(a["mag"]-b["mag"])<=0.5

def dedupe(groups):
    kept=[]; removed=[]
    for group in groups:
        for ev in sorted(group,key=lambda x:x["dt"],reverse=True):
            match=next((old for old in kept if duplicate(ev,old)),None)
            if match is None: kept.append(ev)
            else: removed.append({"kept_source":match["source"],"kept_id":match["id"],"removed_source":ev["source"],"removed_id":ev["id"],"time_difference_seconds":round(abs((ev["dt"]-match["dt"]).total_seconds())),"distance_km":round(haversine_km(ev,match),2),"magnitude_difference":round(abs(ev["mag"]-match["mag"]),2)})
    return sorted(kept,key=lambda x:x["dt"],reverse=True),removed

def write_eq3d(path,events,header=HEADER):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        f.write(header+"\n"); w=csv.writer(f,lineterminator="\n")
        for e in events:
            d=e["dt"]; w.writerow([d.year,d.month,d.day,f"{d.hour:02d}",f"{d.minute:02d}",f'{e["dep"]:g}',f'{e["mag"]:g}',f'{e["lat"]:.6f}',f'{e["lon"]:.6f}',10,e["url"]])

def write_audit(status,duplicates):
    OUT_STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding="utf-8")
    OUT_LATEST.write_text(f"Generado UTC: {status['updated_utc']}\nPeriodo: {DAYS} dias\nFuentes: IGP, EMSC, USGS\nEventos publicados: {status['combined_after_dedup']}\nEstado: {status['status']}\n",encoding="utf-8")
    with OUT_DUPLICATES.open("w",encoding="utf-8",newline="") as f:
        fields=["kept_source","kept_id","removed_source","removed_id","time_difference_seconds","distance_km","magnitude_difference"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(duplicates)

def main():
    now=datetime.now(timezone.utc); cutoff=now-timedelta(days=DAYS)
    raw_igp=load_igp(cutoff); raw_emsc=load_geojson(EMSC_API,"EMSC",cutoff); raw_usgs=load_geojson(USGS_API,"USGS",cutoff)
    igp=[e for e in raw_igp if valid_event(e,now)]; emsc=[e for e in raw_emsc if valid_event(e,now)]; usgs=[e for e in raw_usgs if valid_event(e,now)]
    combined,removed=dedupe([igp,emsc,usgs])
    if len(combined)<10: raise SystemExit("Actualizacion rechazada: muy pocos eventos validos; se conserva el archivo anterior")
    write_eq3d(OUT_COMBINED,combined)
    write_eq3d(OUT_IGP_ONLY,sorted(igp,key=lambda x:x["dt"],reverse=True),"YEAR, MON, DAY, HOUR, MIN, DEP, MAG, LAT, LONG, URL   // IGP Peru, rolling 10 days")
    status={"estado":"OK","actualizado_utc":now.isoformat(),"periodo_dias":DAYS,"actualizacion_minutos":5,"igp":len(igp),"emsc":len(emsc),"usgs":len(usgs),"duplicados_eliminados":len(removed),"eventos_publicados":len(combined),"evento_mas_reciente_utc":combined[0]["dt"].isoformat(),"invalidos_rechazados":{"igp":len(raw_igp)-len(igp),"emsc":len(raw_emsc)-len(emsc),"usgs":len(raw_usgs)-len(usgs)}}
    # English aliases retained for compatibility with future dashboard versions.
    status["status"]=status["estado"]; status["updated_utc"]=status["actualizado_utc"]; status["combined_after_dedup"]=status["eventos_publicados"]
    write_audit(status,removed)
    print(f"IGP={len(igp)} EMSC={len(emsc)} USGS={len(usgs)} duplicates={len(removed)} combined_after_dedup={len(combined)}")

if __name__=="__main__": main()
