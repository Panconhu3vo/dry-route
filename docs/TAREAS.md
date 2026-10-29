# Tareas hasta el Entregable III (viernes 30 de octubre, 23:55)

Plan corto y realista para **dos días**. Cada tarea es un Issue y una rama; Juan combina las ramas en `main`.
Para trabajar en tu tarea con Claude, revisa [TAREAS-POR-INTEGRANTE.md](TAREAS-POR-INTEGRANTE.md).
Los horarios son el **plazo máximo**. Si a alguien no le va a alcanzar, avisa en el grupo **antes** del plazo para reasignar (R7).

## Línea de tiempo

```
Mié 28 noche   T0 todos: entorno funcionando
Jue 29 ─13:00  T1 Vicente: datos OSM          T2 Juan: app rutas + /api/puntos/
       ─18:00  T3 Gonzalo: mapa + layout      T4 Cristóbal: entrada      T5 Yusu: resultado   (con datos falsos del API.md)
       ─23:00  T6 Juan + Vicente: ruteo + /api/ruta/ + pruebas
Vie 30 ─14:00  T7 todos: integración en main + correr los 2 casos
       ─20:00  T8 video grabado y subido
       ─23:00  T9 documento E3 completo y README final   →  entrega antes de las 23:55
```

Dependencias: T6 necesita T1 y T2. Los integrantes de front (T3, T4, T5) **no esperan al backend**: usan los JSON de ejemplo de [API.md](API.md) y se conectan al endpoint real en T7.

---

### T0 · Entorno funcionando en los 5 computadores — *Todos* — mié 28, 23:59
Es el hito H2 del E1, que quedó pendiente.
- [ ] `git pull`, crear el venv, `pip install -r requirements.txt`, `python manage.py migrate` y `python manage.py runserver` (ver README).
- [ ] Abrir http://127.0.0.1:8000/admin/ y ver la pantalla de login de Django.
- [ ] Comentar en el Issue con una captura. Si algo falla, pegar el error **completo**.

### T1 · Datos desde OpenStreetMap — *Vicente* — jue 29, 13:00
Crear `scripts/generar_datos.py` (usa `requirements-datos.txt`), que escribe en `dry-route/data/`:
- [ ] `grafo.json`: `{"nodos": {"<id>": [lat, lon]}, "aristas": [["<id_u>", "<id_v>", largo_m, "nombre calle"]]}`, con red `drive` en la zona definida en DECISIONES D3.
- [ ] `puntos_anegados.json`: `[{"osm_id", "nombre", "tipo": "paso_bajo_nivel", "lat", "lon"}]`, a partir de las aristas con `tunnel=yes` o `layer<0`.
- [ ] `puntos_evacuacion.json`: `[{"osm_id", "nombre", "tipo", "lat", "lon"}]` (los tipos están en API.md).
- [ ] Verificar que aparezcan los pasos bajo nivel de **Gran Avenida/Departamental** y de la zona de **Lo Espejo**. Si no, ajustar el área y anotarlo.
- [ ] `grafo.json` pesa menos de 10 MB. Los 3 archivos se suben al repo.
- [ ] El script tiene comentarios que explican cada paso (Vicente lo tiene que poder explicar).

### T2 · App `rutas`: modelos, admin, carga de datos y `/api/puntos/` — *Juan* — jue 29, 13:00
- [ ] `python manage.py startapp rutas` y registrarla en `INSTALLED_APPS`.
- [ ] Modelos `PuntoAnegado` (`nombre`, `tipo`, `lat`, `lon`, `activo`, `fuente`, `osm_id`) y `PuntoEvacuacion` (`nombre`, `tipo`, `lat`, `lon`, `osm_id`).
- [ ] Admin con `list_editable = ["activo"]` y filtro por `activo`, para simular el escenario con un clic.
- [ ] Comando `python manage.py cargar_datos`, que lee los JSON de `data/` y se puede correr varias veces sin duplicar (`update_or_create` por `osm_id`).
- [ ] Vista `GET /` que renderiza `rutas/mapa.html`, y `GET /api/puntos/` según [API.md](API.md).
- [ ] Crear un superusuario de demo y dejar el comando documentado en el README.

