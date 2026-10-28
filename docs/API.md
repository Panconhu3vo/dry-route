# Contrato entre frontend y backend

Este documento permite que el front y el back trabajen **en paralelo**. El front puede usar los JSON de ejemplo como datos falsos (*mock*) mientras el endpoint real no esté listo.
**Si cambias algo de este contrato, actualiza este archivo en el mismo PR y avísale al otro lado.**

Todas las coordenadas van en formato **`[lat, lon]`**, en grados decimales (WGS84), en ese orden. Leaflet usa el mismo orden.

---

## Páginas

| URL | Vista | Plantilla |
|---|---|---|
| `GET /` | `rutas.views.mapa` | `templates/rutas/mapa.html` |
| `GET /admin/` | admin de Django | marcar puntos anegados (`activo`) |

---

## `GET /api/puntos/`

Devuelve los puntos que se dibujan al abrir el mapa y los límites de la zona cubierta.

**Respuesta 200**

```json
{
  "zona": { "norte": -33.490, "sur": -33.545, "oeste": -70.680, "este": -70.635 },
  "anegados": [
    {
      "id": 1,
      "nombre": "Paso bajo nivel Gran Avenida / Departamental",
      "tipo": "paso_bajo_nivel",
      "activo": true,
      "lat": -33.5019,
      "lon": -70.6526
    }
  ],
  "evacuacion": [
    {
      "id": 7,
      "nombre": "Hospital Barros Luco",
      "tipo": "hospital",
      "lat": -33.5047,
      "lon": -70.6560
    }
  ]
}
```

- `anegados[].activo`: `true` significa anegado **ahora** (se dibuja en rojo y la ruta lo evita); `false` significa punto de riesgo sin anegamiento (gris, la ruta puede pasar).
- `evacuacion[].tipo`: `hospital` | `clinica` | `bomberos` | `carabineros` | `colegio` | `punto_encuentro`.

---

## `GET /api/ruta/?origen=LAT,LON&destino=LAT,LON`

Calcula la ruta segura. Ejemplo: `/api/ruta/?origen=-33.4950,-70.6540&destino=-33.5300,-70.6620`

### Respuesta 200: hay ruta segura

```json
{
  "estado": "segura",
  "mensaje": "Ruta segura encontrada.",
  "ruta": [[-33.4950, -70.6540], [-33.4968, -70.6545], [-33.5300, -70.6620]],
  "distancia_m": 4200,
  "tiempo_min": 17,
  "puntos_evitados": [
    { "id": 1, "nombre": "Paso bajo nivel Gran Avenida / Departamental", "lat": -33.5019, "lon": -70.6526 }
  ],
  "punto_evacuacion": null
}
```

### Respuesta 200: no hay ruta segura al destino

`ruta` lleva al **punto de evacuación más cercano**, no al destino.

```json
{
  "estado": "sin_ruta",
  "mensaje": "No hay una ruta segura a tu destino. Te guiamos al punto de evacuación más cercano.",
  "ruta": [[-33.4950, -70.6540], [-33.4990, -70.6551]],
  "distancia_m": 650,
  "tiempo_min": 3,
  "puntos_evitados": [],
  "punto_evacuacion": { "id": 7, "nombre": "Hospital Barros Luco", "tipo": "hospital", "lat": -33.5047, "lon": -70.6560 }
}
```

Si tampoco hay ningún punto de evacuación alcanzable: `estado = "sin_ruta"`, `ruta = []`, `punto_evacuacion = null` y un `mensaje` que lo explica.

### Respuesta 400: error de entrada

```json
{ "error": "fuera_de_zona", "mensaje": "El origen está fuera de la zona cubierta. Marca un punto dentro del área." }
```

| `error` | Cuándo |
|---|---|
| `parametros_invalidos` | Falta `origen` o `destino`, o no tienen el formato `lat,lon` |
| `fuera_de_zona` | El origen o el destino caen fuera de `zona` |

Campos:

- `distancia_m` y `tiempo_min` son enteros redondeados. El tiempo se calcula a 15 km/h (ver DECISIONES D5).
- `puntos_evitados` son los anegados activos que la ruta "normal" (sin bloqueos) habría cruzado. Sirve para el texto *"Evita N puntos anegados"*. Puede venir vacío.

---

## Contrato interno del frontend

Los tres archivos JS comparten **un solo objeto global**: `window.DryRoute`. Se cargan en este orden al final de `mapa.html`:

```html
<script src="{% static 'js/mapa.js' %}"></script>       <!-- Gonzalo -->
<script src="{% static 'js/resultado.js' %}"></script>  <!-- Yusu -->
<script src="{% static 'js/entrada.js' %}"></script>    <!-- Cristóbal -->
```

| Archivo | Define | Usa |
|---|---|---|
| `mapa.js` | `DryRoute.mapa` (el `L.map`), `DryRoute.zona`; carga `/api/puntos/` y dibuja los puntos | — |
| `resultado.js` | `DryRoute.mostrarResultado(respuesta)`, `DryRoute.mostrarError(mensaje)`, `DryRoute.limpiarResultado()` | `DryRoute.mapa` |
| `entrada.js` | `DryRoute.origen`, `DryRoute.destino` (`{lat, lon}` o `null`); búsqueda con Nominatim, GPS, clic en el mapa; botón **Calcular ruta** → `fetch('/api/ruta/...')` | `DryRoute.mapa`, `DryRoute.zona`, `mostrarResultado`, `mostrarError`, `limpiarResultado` |

IDs del HTML (los crea Gonzalo en `mapa.html`; los demás solo los usan):

| id | Elemento |
|---|---|
| `mapa` | contenedor del mapa Leaflet |
| `panel` | panel lateral (escritorio) o inferior (móvil) |
| `form-ruta` | formulario de origen y destino |
| `input-origen`, `input-destino` | campos de texto de dirección |
| `btn-gps` | botón "Usar mi ubicación" |
| `btn-calcular` | botón "Calcular ruta" |
| `resultado` | contenedor de la tarjeta de resultado |
| `aviso` | aviso permanente "Ruta referencial…" |
