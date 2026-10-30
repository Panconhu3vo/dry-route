# Decisiones técnicas

Registro de lo que decidimos y por qué. Si alguna decisión cambia, se actualiza aquí y en `CLAUDE.md`.
Fecha de este registro: 28 de octubre de 2026.

## D1. Alcance de la v1: solo la funcionalidad corazón

- **Decisión:** hasta el Entregable III (30 de octubre) solo se implementa la *ruta de evacuación segura*. El reporte colaborativo (F2) y las alertas (F3) quedan para la entrega final.
- **Por qué:** es la acción de respuesta a R1 en la matriz de riesgos (exposición 9, crítica). El Entregable III solo exige la funcionalidad corazón.

## D2. Ruteo propio con NetworkX sobre un grafo precalculado

- **Decisión:** el grafo de calles se descarga **una sola vez** con OSMnx y se guarda en `dry-route/data/grafo.json`. Django lo carga con `json` y `networkx`, y calcula la ruta con Dijkstra (`nx.shortest_path(..., weight="largo")`) después de quitar los nodos cercanos a los puntos anegados.
- **Alternativas descartadas:**
  - *Google Directions API:* no permite excluir puntos arbitrarios de la ruta, que es justamente nuestra funcionalidad. Además exige una API key con facturación.
  - *OpenRouteService:* sí permite evitar polígonos, pero el procesamiento quedaría fuera de nuestra app y sería difícil de explicar en el video.
  - *OSMnx en tiempo de ejecución:* necesita internet, es lento y obliga a los 5 integrantes a instalar geopandas.
- **Por qué:** coincide con la mitigación de R3 (NetworkX y una sola zona primero), funciona sin internet durante la demo y el algoritmo cabe en unas 30 líneas que el equipo puede explicar.
- **Grafo no dirigido (decisión de Vicente en T1):** en `grafo.json` cada calle aparece **una sola vez y sin sentido de tránsito**, porque la ruta es referencial. El archivo pesa menos y el cálculo es más simple. En T6 se carga como `nx.Graph()`, no `nx.DiGraph()`.
- **Formato elegido:** JSON propio en lugar de GraphML. GraphML guarda todo como texto y obliga a convertir tipos, mientras que el JSON se lee directo y cualquiera puede abrirlo.

## D3. Zona: eje Gran Avenida, de Departamental a Lo Espejo

- **Decisión:** el grafo cubre aproximadamente el rectángulo norte −33.490, sur −33.545, oeste −70.680, este −70.635 (San Miguel, La Cisterna y Lo Espejo). **Vicente verifica los límites en el mapa al generar los datos.**
- **Por qué:** los pasos bajo nivel de Gran Avenida, Departamental y Lo Espejo son los que citamos en el E1 y en R5. Una zona acotada mantiene el grafo pequeño y el cálculo rápido (R3).
- **Red:** `network_type="drive"` (calles vehiculares). Es más pequeña y los pasos bajo nivel son vehiculares.

## D4. Datos desde OpenStreetMap, sin trabajo manual

- **Puntos de riesgo:** las aristas del mismo grafo con `tunnel=yes` o `layer<0` (pasos bajo nivel). Se toma el punto medio de cada una. Según Senapred, citado por El Dínamo (23/10/2026), el 41% de los puntos críticos del Gran Santiago son anegamientos de caminos o pasos a desnivel.
- **Puntos de evacuación:** elementos de OSM con `amenity` = `hospital`, `clinic`, `fire_station`, `police` o `school`, más `emergency=assembly_point`.
- **Estado "anegado ahora":** como no tenemos sensores (R5), para la demo se **simula un escenario**: en el admin de Django se marca `activo=True` en los puntos que están anegados. Esto es coherente con la prueba por escenarios simulados que comprometimos en R5.
- **`osm_id` es texto (decisión de Vicente en T1):** viene como `"way/123"` o `"node/456"`, porque en OpenStreetMap dos elementos de distinto tipo pueden tener el mismo número. En los modelos debe ser `CharField(unique=True)`, no un número.
- **CONDOR:** no encontramos una descarga pública (solo listados en la prensa). Si se consigue más adelante, se carga con el mismo comando `cargar_datos`.

## D5. Regla de "ruta segura"

- Un **tramo de calle** (arista) queda **bloqueado** si pasa a menos de `RADIO_BLOQUEO_M = 100` metros de un punto anegado activo. Se miden tramos y no esquinas porque un paso bajo nivel es un tramo largo (~300 m): sus esquinas quedan lejos del punto aunque el tramo pase justo por él (lo detectó la prueba del caso 1).
- **Hay ruta segura** si existe un camino desde el origen al destino que no usa tramos bloqueados.
- **No hay ruta segura** si el destino está a menos de 100 m de un anegado activo o si los bloqueos lo dejan desconectado. En ese caso se busca el punto de evacuación alcanzable más cercano al origen y se entrega la ruta hacia él.
- Los tramos que salen del origen nunca se bloquean: si el usuario está dentro de una zona anegada, igual tiene que poder salir.
- **Tiempo estimado:** distancia dividida por 15 km/h (velocidad urbana en contingencia; coincide con el prototipo: 4,2 km en 18 min).

## D6. Frontend con plantillas Django, Leaflet y JavaScript plano

- **Decisión:** sin React, sin Node y sin build. Leaflet 1.9.4 desde un CDN y teselas de OpenStreetMap con su atribución obligatoria.
- **JS dividido por responsable:** `mapa.js` (Gonzalo), `entrada.js` (Cristóbal) y `resultado.js` (Yusu). Así se evitan conflictos de Git. Los tres comparten el objeto global `window.DryRoute` (ver [API.md](API.md#contrato-interno-del-frontend)).
- **Por qué:** es lo más simple para un equipo que aprende y reduce el riesgo de integración (R4).

## D7. Búsqueda de direcciones con Nominatim

- **Decisión:** se busca **al presionar "Buscar"** (no mientras se escribe), con `countrycodes=cl`, `viewbox` de la zona y `bounded=1`.
- **Por qué:** es gratis, no requiere key, y su política de uso exige un máximo de 1 consulta por segundo y prohíbe el autocompletado.
- **Plan B:** el clic en el mapa siempre funciona, aunque Nominatim falle.

## D8. Git: rama por tarea; Juan combina

- Ramas `feat/tN-descripcion` o `fix/descripcion`. Cada integrante hace su commit y sube su rama; **Juan Yañez revisa y combina en `main`** (R4).
- Claude Code **no hace commits ni push**: así cada integrante sabe exactamente qué sube (ver [TAREAS-POR-INTEGRANTE.md](TAREAS-POR-INTEGRANTE.md)).
- `db.sqlite3` **no se versiona**: cada integrante genera la suya con `migrate` y `cargar_datos`.

## D9. GPS fuera de la zona

- `navigator.geolocation` funciona en `localhost`. Pero si la ubicación real del usuario está fuera de la zona del grafo, el backend responde con un error 400 (`fuera_de_zona`) y el front muestra: *"Tu ubicación está fuera de la zona cubierta. Marca tu origen en el mapa."*
- **Para el video:** el origen se marca con clic o con búsqueda, no con GPS.
