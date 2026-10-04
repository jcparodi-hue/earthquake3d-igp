import csv,io,json,math,urllib.parse,urllib.request
from datetime import datetime,timedelta,timezone
from pathlib import Path
DAYS=10; MIN_MAG=2.5
IGP="https://raw.githubusercontent.com/IFC-Chalaco/peru-seismic-dashboard/main/seismic_bi_stream/exports/earthquakes_live_curated.csv"
EMSC="https://www.seismicportal.eu/fdsnws/event/1/query"; USGS="https://earthquake.usgs.gov/fdsnws/event/1/query"
D=Path("docs"); HIST=D/"igp_historico.csv"; COMB=D/"igp_7dias_eq3d.csv"; IGP_OUT=D/"igp_solo_10dias_eq3d.csv"; STATUS=D/"estado_fuentes.json"; DUP=D/"duplicados.csv"; REJ=D/"eventos_rechazados.csv"; LATEST=D/"ultima_actualizacion.txt"
A={"time":["event_ts_utc","datetime_utc","fecha_hora_utc","timestamp_utc","time","datetime","fecha_hora"],"date":["event_date_utc","fecha_utc","date","fecha"],"clock":["event_time_utc","hora_utc","hour","hora"],"dep":["prof","depth_km","depth","profundidad_km"],"mag":["magnitude","mag","magnitud"],"lat":["latitude","lat","latitud"],"lon":["longitude","lon","long","longitud"],"url":["url","event_url","source_url","detail_url","enlace"],"id":["event_code","code","codigo","codigo_reporte","id"],"place":["place","referencia","reference","location","lugar"]}
REJECTED=[]
def fetch(url):
 r=urllib.request.Request(url,headers={"User-Agent":"GEOPOWER-PULSE/5.1"}); return urllib.request.urlopen(r,timeout=90).read().decode("utf-8-sig")
def pick(row,names):
 low={str(k).strip().lower():v for k,v in row.items()}
 for n in names:
  if low.get(n) is not None and str(low[n]).strip(): return str(low[n]).strip()
 return ""
def dtparse(raw):
 raw=str(raw).replace("Z","+00:00")
 for f in (None,"%Y-%m-%d %H:%M:%S","%d/%m/%Y %H:%M:%S","%Y-%m-%d %H:%M","%d/%m/%Y %H:%M"):
  try:
   d=datetime.fromisoformat(raw) if f is None else datetime.strptime(raw,f); return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
  except: pass
 raise ValueError("fecha no reconocida")
def ev(dt,dep,mag,lat,lon,url,src,eid="",country="",place=""): return {"dt":dt,"dep":float(dep),"mag":float(mag),"lat":float(lat),"lon":float(lon),"url":url,"source":src,"id":eid,"country":country,"place":place}
def load_igp(cut):
 out=[]
 for r in csv.DictReader(io.StringIO(fetch(IGP))):
  try:
   raw=pick(r,A["time"]) or (pick(r,A["date"])+" "+pick(r,A["clock"])).strip(); d=dtparse(raw)
   if d<cut: continue
   eid=pick(r,A["id"]); url=pick(r,A["url"]) or (("https://ultimosismo.igp.gob.pe/evento/"+eid) if eid else "https://ultimosismo.igp.gob.pe/")
   out.append(ev(d,pick(r,A["dep"]),pick(r,A["mag"]),pick(r,A["lat"]),pick(r,A["lon"]),url,"IGP",eid,"Perú",pick(r,A["place"])))
  except Exception as x: print("IGP omitido",x)
 return out
def api_url(base,cut):
 p={"format":"geojson" if "usgs" in base else "json","starttime":cut.strftime("%Y-%m-%dT%H:%M:%S"),"endtime":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),"minmagnitude":MIN_MAG,"orderby":"time","limit":20000}
 if "seismicportal" in base:p["catalog"]="EMSC-RTS"
 return base+"?"+urllib.parse.urlencode(p)
def reject(src,f,why):
 p=f.get("properties",{}) or {}; c=(f.get("geometry",{}) or {}).get("coordinates",[]) or []
 REJECTED.append({"fecha_consulta_utc":datetime.now(timezone.utc).isoformat(),"fuente":src,"id":str(f.get("id") or p.get("unid") or p.get("source_id") or ""),"fecha_evento":str(p.get("time") or ""),"magnitud":str(p.get("mag") if p.get("mag") is not None else ""),"latitud":str(c[1] if len(c)>1 else ""),"longitud":str(c[0] if c else ""),"motivo_rechazo":why})
