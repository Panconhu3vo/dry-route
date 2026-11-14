# Diseño visual

La persona usuaria está **en la calle, con lluvia, apurada y con el celular en una mano**. Todo se decide desde ahí: alto contraste, botones grandes, poco texto y la información crítica primero.
Base: el prototipo de baja fidelidad del E2 ([img/prototipo-baja-fidelidad.png](img/prototipo-baja-fidelidad.png)).

## Principios

1. **Mobile-first.** Se diseña primero para 375 px de ancho; en escritorio, el panel pasa al costado.
2. **El mapa es la pantalla.** El panel ocupa como máximo el 40% de la altura en el celular.
3. **Nunca solo color.** Cada estado lleva color, ícono o forma, y texto (hay daltonismo y pantallas con reflejo).
4. **Tema claro, alto contraste.** Se lee mejor al sol y bajo la lluvia. Contraste mínimo AA (4,5:1) para todo el texto.
5. **Botones de al menos 48 px de alto**, separados entre sí, para usar con el dedo mojado.

## Tokens (en `static/css/app.css`)

```css
:root {
  --fondo:            #F8F9FA;
  --superficie:       #FFFFFF;
  --superficie-suave: #F1F3F4;  /* campos de texto */
  --texto:            #1F2328;
  --texto-suave:      #5F6368;
  --borde:            #DADCE0;
  --agua:             #1A6FD8;  /* acción principal */
  --ruta:             #188038;  /* ruta segura (no usar para texto) */
  --ruta-texto:       #137333;
  --peligro:          #D93025;  /* anegado, "No hay ruta segura" */
  --alerta-fondo:     #FEF7E0;
  --alerta-borde:     #F29900;  /* avisos y reportes pendientes */
  --inactivo:         #9AA0A6;  /* paso bajo nivel sin agua */
}
```

**Estilo (rediseño del 13-11, inspirado en Google Flood Hub):** mapa a pantalla completa en grises suaves; panel blanco flotante con sombra (en el celular, hoja inferior); campos grises redondeados; botones tipo píldora; tarjetas de resultado con fondo verde o rojo suave. El color se reserva para lo que significa algo: azul para las acciones, verde para la ruta, rojo para lo anegado y ámbar para lo pendiente.

**Tipografía:** [Atkinson Hyperlegible](https://fonts.google.com/specimen/Atkinson+Hyperlegible), diseñada para máxima legibilidad (encaja con una app de emergencia). Una sola familia, en pesos 400 y 700.
Escala: 14 / **16 (base)** / 20 / 24 px. Interlineado 1,4.

## Elementos del mapa (Leaflet)

| Elemento | Representación |
|---|---|
| Ubicación u origen del usuario | círculo azul `--agua` con halo claro |
| Destino | bandera verde `--ruta` |
| Punto anegado **activo** | círculo rojo `--peligro` relleno, radio de unos 100 m (el radio de bloqueo), con popup que muestra el nombre |
| Punto de riesgo **inactivo** | punto pequeño gris `--inactivo` |
| Punto de evacuación | marcador verde con ícono de cruz o casa; solo se resalta cuando es el resultado |
| Ruta segura | línea `--ruta`, grosor 6, con borde blanco para que se lea sobre el mapa |

Teselas: OpenStreetMap estándar, pasadas a grises con un filtro CSS solo en la capa base (`.leaflet-tile-pane`), **con la atribución visible** (es obligatoria): `© OpenStreetMap contributors`. Se probó CARTO Positron, pero ahora exige una clave de API.

## Pantallas (del prototipo E2)

1. **Inicio:** mapa centrado en la zona, con puntos anegados y el aviso. Panel con "Origen" y "Destino".
2. **Ingreso:** el origen se puede fijar con *Usar mi ubicación*, buscando una dirección o con un clic en el mapa; el destino, buscando o con un clic. Botón **Calcular ruta** (deshabilitado hasta tener ambos).
3. **Ruta segura:** tarjeta con el título "Ruta segura" en `--ruta-texto`, `4,2 km · 17 min` y "Evita 2 puntos anegados". La ruta se dibuja y el mapa se ajusta a ella.
4. **Sin ruta segura:** tarjeta con borde `--peligro` y el título "No hay ruta segura a tu destino", más el nombre y la distancia del punto de evacuación. Se dibuja la ruta hacia ese punto.
5. *(Después del viernes)* Recalcular la ruta ante nuevos reportes.

**Aviso permanente** (`#aviso`), con fondo `--alerta-fondo` y borde `--alerta-borde`:
> Ruta referencial. Sigue las indicaciones de las autoridades. Emergencias: 131 SAMU · 132 Bomberos · 133 Carabineros.

## Layout

- **Móvil (< 768 px):** encabezado delgado con "Dry Routes", mapa a pantalla completa y panel inferior tipo hoja (*bottom sheet*) con esquinas redondeadas.
- **Escritorio (≥ 768 px):** panel a la izquierda de 380 px de ancho y mapa en el resto.
- El panel muestra **o** el formulario **o** el resultado, con un botón "Nueva ruta" para volver.

## Textos (tono)

Tuteo, frases cortas y verbos de acción: "Calcular ruta", "Usar mi ubicación", "Ir al punto de evacuación".
Los errores dicen qué hacer: *"No encontramos esa dirección. Prueba con calle y número, o marca el punto en el mapa."*

## Accesibilidad mínima

- Cada `input` tiene un `<label>`, y los botones de solo ícono llevan `aria-label`.
- El foco es visible (`outline` de 3 px en `--agua`).
- El resultado se anuncia con `aria-live="polite"` en `#resultado`.
