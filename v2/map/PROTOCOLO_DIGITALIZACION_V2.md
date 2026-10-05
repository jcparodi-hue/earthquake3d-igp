# EARTHQUAKE 3D v2.0 - Protocolo de digitalizacion

## 1. Proposito

Este protocolo define como convertir los elementos visuales del Transfer Pressure Map en geometria digital versionada, reproducible y auditable.

El mapa original debe permanecer sin modificaciones. Toda geometria creada es una interpretacion digital derivada y experimental.

## 2. Alcance inicial

La primera aplicacion del protocolo sera exclusivamente el corredor piloto:

- Codigo: `PER-NORTE-01`
- Nombre: Corredor norte del Peru
- Regiones de referencia: Tumbes, Piura, Lambayeque y La Libertad
- Estado inicial: `PENDING_DIGITIZATION`
- Forecast habilitado: no

No se digitalizara el resto del planeta hasta completar y revisar este corredor piloto.

## 3. Niveles de evidencia

- `E2`: elemento visible en el mapa original.
- `E3`: calculo o geometria reproducible derivada de la digitalizacion.
- `E4`: interpretacion experimental del metodo.

Un elemento derivado nunca debe presentarse como dato geologico oficial solamente por aparecer en el mapa.

## 4. Sistema de coordenadas

Todas las geometrías se almacenaran en:

- Sistema: `EPSG:4326`
- Orden de coordenadas GeoJSON: `[longitud, latitud]`
- Longitud valida: -180 a 180
- Latitud valida: -90 a 90

Queda prohibido invertir latitud y longitud.

## 5. Preparacion de la sesion

Antes de digitalizar se debe registrar:

- Operador.
- Fecha y hora UTC.
- Version del mapa.
- Archivo fuente.
- Herramienta utilizada.
- Nivel de zoom.
- Corredor trabajado.
- Observaciones iniciales.

No se debe iniciar una sesion sin identificar el archivo fuente y la version del mapa.

## 6. Tipos de elementos

### 6.1 Nodo D

Se registra como punto cuando la letra `D` o su zona profunda asociada sea visible en el mapa.

Propiedades minimas:

- `node_code`
- `node_type`: `D`
- `map_version_code`
- `visual_source_page`
- `visual_confidence`
- `operator`
- `digitized_at_utc`
- `notes`

La coordenada se coloca en el centro visual del simbolo o zona marcada. Si el centro no es claro, se registra incertidumbre y no se fuerza una precision falsa.

### 6.2 Nodo X

Se registra como punto cuando el mapa muestre un punto de terminacion `X`.

Propiedades minimas:

- `node_code`
- `node_type`: `X`
- `visual_confidence`
- `notes`

### 6.3 Volcan V

Se registra como punto visual independiente.

La marca `V` del mapa no debe confundirse automaticamente con un volcan oficial identificado. La asociacion con un volcan real se realizara posteriormente mediante otra fuente.

### 6.4 Bifurcacion

Se registra cuando una flecha se divide en dos o mas rutas visibles.

La bifurcacion debe representarse como:

- Un nodo `BRANCH` en `nodes.geojson`.
- Una relacion entre corredores en `branches.geojson`.

### 6.5 Reflexion

El simbolo de reflexion se registra como nodo `REFLECTION` o como propiedad de un tramo, segun su representacion visual.

No se interpretara como reflexion fisica demostrada. Se conserva como regla visual experimental del mapa.

### 6.6 Corredor

Cada flecha se digitaliza como `LineString` siguiendo su eje central visible.

La direccion de la coordenada debe respetar la punta de la flecha:

- Primer punto: origen visual.
- Ultimo punto: destino visual.

Si la direccion no puede determinarse, el corredor permanece `DIRECTION_UNCERTAIN` y no se habilita para forecast.

## 7. Numero de puntos por corredor

Se usaran los puntos necesarios para conservar la forma visible sin crear detalle artificial.

Criterios:

- Punto inicial.
- Punto final.
- Un punto en cada cambio claro de direccion.
- Un punto en cada bifurcacion.
- Puntos intermedios solo cuando sean necesarios para conservar la curvatura.

No se agregaran puntos para simular precision que el mapa original no tiene.

## 8. Incertidumbre visual

Cada elemento debe recibir una clasificacion:

