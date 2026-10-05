# EARTHQUAKE 3D v2.0 - Criterios de evaluacion

## 1. Alcance

Este documento define, antes de observar los resultados, como se evaluaran los forecasts experimentales de EARTHQUAKE 3D v2.0.

El sistema no constituye una alerta oficial, una prediccion determinista ni sustituye la informacion del IGP/CENSIS y otras autoridades competentes.

## 2. Principio de inmutabilidad

Una vez emitida una version de forecast, no se permite modificar retroactivamente:

- La region vigilada.
- El corredor o segmento seleccionado.
- La fecha y hora de inicio.
- La fecha y hora de vencimiento.
- El rango experimental de magnitud.
- El evento activador.
- Las reglas utilizadas.
- Los parametros del modelo.
- Los criterios de acierto.

Cualquier cambio posterior debe crear una nueva version del forecast y conservar la anterior.

## 3. Ventanas iniciales

- Ventana de formacion: 48 horas anteriores a la emision.
- Ventana de evaluacion: 168 horas desde la emision.
- Zona horaria de almacenamiento: UTC.
- Zona horaria de presentacion: America/Lima.

## 4. Datos obligatorios del forecast

Cada forecast debe registrar como minimo:

- Codigo unico.
- Numero de version.
- Version del modelo.
- Fecha y hora de emision.
- Inicio y fin de vigencia.
- Evento activador.
- Fuente del evento activador.
- Corredor y segmentos vigilados.
- Region administrativa asociada.
- Geometria exacta o metodo para reconstruirla.
- Area total vigilada.
- Magnitud instrumental del activador.
- Profundidad del activador.
- Modelos experimentales aplicados.
- Rango experimental de magnitud.
- Parametros utilizados.
- Justificacion del forecast.
- Advertencia experimental obligatoria.

## 5. Evento objetivo

Un evento solo puede utilizarse para evaluar un forecast cuando:

1. Proviene de una fuente identificada.
2. Tiene fecha, hora, latitud y longitud validas.
3. No es un duplicado de otro registro.
4. No es solamente una revision del mismo evento.
5. Cumple el umbral de magnitud definido antes de la prueba.
6. Ocurre despues de la emision del forecast.
7. Cumple las reglas predefinidas para replicas y sismicidad inducida.

Los umbrales que todavia no hayan sido calibrados permaneceran como `null` y el forecast no se evaluara con criterios inventados posteriormente.

## 6. Dimensiones de evaluacion

### 6.1 Coincidencia temporal

Existe coincidencia temporal cuando el evento objetivo ocurre entre `valid_from_utc` y `valid_to_utc`, incluidos ambos limites.

Un evento anterior a la emision nunca cuenta como acierto.

### 6.2 Coincidencia espacial

Existe coincidencia espacial cuando el evento objetivo:

- Cae dentro de la geometria congelada de la region vigilada; o
- Cumple una tolerancia espacial definida y versionada antes del resultado.

Si la tolerancia espacial permanece en `null`, solo se acepta un evento dentro de la geometria congelada.

### 6.3 Coincidencia de magnitud

Existe coincidencia de magnitud cuando la magnitud observada queda dentro del rango experimental congelado.

La magnitud instrumental, la magnitud Rebella, la magnitud del corredor y la magnitud energetica equivalente deben permanecer separadas.

### 6.4 Compatibilidad con el corredor

Se registraran por separado:

- Distancia perpendicular al corredor.
- Posicion longitudinal sobre el corredor.
- Segmento mas cercano.
- Direccion compatible o incompatible.
- Distancia al nodo D mas cercano.
- Distancia al nodo X mas cercano.

## 7. Clasificacion de resultados

### FULL_HIT

Cumple simultaneamente:

- Coincidencia temporal.
- Coincidencia espacial.
- Coincidencia de magnitud.
- Umbral del evento objetivo.

### SPATIAL_TEMPORAL_HIT

Cumple:

- Coincidencia temporal.
- Coincidencia espacial.

Pero no cumple la magnitud prevista o no existe un rango de magnitud evaluable.

### PARTIAL_HIT

Cumple solo una parte de los criterios predefinidos y debe indicar expresamente cuales cumplio y cuales fallo.

No debe mostrarse publicamente como acierto completo.

### MISS

No existe un evento objetivo que cumpla los criterios del forecast durante la ventana de 168 horas.

### FALSE_ALARM

Se emitio un forecast evaluable y no ocurrio el resultado objetivo dentro de la region, ventana y umbral definidos.

### FALSE_NEGATIVE

Ocurrio un evento objetivo relevante durante el periodo de evaluacion, pero ninguna region activa del modelo lo cubrio.

### NOT_EVALUATED

