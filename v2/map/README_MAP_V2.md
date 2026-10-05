# Mapa y digitalizacion EARTHQUAKE 3D v2.0

Esta carpeta conserva los metadatos del Transfer Pressure Map y las futuras geometrías versionadas.

## Regla principal

El PDF original no debe modificarse. Los nodos, corredores, bifurcaciones y vínculos volcánicos se guardarán como archivos derivados independientes.

## Archivos previstos

- `TRANSFER_PRESSURE_MAP_METADATA.json`: identificación, hash, leyenda y reglas de digitalización.
- `nodes.geojson`: nodos D, X, volcanes, puntos intermedios y otros nodos.
- `corridors.geojson`: flechas convertidas en líneas dirigidas.
- `branches.geojson`: bifurcaciones entre corredores.
- `volcano_links.geojson`: asociaciones visuales entre volcanes y corredores.

## Estado inicial

- Mapa original: preservado.
- Digitalización: no iniciada.
- Corredor piloto: `PER-NORTE-01`.
- Forecast habilitado: no.

## Criterios de seguridad

- No inventar coordenadas.
- Registrar incertidumbre visual.
- Versionar cada cambio geométrico.
- Validar la dirección contra el mapa original.
- No activar forecasts antes de la validación histórica.
