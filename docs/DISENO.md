# Diseño visual

La persona usuaria está **en la calle, con lluvia, apurada y con el celular en una mano**. Todo se decide desde ahí: alto contraste, botones grandes, poco texto y la información crítica primero.

- **Base:** el prototipo de baja fidelidad del E2 ([img/prototipo-baja-fidelidad.png](img/prototipo-baja-fidelidad.png)).
- **Diseño actual (rediseño del 20-11):** el prototipo *"Dry Routes — Rediseño moderno"*, con 4 pantallas: ingreso y ruta segura en el navegador, ruta segura y sin ruta en el celular.

## Principios

1. **Mobile-first.** Se diseña primero para 375 px de ancho; en escritorio, el panel pasa al costado.
2. **El mapa es la pantalla.** El panel ocupa como máximo el 45% de la altura en el celular.
3. **Nunca solo color.** Cada estado lleva color, ícono o forma, y texto (hay daltonismo y pantallas con reflejo).
4. **Tema claro, alto contraste.** Se lee mejor al sol y bajo la lluvia. Contraste mínimo AA (4,5:1) para todo el texto.
5. **Botones de al menos 48 px de alto**, separados entre sí, para usar con el dedo mojado.

## Tokens (en `static/css/app.css`)

```css
:root {
  --fondo:            #F4F7FA;
  --superficie:       #FFFFFF;
  --texto:            #14212B;
  --texto-suave:      #51616E;
  --borde:            #D3DCE3;
  --agua:             #0B63C4;  /* acción principal y tu ubicación */
  --agua-suave:       #E8F1FB;  /* botones con ícono, etiqueta "Evita N puntos" */
  --ruta:             #0B63C4;  /* línea de la ruta segura */
  --ruta-texto:       #0B4E9C;  /* texto "Ruta segura" */
  --anegado:          #0782A8;  /* agua: zona anegada ahora */
  --peligro:          #C8322A;  /* "No hay ruta segura", errores, alertas de lluvia */
  --peligro-fondo:    #FBE6E4;
  --alerta-fondo:     #FFF1D6;  /* aviso permanente y reportes pendientes */
  --alerta-borde:     #E08A00;
  --inactivo:         #8D9AA5;  /* punto de riesgo sin agua */
  --evacuacion:       #188038;  /* salud, bomberos, Carabineros y colegios */
}
```

**Estilo:** mapa a pantalla completa en grises suaves.

- **Escritorio:** panel blanco flotante a la izquierda, sobre el mapa (tarjeta con margen, esquinas redondeadas y sombra).
- **Celular:** cabecera flotante arriba y hoja inferior.
- **Elementos del panel:** campos blancos con borde, botones tipo píldora y una tarjeta de resultado con sombra.
- **Sombras:** `--sombra-suave` despega del fondo los campos, los botones secundarios y la caja del estado de la zona. La tarjeta "sin ruta" lleva una sombra rojiza, el aviso una ámbar y la ruta del mapa una sombra bajo su borde blanco.
- **Leyenda compacta** (12 px): acompaña al mapa sin taparlo.

El color se reserva para lo que significa algo:

- **Azul:** acción y ruta segura.
- **Celeste con olas:** agua.
- **Rojo:** peligro.
- **Ámbar:** aviso o reporte pendiente.
- **Verde:** puntos de evacuación.

