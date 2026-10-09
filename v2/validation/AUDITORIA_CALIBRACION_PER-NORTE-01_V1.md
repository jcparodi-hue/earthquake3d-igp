# EARTHQUAKE 3D v2.0 - Auditoria de calibracion PER-NORTE-01 V1

## Alcance

- Motor: V1.1
- Periodo: 1980-01-01 a 2009-12-31
- Filas procesadas: 10977
- Validacion abierta: no
- Holdout abierto: no
- Forecast operativo: deshabilitado

## Auditoria de distancias

No existen valores nulos en las columnas de distancia.

### Eventos objetivo M4.5+ proximos a PER-NORTE-01

- 50 km: 0
- 100 km: 2
- 150 km: 8

Los ocho eventos dentro de 150 km fueron someros, con profundidades entre 11 y 33 km. El evento objetivo mas cercano fue IGP-8C0174A79AD7, del 1980-02-19, M5.1, profundidad 33 km, a 80.531 km del corredor.

### Disparadores principales

Criterio: M4.5+, profundidad igual o mayor a 300 km.

- Eventos en todo el catalogo de calibracion: 44
- Eventos dentro de 150 km del corredor: 0
- Distancia minima al corredor: 1164.993 km
- Evento mas cercano: IGP-D1941201047B, 2009-01-29, M5.8, profundidad 690 km

### Disparadores exploratorios

Criterio: M4.5+, profundidad desde 200 km hasta menos de 300 km.

- Eventos en todo el catalogo de calibracion: 42
- Eventos dentro de 150 km del corredor: 0
- Distancia minima al corredor: 1214.554 km
- Evento mas cercano: IGP-3FB699D09366, 1991-03-21, M4.8, profundidad 206 km

### Control C0

- Eventos objetivo M4.5+ dentro de 150 km: 0
- Distancia minima de un evento objetivo al control: 207.723 km

## Resultado

- PRIMARY: 0 forecasts
- EXPLORATORY: 0 forecasts
- B1: 0 hits; todas las ventanas fueron falsas alarmas
- B0: tasa historica muy baja cerca del corredor
- C0: sin eventos objetivo dentro de las bandas

## Interpretacion

La ejecucion fue tecnicamente consistente, pero la regla espacial congelada para los disparadores no produjo ninguna oportunidad de prueba. Los sismos profundos e intermedios del catalogo de calibracion se localizaron a mas de 1100 km de PER-NORTE-01. Por tanto, V1 es no informativa para evaluar la hipotesis de transferencia hacia el corredor.

Esto no prueba ni refuta la hipotesis de Dutchsinse. Demuestra que exigir que el disparador profundo ocurra a menos de 150 km del corredor no representa adecuadamente una hipotesis en la que el origen puede encontrarse lejos y la actividad se propone trasladar por una ruta.

## Decision recomendada

- Conservar V1 como prueba nula documentada.
- No abrir validacion ni holdout con V1.
- No cambiar silenciosamente las reglas V1.
- Diseñar un protocolo V2 usando solo informacion de calibracion, con una regla de origen remoto y conectividad geograficamente definida antes de abrir 2010-2019.
- Redisenar C0 porque el control actual no contiene eventos objetivo y no es informativo.

## Seguridad

- historical_validation: NOT_STARTED
- enabled_for_forecast: false
- public_alert_capability: false
- merge_to_main: false