Se utiliza cuando faltan datos esenciales, la fuente es insuficiente, los parametros requeridos permanecen sin definir o el forecast fue cancelado antes de una evaluacion valida.

## 8. Reajustes

Un nuevo evento puede producir una accion versionada:

- `MAINTAIN`: conserva region y vencimiento.
- `CONFIRM`: registra evidencia compatible sin borrar la version anterior.
- `DISPLACE`: mueve la region en una version nueva.
- `SPLIT`: divide el escenario en dos o mas regiones nuevas.
- `CANCEL`: cancela la version activa con justificacion.
- `RESTART`: crea una nueva ventana de 168 horas por un nuevo activador valido.

Un evento pequeno de seguimiento no reinicia automaticamente la vigencia.

Cada reajuste debe registrar:

- Evento modificador.
- Version anterior.
- Version nueva.
- Variables modificadas.
- Justificacion.
- Area anterior y nueva.
- Vencimiento anterior y nuevo.

## 9. Penalizacion por ampliacion

La evaluacion debe registrar el area total vigilada.

Una version reajustada no se considerara mejor solamente por ampliar considerablemente la region o extender la vigencia. La comparacion debera considerar:

- Cambio de area.
- Cambio de tiempo cubierto.
- Numero de regiones activas.
- Numero de reajustes.
- Ganancia real frente a la version anterior.

## 10. Multiples eventos

Si existen varios eventos objetivo dentro de una ventana:

- Se identificara el evento que mejor cumple el forecast.
- Tambien se registraran todos los eventos relevantes dentro y fuera de la region.
- Un solo evento coincidente no elimina los falsos negativos observados en otras regiones.
- No se contaran revisiones del mismo sismo como eventos independientes.

## 11. Actividad fuera del corredor

Toda evaluacion debe registrar:

- Eventos relevantes dentro de la region prevista.
- Eventos relevantes fuera de la region prevista.
- Eventos relevantes dentro del corredor pero fuera del segmento previsto.
- Eventos relevantes en corredores alternativos.

La actividad fuera del forecast no debe ocultarse.

## 12. Evaluacion de magnitud

Para cada modelo se calculara por separado:

- Error con signo: `M_estimada - M_observada`.
- Error absoluto.
- Error cuadratico.
- Cobertura del rango.
- Ancho del rango experimental.

No se seleccionara retrospectivamente el modelo que haya quedado mas cerca.

## 13. Modelos de referencia

Los modelos experimentales deben compararse con:

- B0: tasa historica regional.
- B1: persistencia de actividad reciente.
- C0: region de control de area comparable.

Un componente solo aporta valor si mejora el resultado frente al modelo de referencia sin aumentar desproporcionadamente falsas alarmas o area vigilada.

## 14. Pruebas de ablacion

El modelo combinado se evaluara retirando un componente cada vez:

- Sin conversion Rebella.
- Sin punto medio.
- Sin anillos.
- Sin zona silenciosa.
- Sin actividad volcanica.
- Sin bordes de craton.
- Sin reajustes.
- Sin antipodas.

Si retirar un componente no empeora el rendimiento, no se considerara demostrado su valor incremental.

## 15. Registro minimo de la evaluacion

Cada evaluacion debe guardar:

- Forecast y version evaluada.
- Fecha de evaluacion.
- Estado final.
- Evento coincidente, si existe.
- Coincidencia temporal.
- Coincidencia espacial.
- Coincidencia de magnitud.
- Distancia a la region.
- Error longitudinal sobre el corredor.
- Error de magnitud.
- Eventos relevantes dentro.
- Eventos relevantes fuera.
- Falso positivo.
- Falso negativo.
- Parametros de evaluacion.
- Version del evaluador.

## 16. Reglas de transparencia

1. Publicar aciertos, resultados parciales y fallos.
2. No cambiar criterios despues del resultado.
3. No convertir un resultado parcial en acierto completo.
4. No ocultar actividad fuera de la region prevista.
5. No confundir correlacion con causalidad.
6. No confundir anillos graficos con areas fisicas de ruptura.
7. No presentar analogias de ondas como mediciones instrumentales.
8. Mantener visible la fuente oficial de cada evento.
9. Mantener la advertencia experimental en toda salida publica.

## 17. Criterio de aceptacion del sistema

EARTHQUAKE 3D v2.0 solo se considerara prometedor cuando:

- Supere de forma consistente a los modelos de referencia.
- Mantenga sus resultados fuera de muestra.
- Registre una tasa de falsas alarmas definida y visible.
- Muestre valor incremental en pruebas de ablacion.
- Funcione en mas de una region sin cambiar retrospectivamente las reglas.
- Conserve una auditoria completa de datos, parametros, forecasts, reajustes y evaluaciones.

Los umbrales numericos finales de aceptacion deben fijarse antes de la prueba prospectiva y permanecer versionados.