**Tipografía:** [Atkinson Hyperlegible Next](https://fonts.google.com/specimen/Atkinson+Hyperlegible+Next), diseñada para máxima legibilidad (encaja con una app de emergencia), en pesos 400, 500 y 700. Los números que importan (minutos, distancia y teléfonos de emergencia) van en **Atkinson Hyperlegible Mono**, que tiene todas las cifras del mismo ancho.

**Íconos:** son máscaras CSS (`.icono-ruta`, `.icono-escudo`, `.icono-gps`, `.icono-casa`…) que toman el color del texto. Se usan con `<span class="icono icono-escudo"></span>`.

## Elementos del mapa (Leaflet)

| Elemento | Representación |
|---|---|
| Ubicación u origen del usuario | círculo azul `--agua` con borde blanco y halo |
| Destino | bandera oscura con borde blanco |
| Punto anegado **activo** | círculo de 100 m (el radio de bloqueo) relleno con **olas celestes** y una **gota** blanca en un círculo `--anegado` al centro; popup con el nombre (y los mm/h si lo encendió la lluvia) |
| Punto de riesgo **inactivo** | punto gris `--inactivo` con borde blanco |
| Reporte sin confirmar | triángulo ámbar con "!" |
| Punto de evacuación | cuadrado verde con cruz (salud) o casa; el elegido como resultado es un círculo azul grande con casa o cruz |
| Ruta segura | línea `--ruta`, grosor 7, con borde blanco para que se lea sobre el mapa |

Teselas: OpenStreetMap estándar, pasadas a grises con un filtro CSS solo en la capa base (`.leaflet-tile-pane`), **con la atribución visible** (es obligatoria): `© OpenStreetMap contributors` y `Lluvia: Open-Meteo`.

**Leyenda:** franja blanca flotante abajo del mapa en escritorio. En el celular se abre con el botón (i) de la cabecera.

## Pantallas

1. **Inicio:**
   - Estado de la zona arriba: "💧 N anegamientos activos" y la franja de lluvia.
   - Título "¿A dónde necesitas llegar?".
   - Origen, con el botón de ubicación al lado, y Destino.
   - Botón **Calcular ruta** (deshabilitado hasta tener ambos).
   - Lista de anegamientos activos: a lo más 5; al tocar uno, el mapa va a ese lugar.
2. **Ingreso:** el origen se puede fijar con el botón de ubicación, buscando una dirección (Enter) o con un clic en el mapa; el destino, buscando o con un clic.
3. **Ruta segura:**
   - "Desde / Hasta".
   - Tarjeta con 🛡 "Ruta segura", **"17 min"** grande, "4,2 km" y la etiqueta "Evita 2 puntos anegados".
   - Botón **Nueva ruta**.
   - La ruta se dibuja y el mapa se ajusta a ella.
4. **Sin ruta segura:**
   - Tarjeta con borde `--peligro`, ícono de advertencia y el título "No hay ruta segura a tu destino" (o "Estás en una zona de peligro").
   - Debajo, la fila **Punto de evacuación** con su nombre, distancia y tiempo.
5. **Recálculo:** si cambian los puntos anegados, la ruta se recalcula sola y aparece "↻ Cambiaron los puntos anegados de la zona. Ruta recalculada." arriba del resultado.
6. **Franja de lluvia** (`#alerta-lluvia`, F3), junto al número de anegamientos:
   - Sin alerta: texto gris ("Sin alertas de lluvia en la zona · actualizado 20:45").
   - Aviso: ☁ ámbar.
   - Alerta: ⚠ rojo suave.
   - Alarma: ⚠ rojo lleno con texto blanco.
   - Sin datos al día: "?".

**Aviso permanente** (`#aviso`), con fondo `--alerta-fondo` y borde `--alerta-borde`. Queda **pegado al borde de abajo del panel** aunque el contenido haga scroll, para que siempre esté a la vista (R5):
> **Ruta referencial.** Sigue las indicaciones de las autoridades.

Debajo van tres botones `tel:` para llamar con un toque: **131** SAMU · **132** Bomberos · **133** Carabineros.

## Layout

- **Móvil (< 768 px):**
  - Mapa a pantalla completa.
  - Arriba flota una barra blanca con "Dry Routes" y el botón (i), y debajo las píldoras del estado de la zona.
  - Abajo, un panel tipo hoja (*bottom sheet*) con esquinas redondeadas.
  - Con una ruta en pantalla, la hoja muestra primero la tarjeta y esconde la lista de anegamientos.
- **Escritorio (≥ 768 px):** el mapa ocupa toda la pantalla y el panel de 400 px flota encima, a 16 px del borde izquierdo y de arriba. Mide lo que mide su contenido y, si no cabe, hace scroll por dentro. La leyenda empieza a la derecha del panel, y al encuadrar una ruta se deja libre el espacio que tapa el panel.
- El panel muestra **o** el formulario **o** el resultado, con un botón "Nueva ruta" para volver. El formulario de reporte (F2) reemplaza a los dos mientras está abierto.

## Textos (tono)

Tuteo, frases cortas y verbos de acción: "Calcular ruta", "Usar mi ubicación", "Ir al punto de evacuación".
Los errores dicen qué hacer: *"No encontramos esa dirección. Prueba con calle y número, o marca el punto en el mapa."*

## Accesibilidad mínima

- Cada `input` tiene un `<label>`, y los botones de solo ícono (ubicación, leyenda) llevan `aria-label`.
- El foco es visible (`outline` de 3 px en `--agua`).
- El resultado se anuncia con `aria-live="polite"` en `#resultado`, y la lluvia en `#alerta-lluvia`.
