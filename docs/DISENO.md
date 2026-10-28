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
  --fondo:          #F4F7FA;
  --superficie:     #FFFFFF;
  --texto:          #14212B;
  --texto-suave:    #51616E;
  --borde:          #D3DCE3;

  --agua:           #0B63C4;  /* acción principal, ubicación del usuario */
  --ruta:           #1E9E5A;  /* línea de la ruta segura y bandera de destino (no usar para texto) */
  --ruta-texto:     #146B3E;  /* texto "Ruta segura" */
  --peligro:        #C8322A;  /* anegado activo, "No hay ruta segura" */
  --alerta-fondo:   #FFF1D6;  /* fondo del aviso; texto en --texto */
  --alerta-borde:   #E08A00;
  --inactivo:       #8D9AA5;  /* punto de riesgo sin anegamiento */

  --radio:          12px;
  --sombra:         0 2px 12px rgb(20 33 43 / 0.12);
  --fuente:         "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif;
}
```

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

Teselas: OpenStreetMap estándar, **con la atribución visible** (es obligatoria): `© OpenStreetMap contributors`.

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
