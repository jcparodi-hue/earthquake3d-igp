# GEOPOWER PULSE

**Global Seismic Monitor**  
**INSPIRED BY GIULIA**  
**BORN TO SHAKE. BUILT TO STAND.**

GEOPOWER PULSE es un sistema automatizado de recopilación, validación, deduplicación, conservación y publicación de datos sísmicos. Integra información del Instituto Geofísico del Perú (IGP/CENSIS), el European-Mediterranean Seismological Centre (EMSC) y el U.S. Geological Survey (USGS), y genera archivos compatibles con EARTHQUAKE 3D.

> Proyecto informativo. No constituye una alerta temprana, no predice terremotos y no reemplaza los reportes oficiales de los organismos sismológicos.

## Estado operativo

El sistema se ejecuta automáticamente mediante cron-job.org y GitHub Actions. La programación solicita una actualización cada cinco minutos. La ejecución efectiva puede presentar variaciones por disponibilidad de los servicios externos y de GitHub.

Panel público:

- https://jcparodi-hue.github.io/earthquake3d-igp/

## Fuentes de datos

### IGP / CENSIS

- Fuente prioritaria para los eventos sísmicos del Perú.
- Los eventos peruanos se conservan en un histórico acumulativo.
- Los registros anteriores no se eliminan al superar la ventana mundial de diez días.
- Se conserva el identificador, la fecha y hora UTC, magnitud, profundidad, coordenadas, país, referencia geográfica, URL y fuente.

### EMSC

- Se consulta explícitamente el catálogo de tiempo casi real `EMSC-RTS`.
- Se incluyen eventos de magnitud 2.5 o superior.
- Se conserva una ventana móvil de diez días.
- Se registran eventos recibidos, aceptados y rechazados por problemas de lectura o información incompleta.

### USGS

- Se incluyen eventos de magnitud 2.5 o superior.
- Se conserva una ventana móvil de diez días.
- Se registran datos de magnitud, profundidad, coordenadas, ubicación, identificador y enlace oficial.

## Arquitectura

```text
cron-job.org
      ↓ cada 5 minutos
GitHub Actions
      ↓
convert.py
      ↓
IGP + EMSC-RTS + USGS
      ↓
validación + deduplicación + auditoría
      ↓
archivos operativos + histórico + respaldos
      ↓
GEOPOWER PULSE + EARTHQUAKE 3D
```

## Criterios de procesamiento

### Ventanas temporales

- IGP: histórico acumulativo desde la creación del archivo histórico.
- EMSC: últimos diez días.
- USGS: últimos diez días.

### Magnitud mínima mundial

El monitor mundial utiliza magnitud mínima 2.5 para EMSC y USGS. Este umbral pertenece al monitor operativo y no debe interpretarse como una magnitud de completitud científica.

### Validación

Se rechazan registros con parámetros imposibles o incompletos, entre ellos:

- latitud fuera de -90 a 90;
- longitud fuera de -180 a 180;
- profundidad fuera de 0 a 800 km;
- magnitud fuera de -1 a 10;
- fecha futura por encima de la tolerancia configurada;
- magnitud ausente;
- estructura ilegible.

### Deduplicación

Los eventos equivalentes entre fuentes se comparan mediante tolerancias de:

- tiempo;
- distancia geográfica;
- diferencia de magnitud.

El orden de prioridad es:

```text
IGP → EMSC → USGS
```

Cuando dos fuentes describen el mismo evento, se conserva un único registro en el feed combinado.

## Archivos principales

### Archivos operativos

- `docs/igp_7dias_eq3d.csv`: feed combinado para EARTHQUAKE 3D.
- `docs/igp_solo_10dias_eq3d.csv`: histórico del IGP en formato compatible con EARTHQUAKE 3D.
- `docs/igp_historico.csv`: catálogo acumulativo y estructurado del IGP.
- `docs/estado_fuentes.json`: estado general, salud por fuente, últimos eventos y auditoría.
- `docs/ultima_actualizacion.txt`: resumen textual de la última generación.
- `docs/duplicados.csv`: registros eliminados como duplicados.
- `docs/eventos_rechazados.csv`: eventos rechazados en la última consulta y motivo.
- `docs/historial_actualizaciones.csv`: fotografía acumulativa de cada actualización.
- `docs/index.html`: panel público de GEOPOWER PULSE.

