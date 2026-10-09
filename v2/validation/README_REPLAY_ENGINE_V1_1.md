# EARTHQUAKE 3D - Motor de replay V1.1

Motor exclusivamente retrospectivo para el periodo de calibracion 1980-2009.

## Correccion V1.1

Un evento que actua como disparador no se cuenta simultaneamente como su propio objetivo ni como falso negativo en la misma corriente de prueba. La ventana se abre despues de evaluar el evento, conforme a la regla TRIGGER_ONLY pre-registrada.

## Entradas requeridas

- `IGP_CENSIS_CATALOGO_NORMALIZADO_1960_2026_V1.xlsx`
- `PER-NORTE-01_DIGITIZATION_V1.geojson`

## Ejecucion

```bat
py earthquake3d_replay_engine_v1_1.py --catalog IGP_CENSIS_CATALOGO_NORMALIZADO_1960_2026_V1.xlsx --corridor PER-NORTE-01_DIGITIZATION_V1.geojson --output replay_calibration_v1_1
```

## Proteccion

- Solo abre 1980-2009 por defecto.
- No abre validacion ni holdout.
- No modifica la geometria V1.
- No activa forecasts.
- No constituye alerta oficial ni prediccion determinista.
