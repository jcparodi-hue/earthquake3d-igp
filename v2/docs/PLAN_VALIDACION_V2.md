# EARTHQUAKE 3D v2.0 - Plan inicial de validacion

## Alcance
Modelo experimental de investigacion. No constituye alerta oficial ni prediccion determinista.

## Objetivo
Comprobar si cada componente mejora el resultado frente a modelos de referencia, sin cambiar retrospectivamente regiones, ventanas ni parametros.

## Modelos a comparar
- B0: tasa historica por region.
- B1: persistencia de actividad reciente.
- M1: proximidad al corredor.
- M2: sismo profundo.
- M3: conversion Rebella.
- M4: punto medio del corredor.
- M5: interseccion de anillos.
- M6: zona silenciosa estadistica.
- M7: variables volcanotectonicas.
- M8: modelo combinado.

## Ventanas iniciales
- Formacion: 48 horas.
- Evaluacion: 168 horas.

## Resultados permitidos
- FULL_HIT
- SPATIAL_TEMPORAL_HIT
- PARTIAL_HIT
- MISS
- FALSE_ALARM
- FALSE_NEGATIVE
- NOT_EVALUATED

## Reglas de integridad
1. Guardar cada forecast antes del resultado.
2. No sobrescribir versiones anteriores.
3. Registrar area vigilada y rango de magnitud.
4. Publicar aciertos y fallos.
5. Evaluar actividad dentro y fuera del corredor.
6. Comparar cada regla de manera independiente antes del modelo combinado.
7. Mantener separados datos oficiales, calculos, reglas experimentales e hipotesis fisicas.

## Metricas iniciales
- Coincidencia temporal.
- Coincidencia espacial.
- Distancia a la region prevista.
- Error de magnitud.
- Falsos positivos.
- Falsos negativos.
- Area total vigilada.
- Ganancia frente al modelo base.

## Fases
1. Verificacion de datos y duplicados.
2. Digitalizacion independiente del mapa.
3. Replay historico sin acceso a eventos futuros.
4. Validacion temporal fuera de muestra.
5. Validacion geografica.
6. Prueba prospectiva con parametros congelados.