### T3 · Plantilla base, layout y mapa — *Gonzalo* — jue 29, 18:00
- [ ] `templates/base.html` (fuente Atkinson Hyperlegible y Leaflet 1.9.4 desde un CDN) y `templates/rutas/mapa.html` con **todos los IDs** de [API.md](API.md#contrato-interno-del-frontend).
- [ ] `static/css/app.css` con los tokens de [DISENO.md](DISENO.md); layout móvil (bottom sheet) y de escritorio (panel de 380 px).
- [ ] `static/js/mapa.js`: crea `DryRoute.mapa` centrado en la zona, guarda `DryRoute.zona`, carga `/api/puntos/` (o el JSON de ejemplo) y dibuja los anegados activos e inactivos y los de evacuación según DISENO.md.
- [ ] Aviso permanente "Ruta referencial…" en `#aviso`. Atribución de OSM visible.

### T4 · Panel de entrada: origen y destino — *Cristóbal* — jue 29, 18:00
`static/js/entrada.js`:
- [ ] El botón **Usar mi ubicación** (`navigator.geolocation`) fija el origen. Si cae fuera de `DryRoute.zona`, muestra el mensaje de DECISIONES D9.
- [ ] Búsqueda con **Nominatim** al presionar Buscar o Enter (no mientras se escribe), con `countrycodes=cl`, `viewbox` de la zona y `bounded=1`. Muestra hasta 5 resultados para elegir.
- [ ] Clic en el mapa: el primer clic fija el origen y el segundo el destino. Los marcadores se pueden mover arrastrándolos.
- [ ] **Calcular ruta** queda habilitado solo con origen y destino. Hace `fetch('/api/ruta/?origen=..&destino=..')` y llama a `DryRoute.mostrarResultado(json)` o, si hay un error 400, a `DryRoute.mostrarError(json.mensaje)`.

### T5 · Presentación del resultado — *Yusu* — jue 29, 18:00
`static/js/resultado.js`:
- [ ] `DryRoute.mostrarResultado(r)`: dibuja `r.ruta` (estilo de DISENO.md), ajusta el mapa a la ruta y muestra la tarjeta.
  - `estado = "segura"`: "Ruta segura · X km · Y min · Evita N puntos anegados".
  - `estado = "sin_ruta"`: "No hay ruta segura a tu destino" más el punto de evacuación resaltado y la ruta hacia él.
- [ ] `DryRoute.mostrarError(mensaje)` y `DryRoute.limpiarResultado()`, con el botón **Nueva ruta**.
- [ ] Probado con **los dos JSON de ejemplo** de [API.md](API.md) antes de que exista el endpoint.

### T6 · Algoritmo de ruta segura y `/api/ruta/` — *Juan + Vicente (en pareja)* — jue 29, 23:00
- [ ] `rutas/ruteo.py`: carga `grafo.json` una sola vez, busca el nodo más cercano a un punto, bloquea los nodos a menos de 100 m de los anegados activos y calcula la ruta con `nx.shortest_path(weight="largo")`. Si no hay ruta, va al punto de evacuación alcanzable más cercano (reglas en DECISIONES D5).
- [ ] La vista `/api/ruta/` valida los parámetros y la zona, y responde **exactamente** como en [API.md](API.md).
- [ ] `rutas/tests.py` con los **2 casos de prueba** de [ENTREGABLE-3.md](ENTREGABLE-3.md), pasando con `python manage.py test rutas`.
- [ ] `calcular_ruta` queda en unas 30 líneas legibles: es el fragmento que se explica en el video.

### T7 · Integración y ejecución de los casos — *Juan coordina, todos* — vie 30, 14:00
- [ ] Unir todos los PR a `main`; quitar los datos falsos del front.
- [ ] Desde un clon limpio: seguir el README de principio a fin y comprobar que funciona.
- [ ] Ejecutar en el navegador los 2 casos y anotar el *resultado observado* en ENTREGABLE-3.md, con capturas.
- [ ] Corregir solo los bugs que impiden los casos. Lo cosmético queda para después.

### T8 · Video de demostración (máx. 5 min) — *Yusu (graba); Juan o Vicente (explican el código)* — vie 30, 20:00
- [ ] Seguir el guion de [ENTREGABLE-3.md](ENTREGABLE-3.md#guion-del-video-5-min).
- [ ] Subirlo con un enlace **accesible para el equipo docente** (probarlo en una ventana de incógnito).

### T9 · Documento del Entregable III y README — *Cristóbal + Gonzalo* — vie 30, 23:00
- [ ] Completar las tablas del documento (componentes, casos, estado, plan y riesgos) a partir de [ENTREGABLE-3.md](ENTREGABLE-3.md).
- [ ] Revisar que el README tenga dependencias, pasos de ejecución y datos de prueba (lo exige la pauta).
- [ ] Enlaces del video y del repo; **entregar antes de las 23:55**.

---

## Después del viernes (no empezar antes)

- F2 Reporte colaborativo o F3 Alertas (con MeteoPrecisa): el equipo prioriza una para la entrega final.
- Pruebas con 5 usuarios (R5).
- Sesión de traspaso de Django y tutorial oficial antes del 2 de noviembre (R2).
- Guardar `Consulta` y `Ruta` en la base de datos (persistencia, alineada con el ER del E2).