def load_api(base,src,cut):
 out=[]; data=json.loads(fetch(api_url(base,cut)))
 for f in data.get("features",[]):
  try:
   p=f.get("properties",{}) or {}; c=(f.get("geometry",{}) or {}).get("coordinates",[]); lon,lat=float(c[0]),float(c[1]); dep=p.get("depth") if p.get("depth") is not None else c[2]; mag=p.get("mag"); raw=p.get("time")
   d=datetime.fromtimestamp(raw/1000,tz=timezone.utc) if isinstance(raw,(int,float)) else dtparse(raw)
   if d<cut: reject(src,f,"evento anterior a la ventana"); continue
   if mag is None: reject(src,f,"magnitud ausente"); continue
   eid=str(f.get("id") or p.get("unid") or p.get("source_id") or ""); url=p.get("url") or (("https://earthquake.usgs.gov/earthquakes/eventpage/"+eid) if src=="USGS" else "https://www.emsc-csem.org/Earthquake_information/earthquake.php?id="+eid); place=str(p.get("place") or p.get("flynn_region") or "")
   out.append(ev(d,dep,mag,lat,lon,url,src,eid,"",place))
  except Exception as x: reject(src,f,"error de lectura: "+str(x)); print(src,"omitido",x)
 return out
def valid(e,now): return -90<=e["lat"]<=90 and -180<=e["lon"]<=180 and 0<=e["dep"]<=800 and -1<=e["mag"]<=10 and e["dt"]<=now+timedelta(minutes=5)
def load_hist():
 if not HIST.exists(): return []
 out=[]
 for r in csv.DictReader(HIST.open(encoding="utf-8-sig")):
  try: out.append(ev(dtparse(r["datetime_utc"]),r["depth_km"],r["magnitude"],r["latitude"],r["longitude"],r.get("url",""),"IGP",r.get("id",""),r.get("country","Perú"),r.get("place","")))
  except Exception as x: print("histórico omitido",x)
 return out
def hkey(e): return "id:"+str(e["id"]) if e.get("id") else e["dt"].strftime("%Y%m%d%H%M%S")+f':{e["lat"]:.4f}:{e["lon"]:.4f}'
def save_hist(es):
 fs=["id","datetime_utc","depth_km","magnitude","latitude","longitude","country","place","url","source"]
 with HIST.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fs);w.writeheader()
  for e in sorted(es,key=lambda x:x["dt"],reverse=True):w.writerow({"id":e["id"],"datetime_utc":e["dt"].isoformat(),"depth_km":e["dep"],"magnitude":e["mag"],"latitude":e["lat"],"longitude":e["lon"],"country":e["country"],"place":e["place"],"url":e["url"],"source":"IGP"})
def km(a,b):
 r=6371;p1,p2=map(math.radians,[a["lat"],b["lat"]]);dp=math.radians(b["lat"]-a["lat"]);dl=math.radians(b["lon"]-a["lon"]);h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*r*math.asin(min(1,math.sqrt(h)))
def same(a,b): return abs((a["dt"]-b["dt"]).total_seconds())<=120 and km(a,b)<=50 and abs(a["mag"]-b["mag"])<=.5
def dedupe(groups):
 kept=[];removed=[]
 for g in groups:
  for e in sorted(g,key=lambda x:x["dt"],reverse=True):
   m=next((o for o in kept if same(e,o)),None)
   if not m:kept.append(e)
   else:removed.append({"kept_source":m["source"],"kept_id":m["id"],"removed_source":e["source"],"removed_id":e["id"],"time_difference_seconds":round(abs((e["dt"]-m["dt"]).total_seconds())),"distance_km":round(km(e,m),2),"magnitude_difference":round(abs(e["mag"]-m["mag"]),2)})
 return sorted(kept,key=lambda x:x["dt"],reverse=True),removed
