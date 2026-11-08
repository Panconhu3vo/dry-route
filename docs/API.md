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

**Claves nuevas para el reporte colaborativo** (se agregan a las anteriores):

```json
{
  "anegados": [
    {
      "id": 9,
      "nombre": "Reporte ciudadano: calle anegada",
      "tipo": "anegamiento",
      "activo": true,
      "fuente": "Reportes ciudadanos",
      "confirmaciones": 2,
      "lat": -33.5101,
      "lon": -70.6566
    }
  ],
  "reportes_pendientes": [
    { "id": 12, "tipo": "arbol_caido", "descripcion": "Árbol sobre la calzada", "lat": -33.5150, "lon": -70.6580, "fecha_hora": "2026-11-11T18:30:00-03:00", "confirmaciones": 1, "requeridas": 2 }
  ]
}
```

- `anegados[].fuente`: `"OpenStreetMap"` o `"Reportes ciudadanos"`. `anegados[].confirmaciones` es `0` si el punto no tiene reportes.
- `reportes_pendientes`: reportes vigentes que aún no se confirman. **No bloquean rutas.**

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

### Respuesta 200: el origen está en una zona anegada

Si el origen está a menos de 100 m de un anegado activo, **se ignora el destino**: lo primero es salir. Misma forma que `sin_ruta`, con `"estado": "en_peligro"`, `"mensaje": "Estás en una zona anegada. Sal por esta ruta al punto de evacuación más cercano."` y `ruta` hacia `punto_evacuacion`. El front muestra el título *"Estás en una zona de peligro"*.

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

## `POST /api/reportes/`

Crea un reporte. El cuerpo va en JSON y hay que enviar el encabezado `X-CSRFToken` con el valor de la cookie `csrftoken`. La vista `/` entrega esa cookie.

```json
{ "tipo": "anegamiento", "descripcion": "Agua hasta la vereda", "lat": -33.5101, "lon": -70.6566 }
```

`tipo`: `anegamiento` | `calle_cortada` | `arbol_caido` | `puente_cortado`. `descripcion` es opcional (máximo 200 caracteres).

### Respuesta 201: reporte recibido, falta confirmar

```json
{ "id": 12, "estado": "pendiente", "confirmaciones": 1, "requeridas": 2, "punto_id": null, "mensaje": "Reporte recibido. Falta que otra persona confirme este lugar." }
```

### Respuesta 201: reporte confirmado

```json
{ "id": 13, "estado": "confirmado", "confirmaciones": 2, "requeridas": 2, "punto_id": 9, "mensaje": "Reporte confirmado. Las rutas ya evitan este lugar." }
```

### Respuesta 400: error de entrada

```json
{ "error": "ya_reportado", "mensaje": "Ya reportaste este lugar. Falta que otra persona lo confirme." }
```

| `error` | Cuándo |
|---|---|
| `parametros_invalidos` | Falta un campo, o la descripción es demasiado larga |
| `tipo_invalido` | `tipo` no es uno de los cuatro permitidos |
| `fuera_de_zona` | El punto cae fuera de `zona` |
| `ya_reportado` | La misma persona (sesión) ya reportó ese lugar en las últimas 6 horas |

---

## Contrato interno del frontend

Los tres archivos JS comparten **un solo objeto global**: `window.DryRoute`. Se cargan en este orden al final de `mapa.html`:

```html
<script src="{% static 'js/mapa.js' %}"></script>       <!-- Gonzalo -->
<script src="{% static 'js/resultado.js' %}"></script>  <!-- Yusu -->
<script src="{% static 'js/entrada.js' %}"></script>    <!-- Cristóbal -->
<script src="{% static 'js/reporte.js' %}"></script>    <!-- Cristóbal -->
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
| `btn-reportar` | botón "Reportar un problema" (fuera de `form-ruta`) |
| `form-reporte` | formulario de reporte, oculto al inicio |
| `select-tipo-reporte` | lista de tipos de reporte |
| `input-descripcion-reporte` | descripción opcional |
| `btn-enviar-reporte` | enviar el reporte |
| `btn-cancelar-reporte` | cerrar el formulario |
| `reporte-mensaje` | mensajes del reporte (`aria-live="polite"`) |

Funciones nuevas para el reporte colaborativo:

| Archivo | Define | Usa |
|---|---|---|
| `mapa.js` | `DryRoute.recargarPuntos()`: vuelve a pedir `/api/puntos/`, redibuja y devuelve los datos | Llama a `DryRoute.alRecargarPuntos(datos)` si existe |
| `entrada.js` | `DryRoute.calcularRuta()`: repite el cálculo con el origen y destino actuales | `mostrarResultado`, `mostrarError` |
| `reporte.js` | `DryRoute.modoReporte` (`true` mientras se elige el lugar; `entrada.js` ignora esos clics) | `recargarPuntos` |
| `resultado.js` | `DryRoute.alRecargarPuntos(datos)`: si cambiaron los anegados activos y hay ruta, recalcula y avisa | `calcularRuta` |