- `HIGH`: simbolo o linea claramente visible.
- `MEDIUM`: posicion razonablemente visible, con borde o centro ambiguo.
- `LOW`: elemento parcialmente cubierto, borroso o dificil de separar.
- `UNUSABLE`: no debe digitalizarse hasta disponer de una fuente mejor.

La confianza numerica, si se utiliza, debe corresponder a una regla versionada. No se asignaran porcentajes arbitrarios.

## 9. Registro del corredor PER-NORTE-01

La digitalizacion piloto debe comprobar:

1. Que la flecha correspondiente a la costa norte del Peru sea visible.
2. El sentido de la punta de flecha.
3. El punto de entrada al territorio o margen peruano.
4. El punto de salida o continuacion del corredor.
5. Bifurcaciones visibles.
6. Nodos D, X, V o reflexion proximos.
7. Relacion visual con Tumbes, Piura, Lambayeque y La Libertad.
8. Si la escala del mapa permite o no separar esos cuatro segmentos.

Si la escala no permite diferenciar regiones, se digitalizara un solo corredor general y los segmentos administrativos se asociaran posteriormente con una fuente geografica independiente.

## 10. Archivos de salida

- `nodes.geojson`: nodos D, X, V, BRANCH, REFLECTION e INTERMEDIATE.
- `corridors.geojson`: corredores dirigidos.
- `branches.geojson`: relaciones de bifurcacion.
- `volcano_links.geojson`: asociaciones visuales entre marcas V y corredores.
- `DIGITIZATION_LOG.json`: registro de sesiones y revisiones.

## 11. Propiedades minimas de un corredor

Cada `Feature` de corredor debe incluir:

- `corridor_code`
- `corridor_name`
- `map_version_code`
- `direction_status`
- `visual_confidence`
- `digitization_version`
- `operator`
- `digitized_at_utc`
- `review_status`
- `enabled_for_forecast`
- `notes`

El valor inicial de `enabled_for_forecast` sera siempre `false`.

## 12. Revision independiente

Toda geometria debe pasar por dos revisiones:

### Revision A: fidelidad visual

Comprueba que la linea o punto coincide con el mapa original.

### Revision B: consistencia tecnica

Comprueba:

- GeoJSON valido.
- Coordenadas dentro de rango.
- Orden longitud-latitud.
- Identificadores unicos.
- Direccion coherente.
- Propiedades obligatorias.
- Ausencia de geometria vacia en elementos declarados como completados.

Una misma persona puede realizar la primera digitalizacion, pero la aprobacion final debe quedar registrada como una revision separada.

## 13. Estados de digitalizacion

- `NOT_STARTED`
- `IN_PROGRESS`
- `PENDING_REVIEW`
- `CHANGES_REQUIRED`
- `APPROVED_VISUAL`
- `APPROVED_TECHNICAL`
- `VALIDATED`

Solo `VALIDATED` permite considerar la geometria para pruebas historicas. La activacion de forecasts requiere ademas completar la validacion historica definida en los documentos del proyecto.

## 14. Control de versiones

Cada cambio de geometria debe registrar:

- Version anterior.
- Version nueva.
- Fecha y hora UTC.
- Operador.
- Motivo del cambio.
- Elementos modificados.
- Impacto esperado.

No se debe sobrescribir una geometria aprobada sin conservar su version anterior en el historial del repositorio.

## 15. Criterios de rechazo

Una geometria debe rechazarse cuando:

- Utiliza coordenadas inventadas.
- No puede relacionarse con un elemento visible del mapa.
- Invierte latitud y longitud.
- Modifica el mapa original.
- Confunde una marca V con un volcan oficial sin validacion externa.
- Omite la direccion de una flecha visible.
- Declara precision superior a la permitida por la imagen.
- Activa forecasts antes de completar la validacion.

## 16. Criterio para finalizar PER-NORTE-01

El corredor piloto estara listo para validacion historica cuando:

- La geometria este registrada en `corridors.geojson`.
- La direccion este comprobada.
- Los nodos relacionados esten registrados o marcados como no visibles.
- Las bifurcaciones esten documentadas.
- La incertidumbre visual este registrada.
- Las revisiones visual y tecnica esten completadas.
- `PER-NORTE-01.json` apunte a la version geometrica aprobada.
- `enabled_for_forecast` permanezca en `false` hasta terminar el replay historico.

## 17. Advertencia

Modelo experimental. No constituye una alerta oficial, una prediccion determinista ni sustituye la informacion del IGP/CENSIS y otras autoridades competentes.
