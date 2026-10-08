# EARTHQUAKE 3D v2.0 - Evaluacion de segmentacion administrativa de PER-NORTE-01 V1

## Metodo evaluado

NEAREST_COASTAL_DEPARTMENT

## Objetivo

Evaluar si el corredor PER-NORTE-01 V1 podia dividirse de forma reproducible en cuatro segmentos administrativos utilizando el departamento terrestre mas cercano a puntos regulares del corredor.

## Datos utilizados

- Corredor: PER-NORTE-01
- Version geometrica: V1
- Capa de trabajo: PER_NORTE_01_WORKING_UTM17S_V1
- Capa departamental: PER_NORTE_01_DEPARTMENTS_UTM17S_V1
- Departamentos evaluados: Tumbes, Piura, Lambayeque y La Libertad
- Sistema de coordenadas: EPSG:32717 - WGS 84 / UTM zone 17S
- Intervalo de muestreo: 20000 metros
- Cantidad de puntos: 26
- Distancia analizada: 0 a 500000 metros

## Procedimiento

1. Se creo una copia del corredor en EPSG:32717.
2. Se generaron puntos cada 20000 metros.
3. Se proyecto la capa de los cuatro departamentos al mismo sistema metrico.
4. Se uso la herramienta Unir atributos por proximidad.
5. Se copio el campo DEPARTAMEN del poligono terrestre mas cercano.
6. Se revisaron las 26 filas del resultado.

## Resultado

- Puntos asociados correctamente: 26
- Puntos sin asociacion: 0
- Puntos asignados a PIURA: 26
- Puntos asignados a TUMBES: 0
- Puntos asignados a LAMBAYEQUE: 0
- Puntos asignados a LA LIBERTAD: 0
- Transiciones departamentales detectadas: 0

## Interpretacion

El resultado no significa que todo el corredor pertenezca oficialmente a Piura.

El resultado significa que, usando exclusivamente la distancia geometrica entre los puntos marinos del corredor y los poligonos departamentales terrestres, Piura es el poligono mas cercano para los 26 puntos.

Los limites departamentales terrestres no proporcionan una division maritima adecuada para segmentar este corredor.

## Decision

METHOD_REJECTED_FOR_SEGMENTATION

El metodo NEAREST_COASTAL_DEPARTMENT no respalda la division de PER-NORTE-01 V1 en los segmentos S01, S02, S03 y S04.

No se dividira el corredor a ojo.

No se modificara la geometria V1.

No se cambiaran manualmente los valores departamentales.

No se inventaran limites maritimos.

## Capas de evidencia conservadas

- PER_NORTE_01_DEPARTMENTS_V1
- PER_NORTE_01_DEPARTMENTS_UTM17S_V1
- PER_NORTE_01_POINTS_20KM_UTM17S_V1
- PER_NORTE_01_NEAREST_DEPARTMENT_20KM_V1
- PER_NORTE_01_WORKING_UTM17S_V1

## Proximo paso

Investigar un metodo alternativo basado en una fuente independiente y verificable, por ejemplo:

1. Limites maritimos oficiales, si existe una fuente apropiada.
2. Transectos perpendiculares desde limites costeros.
3. Regiones oceanicas construidas mediante una regla predefinida.
4. Mantener PER-NORTE-01 sin segmentos hasta disponer de datos adecuados.

## Estado de seguridad

- review_status: IN_PROGRESS
- historical_validation: NOT_STARTED
- enabled_for_forecast: false
- develop-v2 permanece separado de main

## Advertencia

Modelo experimental. No constituye una alerta oficial, una prediccion determinista ni sustituye la informacion del IGP/CENSIS y otras autoridades competentes.