def write_eq(path,es,head):
 with path.open("w",encoding="utf-8",newline="") as f:
  f.write(head+"\n");w=csv.writer(f,lineterminator="\n")
  for e in es:
   d=e["dt"];w.writerow([d.year,d.month,d.day,f"{d.hour:02d}",f"{d.minute:02d}",e["dep"],e["mag"],f'{e["lat"]:.6f}',f'{e["lon"]:.6f}',10,e["url"]])
def health(es,received,invalid,now):
 n=max((e["dt"] for e in es),default=None);age=(now-n).total_seconds()/60 if n else None
 return {"estado_fuente":"DISPONIBLE" if received>0 else "SIN_DATOS","actividad":"SIN_EVENTOS_EN_VENTANA" if n is None else ("EVENTO_RECIENTE" if age<=1440 else "SIN_EVENTOS_RECIENTES"),"eventos_validos":len(es),"eventos_recibidos":received,"invalidos_rechazados":invalid,"evento_mas_reciente_utc":n.isoformat() if n else None,"antiguedad_evento_mas_reciente_min":round(age,1) if age is not None else None}
def latest(es):
 if not es:return None
 e=max(es,key=lambda x:x["dt"]);return {"id":e["id"],"fecha_hora_utc":e["dt"].isoformat(),"magnitud":e["mag"],"profundidad_km":e["dep"],"latitud":e["lat"],"longitud":e["lon"],"pais":e["country"],"ciudad_referencia":e["place"],"fuente":e["source"],"url":e["url"]}
def write_csv(path,fields,rows):
 with path.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 D.mkdir(exist_ok=True);now=datetime.now(timezone.utc);cut=now-timedelta(days=DAYS)
 ri=load_igp(cut);re=load_api(EMSC,"EMSC",cut);ru=load_api(USGS,"USGS",cut);ci=[e for e in ri if valid(e,now)];em=[e for e in re if valid(e,now)];us=[e for e in ru if valid(e,now)]
 hist={hkey(e):e for e in load_hist() if valid(e,now)}
 for e in ci:hist[hkey(e)]=e
 ih=sorted(hist.values(),key=lambda x:x["dt"],reverse=True);save_hist(ih);combined,removed=dedupe([ih,em,us])
 if len(combined)<10:raise SystemExit("muy pocos eventos; se conserva el archivo anterior")
 write_eq(COMB,combined,"YEAR, MON, DAY, HOUR, MIN, DEP, MAG, LAT, LONG, URL   // IGP history + EMSC-RTS + USGS, global rolling 10 days");write_eq(IGP_OUT,ih,"YEAR, MON, DAY, HOUR, MIN, DEP, MAG, LAT, LONG, URL   // IGP Peru cumulative history")
 hs={"igp":health(ih,len(ri),len(ri)-len(ci),now),"emsc":health(em,len(re),len(re)-len(em),now),"usgs":health(us,len(ru),len(ru)-len(us),now)}
 st={"estado":"OK","actualizado_utc":now.isoformat(),"periodo_mundial_dias":DAYS,"igp_historico":len(ih),"actualizacion_minutos":5,"igp":len(ih),"emsc":len(em),"usgs":len(us),"duplicados_eliminados":len(removed),"eventos_publicados":len(combined),"evento_mas_reciente_utc":combined[0]["dt"].isoformat(),"salud_fuentes":hs,"ultimo_evento":{"igp":latest(ih),"emsc":latest(em),"usgs":latest(us)},"auditoria":{"catalogo_emsc":"EMSC-RTS","eventos_rechazados_registrados":len(REJECTED),"hora_consulta_utc":now.isoformat()}}
 st.update({"status":"OK","updated_utc":st["actualizado_utc"],"combined_after_dedup":len(combined)});STATUS.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding="utf-8");LATEST.write_text(f"Generado UTC: {now.isoformat()}\nIGP histórico: {len(ih)}\nEventos publicados: {len(combined)}\n",encoding="utf-8")
 write_csv(DUP,["kept_source","kept_id","removed_source","removed_id","time_difference_seconds","distance_km","magnitude_difference"],removed);write_csv(REJ,["fecha_consulta_utc","fuente","id","fecha_evento","magnitud","latitud","longitud","motivo_rechazo"],REJECTED)
 print(f"IGP_history={len(ih)} EMSC={len(em)} USGS={len(us)} rejected={len(REJECTED)} combined_after_dedup={len(combined)}")
if __name__=="__main__":main()
