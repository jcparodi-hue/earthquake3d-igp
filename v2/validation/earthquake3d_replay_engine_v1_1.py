#!/usr/bin/env python3
"""EARTHQUAKE 3D retrospective replay engine V1.1.
Research-only. No public alert or operational forecast capability.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import pandas as pd
from shapely.geometry import LineString, shape
from shapely.ops import transform
from pyproj import Transformer

UTM = Transformer.from_crs('EPSG:4326','EPSG:32717',always_xy=True)
WINDOWS=(3,7,10); BANDS=(50,100,150)

def load_line(path: Path) -> LineString:
    obj=json.loads(path.read_text(encoding='utf-8'))
    geom=obj['features'][0]['geometry'] if obj.get('type')=='FeatureCollection' else obj.get('geometry',obj)
    line=shape(geom)
    if line.geom_type!='LineString': raise ValueError('Corridor must be one LineString')
    return line

def shift_south(line: LineString, degrees=5.0) -> LineString:
    return LineString([(x,y-degrees) for x,y in line.coords])

def distance_km(lat,lon,line_utm):
    p=transform(UTM.transform, __import__('shapely').geometry.Point(float(lon),float(lat)))
    return p.distance(line_utm)/1000.0

def load_catalog(path: Path) -> pd.DataFrame:
    x=pd.read_excel(path,sheet_name='Catalogo_Normalizado',engine='openpyxl')
    need={'event_id','event_datetime_utc','latitude','longitude','depth_km','magnitude'}
    if not need.issubset(x.columns): raise ValueError(f'Missing columns: {sorted(need-set(x.columns))}')
    x=x[list(need)].copy(); x['event_datetime_utc']=pd.to_datetime(x['event_datetime_utc'],utc=True)
    for c in ['latitude','longitude','depth_km','magnitude']: x[c]=pd.to_numeric(x[c],errors='raise')
    return x.sort_values('event_datetime_utc').reset_index(drop=True)

@dataclass
class Window:
    model:str; band:int; days:int; trigger_id:str; start:pd.Timestamp; end:pd.Timestamp; outcome:str='OPEN'; target_id:str|None=None

def replay_event_triggered(df, model, trigger_mask, target_mag, band, days, dist_col):
    windows=[]; active=None; false_neg=[]
    for r in df.itertuples(index=False):
        t=r.event_datetime_utc; inside=getattr(r,dist_col)<=band; target=(r.magnitude>=target_mag and inside)
        if active is not None and t>active.end:
            active.outcome='FALSE_ALARM' if active.target_id is None else 'HIT'; windows.append(active); active=None
        if target and active is None: false_neg.append(r.event_id)
        elif target and active is not None and t>active.start and active.target_id is None: active.target_id=r.event_id
        is_trigger=bool(trigger_mask.loc[r.Index] if hasattr(r,'Index') else False)
        if is_trigger and active is None:
            active=Window(model,band,days,r.event_id,t,t+pd.Timedelta(days=days))
    if active is not None:
        active.outcome='FALSE_ALARM' if active.target_id is None else 'HIT'; windows.append(active)
    return windows,false_neg

def replay(df, line, outdir, start='1980-01-01', end='2009-12-31'):
    outdir.mkdir(parents=True,exist_ok=True)
    line_utm=transform(UTM.transform,line); control=shift_south(line); control_utm=transform(UTM.transform,control)
    d=df[(df.event_datetime_utc>=pd.Timestamp(start,tz='UTC'))&(df.event_datetime_utc<=pd.Timestamp(end+' 23:59:59',tz='UTC'))].copy()
    d['distance_per_norte_km']=[distance_km(a,b,line_utm) for a,b in zip(d.latitude,d.longitude)]
    d['distance_control_km']=[distance_km(a,b,control_utm) for a,b in zip(d.latitude,d.longitude)]
    allw=[]; summaries=[]
    for corridor,distcol in [('PER_NORTE_01','distance_per_norte_km'),('C0','distance_control_km')]:
      for band in BANDS:
       for days in WINDOWS:
        for model,depthlo,depthhi in [('PRIMARY',300,None),('EXPLORATORY',200,300)]:
          trig=(d.magnitude>=4.5)&(d[distcol]<=150)&(d.depth_km>=depthlo)
          if depthhi is not None: trig &= d.depth_km<depthhi
          # simple chronological loop with explicit indexes
          windows=[]; active=None; false_neg=[]
          for idx,r in d.iterrows():
            t=r.event_datetime_utc
            current_is_trigger=bool(trig.loc[idx])
            target=(r.magnitude>=4.5 and r[distcol]<=band and not current_is_trigger)
            if active is not None and t>active.end:
                active.outcome='HIT' if active.target_id else 'FALSE_ALARM'; windows.append(active); active=None
            if target:
                if active is None: false_neg.append(r.event_id)
                elif t>active.start and active.target_id is None: active.target_id=r.event_id
            if current_is_trigger and active is None:
                active=Window(f'{corridor}_{model}',band,days,r.event_id,t,t+pd.Timedelta(days=days))
          if active is not None:
            active.outcome='HIT' if active.target_id else 'FALSE_ALARM'; windows.append(active)
          hits=sum(w.outcome=='HIT' for w in windows); fa=len(windows)-hits
          summaries.append({'corridor':corridor,'model':model,'band_km':band,'window_days':days,'forecasts':len(windows),'hits':hits,'false_alarms':fa,'false_negatives':len(false_neg),'precision':hits/len(windows) if windows else None,'recall':hits/(hits+len(false_neg)) if hits+len(false_neg) else None})
          allw.extend([w.__dict__ for w in windows])
        # B1 persistence benchmark
        trig=(d.magnitude>=4.5)&(d[distcol]<=band)
        windows=[]; active=None; false_neg=[]
        for idx,r in d.iterrows():
            t=r.event_datetime_utc; target=bool(trig.loc[idx])
            if active is not None and t>active.end:
                active.outcome='HIT' if active.target_id else 'FALSE_ALARM'; windows.append(active); active=None
            if target:
                if active is None: false_neg.append(r.event_id)
                elif t>active.start and active.target_id is None: active.target_id=r.event_id
            if target and active is None: active=Window(f'{corridor}_B1',band,days,r.event_id,t,t+pd.Timedelta(days=days))
        if active is not None: active.outcome='HIT' if active.target_id else 'FALSE_ALARM'; windows.append(active)
        hits=sum(w.outcome=='HIT' for w in windows)
        summaries.append({'corridor':corridor,'model':'B1','band_km':band,'window_days':days,'forecasts':len(windows),'hits':hits,'false_alarms':len(windows)-hits,'false_negatives':len(false_neg),'precision':hits/len(windows) if windows else None,'recall':hits/(hits+len(false_neg)) if hits+len(false_neg) else None})
        allw.extend([w.__dict__ for w in windows])
    # B0 calibration rate, per corridor/band
    years=(pd.Timestamp(end)-pd.Timestamp(start)).days/365.2425
    b0=[]
    for corridor,distcol in [('PER_NORTE_01','distance_per_norte_km'),('C0','distance_control_km')]:
      for band in BANDS:
        n=int(((d.magnitude>=4.5)&(d[distcol]<=band)).sum()); lam=n/(years*365.2425)
        for days in WINDOWS: b0.append({'corridor':corridor,'band_km':band,'window_days':days,'calibration_targets':n,'lambda_per_day':lam,'probability':1-math.exp(-lam*days)})
    pd.DataFrame(summaries).to_csv(outdir/'calibration_summary.csv',index=False)
    pd.DataFrame(allw).to_csv(outdir/'calibration_forecast_windows.csv',index=False)
    d.to_csv(outdir/'calibration_event_distances.csv',index=False)
    pd.DataFrame(b0).to_csv(outdir/'calibration_B0_rates.csv',index=False)
    meta={'engine_version':'V1.1','period':[start,end],'catalog_rows':len(d),'corridor_sha256':hashlib.sha256(json.dumps(list(line.coords)).encode()).hexdigest(),'rules_frozen':True,'validation_opened':False,'holdout_opened':False,'enabled_for_forecast':False}
    (outdir/'calibration_run_manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')

def self_test():
    line=LineString([(-81,-4),(-80,-8)])
    data=pd.DataFrame([
      ['e1','2000-01-01',-5,-80.5,350,5.0],['e2','2000-01-03',-5.1,-80.5,20,4.8],['e3','2000-02-01',-6,-80.5,350,5.0]
    ],columns=['event_id','event_datetime_utc','latitude','longitude','depth_km','magnitude'])
    data.event_datetime_utc=pd.to_datetime(data.event_datetime_utc,utc=True)
    tmp=Path('/mnt/data/_replay_selftest'); replay(data,line,tmp,'2000-01-01','2000-12-31')
    assert (tmp/'calibration_run_manifest.json').exists()
    sm=pd.read_csv(tmp/'calibration_summary.csv')
    row=sm[(sm.corridor=='PER_NORTE_01')&(sm.model=='PRIMARY')&(sm.band_km==150)&(sm.window_days==7)].iloc[0]
    assert row.forecasts >= 1
    assert row.hits >= 1
    print('SELF_TEST_OK_V1_1')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--catalog'); p.add_argument('--corridor'); p.add_argument('--output'); p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test: return self_test()
    if not all([a.catalog,a.corridor,a.output]): p.error('--catalog, --corridor and --output are required')
    replay(load_catalog(Path(a.catalog)),load_line(Path(a.corridor)),Path(a.output))
if __name__=='__main__': main()