### Respaldos automáticos

- `docs/igp_7dias_eq3d_backup.csv`
- `docs/igp_historico_backup.csv`
- `docs/estado_fuentes_backup.json`

Los respaldos se crean después de una ejecución correcta del conversor.

## Historial de actualizaciones

`docs/historial_actualizaciones.csv` añade una fila por cada ejecución validada e incluye:

- fecha y hora UTC;
- estado general;
- eventos publicados;
- cantidad histórica del IGP;
- cantidades de EMSC y USGS;
- duplicados eliminados;
- identificador del evento más reciente de cada fuente.

Este archivo permite detectar variaciones anormales, reconstruir el comportamiento del sistema y comprobar la continuidad de las fuentes.

## Salud y frescura

El panel consulta `estado_fuentes.json` y muestra:

- estado general del sistema;
- disponibilidad individual de IGP, EMSC y USGS;
- cantidad de eventos por fuente;
- último evento aceptado;
- magnitud, fecha, hora de Lima, profundidad, coordenadas, país, referencia, fuente e identificador.

Indicador de frescura:

```text
Menos de 15 minutos   → SISTEMA OPERATIVO
Entre 15 y 30 minutos → ACTUALIZACIÓN RETRASADA
Más de 30 minutos     → ACTUALIZACIÓN DETENIDA
```

## Automatización

El flujo `.github/workflows/update.yml`:

1. descarga el repositorio;
2. configura Python;
3. ejecuta `convert.py`;
4. registra el historial de actualizaciones;
5. crea respaldos del último conjunto válido;
6. guarda los cambios en la rama `main`;
7. sincroniza la rama antes de publicar para evitar conflictos.

Las ejecuciones simultáneas se mantienen en cola mediante un grupo de concurrencia.

## Restauración controlada

El flujo `.github/workflows/restaurar-respaldos.yml` permite restaurar manualmente los últimos archivos respaldados.

La restauración:

- no se ejecuta automáticamente;
- exige acceso de escritura al repositorio;
- requiere escribir exactamente `RESTAURAR`;
- verifica que los respaldos existan y no estén vacíos;
- no utiliza `git push --force`.

Debe utilizarse únicamente cuando los archivos operativos estén vacíos, dañados o contengan información incorrecta.

## Uso con EARTHQUAKE 3D

Feed mundial combinado:

```text
https://jcparodi-hue.github.io/earthquake3d-igp/igp_7dias_eq3d.csv
```

Histórico IGP compatible:

```text
https://jcparodi-hue.github.io/earthquake3d-igp/igp_solo_10dias_eq3d.csv
```

## Limitaciones

- Las fuentes pueden publicar, revisar, fusionar o retirar eventos.
- La web pública de una fuente y su API pueden no actualizarse exactamente al mismo instante.
- El monitor no representa necesariamente todos los eventos pequeños del planeta.
- Las magnitudes pueden proceder de escalas o redes diferentes.
- El histórico del IGP comenzó con los eventos disponibles al crear `igp_historico.csv`; todavía no contiene por sí solo todo el catálogo histórico oficial del Perú.
- El nombre antiguo de algunos archivos se conserva para mantener compatibilidad, aunque su contenido haya evolucionado.
- El sistema no emite alertas oficiales ni predicciones deterministas.

## Investigación futura

Antes de implementar análisis probabilísticos se deberá:

1. incorporar y documentar el catálogo histórico oficial del IGP;
2. conservar revisiones de magnitud, profundidad, hora y coordenadas;
3. estimar la magnitud de completitud por región y período;
4. evaluar la homogeneidad de escalas de magnitud;
5. controlar cambios en redes y capacidad de detección;
6. separar claramente el monitor operativo del catálogo científico;
7. validar cualquier modelo con datos fuera de muestra;
8. comunicar resultados como probabilidades, no como predicciones exactas de fecha, lugar y magnitud.

## Identidad del proyecto

GEOPOWER PULSE fue desarrollado como un proyecto informativo y tecnológico inspirado por Giulia y su interés por los sismos.

```text
INSPIRED BY GIULIA
BORN TO SHAKE. BUILT TO STAND.
```

## Licencias y atribución

Los datos pertenecen a sus organismos de origen. El uso del repositorio debe respetar las condiciones, licencias y requisitos de atribución publicados por IGP/CENSIS, EMSC y USGS.
