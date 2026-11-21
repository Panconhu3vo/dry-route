// mapa.js — Gonzalo (T3 y T14)
// Crea el mapa, guarda la zona cubierta y dibuja los puntos anegados, los de evacuación y los reportes pendientes.
// Define DryRoute.mapa, DryRoute.zona y DryRoute.recargarPuntos(), que usan los demás archivos (ver docs/API.md).

// Un solo objeto global compartido por los tres archivos JS, para no ensuciar la página con variables sueltas.
window.DryRoute = window.DryRoute || {};

// Radio de bloqueo alrededor de un punto anegado activo. Debe coincidir con el del ruteo (T6).
const RADIO_BLOQUEO_M = 100;

// Nombres legibles para los tipos de punto de evacuación (los tipos están en docs/API.md).
const NOMBRE_TIPO = {
  hospital: "Hospital",
  clinica: "Clínica",
  bomberos: "Bomberos",
  carabineros: "Carabineros",
  colegio: "Colegio",
  punto_encuentro: "Punto de encuentro"
};

// Nombres legibles para los tipos de reporte ciudadano (los mismos del formulario en mapa.html).
const NOMBRE_TIPO_REPORTE = {
  anegamiento: "Calle anegada",
  calle_cortada: "Calle cortada",
  arbol_caido: "Árbol caído",
  puente_cortado: "Puente cortado"
};

// Lee un color de app.css, así los colores se definen en un solo lugar.
function color(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

// Arma el contenido de un popup con texto plano. Los nombres vienen de OpenStreetMap,
// así que no los metemos como HTML (un nombre con "<" podría romper la página).
function textoPopup(titulo, detalle) {
  const caja = document.createElement("div");
  const fuerte = document.createElement("strong");
  fuerte.textContent = titulo;
  caja.appendChild(fuerte);
  caja.appendChild(document.createElement("br"));
  caja.appendChild(document.createTextNode(detalle));
  return caja;
}

// Leaflet pide los límites como [[sur, oeste], [norte, este]].
function limitesDeZona(zona) {
  return [[zona.sur, zona.oeste], [zona.norte, zona.este]];
}

// Al encuadrar algo se deja libre lo que tapa el mapa, para que la ruta o un punto no queden escondidos:
// en escritorio, el panel que flota a la izquierda (16 px de margen + su ancho) y la leyenda de abajo;
// en el celular, la cabecera que flota arriba (ahí el panel va debajo del mapa).
DryRoute.opcionesDeEncuadre = function () {
  const panel = document.getElementById("panel");
  const leyenda = document.getElementById("leyenda");
  const cabecera = document.querySelector(".cabecera");
  if (window.innerWidth >= 768) {
    return { paddingTopLeft: [16 + panel.offsetWidth + 40, 40], paddingBottomRight: [40, leyenda.offsetHeight + 40] };
  }
  return { paddingTopLeft: [24, cabecera.offsetHeight + 24], paddingBottomRight: [24, 32] };
};

// ---------- Crear el mapa ----------
// La zona la escribe la vista en la página (json_script de Django): el mapa se encuadra sin esperar al servidor
DryRoute.zona = JSON.parse(document.getElementById("zona-datos").textContent);
// preferCanvas: los círculos y puntos se pintan en un solo lienzo en vez de uno por uno.
// Con miles de puntos de evacuación (zona ampliada, T28) el mapa se mueve fluido igual.
// El zoom va abajo a la derecha: a la izquierda (en escritorio) queda tapado por el panel flotante
DryRoute.mapa = L.map("mapa", { preferCanvas: true, zoomControl: false });
L.control.zoom({ position: "bottomright", zoomInTitle: "Acercar", zoomOutTitle: "Alejar" }).addTo(DryRoute.mapa);

// La leyenda está escrita en mapa.html; aquí se mueve sobre el mapa, abajo a la izquierda, como un control
// de Leaflet. disableClickPropagation: un clic en la leyenda no marca un origen ni un destino.
const leyendaMapa = document.getElementById("leyenda");
const controlLeyenda = L.control({ position: "bottomleft" });
controlLeyenda.onAdd = function () {
  L.DomEvent.disableClickPropagation(leyendaMapa);
  return leyendaMapa;
};
controlLeyenda.addTo(DryRoute.mapa);

// En el celular la leyenda no cabe siempre a la vista: el botón (i) de la cabecera la abre y la cierra
const botonInfo = document.getElementById("btn-info");
botonInfo.addEventListener("click", function () {
  const abierta = document.body.classList.toggle("leyenda-abierta");
  botonInfo.setAttribute("aria-expanded", String(abierta));
});

DryRoute.mapa.fitBounds(limitesDeZona(DryRoute.zona), DryRoute.opcionesDeEncuadre());

// Teselas estándar de OpenStreetMap. La atribución es obligatoria por su licencia.
// app.css las pasa a grises suaves (.leaflet-tile-pane): así el rojo de lo anegado y el verde de la ruta
// resaltan solos. El filtro afecta solo al mapa base, no a los círculos, marcadores ni a la ruta.
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(DryRoute.mapa);

// ---------- Capas ----------
// Cada grupo de marcadores va en su propia capa. Al recargar los puntos vaciamos las capas y dibujamos
// de nuevo: así un punto nunca queda dibujado dos veces.
const capaAnegados = L.layerGroup().addTo(DryRoute.mapa);   // anegados y puntos de riesgo
const capaReportes = L.layerGroup().addTo(DryRoute.mapa);   // reportes que aún no se confirman

// Los puntos de evacuación se muestran solo al acercarse: con el mapa alejado serían una mancha verde.
// (El punto elegido como resultado lo dibuja resultado.js en su propia capa, así que siempre se ve.)
const capaServicios = L.layerGroup();  // salud, bomberos, Carabineros
const capaColegios = L.layerGroup();   // colegios y puntos de encuentro
const ZOOM_SERVICIOS = 14;
const ZOOM_COLEGIOS = 16;

// Las zonas anegadas se dibujan en SVG y no en el lienzo (preferCanvas): así pueden rellenarse con el
// patrón de olas de mapa.html. Son pocas comparadas con los miles de puntos de evacuación.
const rendererAgua = L.svg();

// Círculo celeste con una gota blanca en el centro de cada zona anegada (los estilos están en app.css)
const ICONO_ANEGADO = L.divIcon({ className: "icono-anegado", iconSize: [28, 28] });

// Triángulo ámbar con "!", como una señal de advertencia: forma, color y símbolo distintos
// de la gota celeste (anegado) y del círculo ámbar con que reporte.js marca el lugar elegido.
const ICONO_REPORTE_PENDIENTE = L.divIcon({
  className: "icono-reporte-pendiente",
  html: "!",
  iconSize: [28, 26]
});

// Solo la primera vez encuadramos la zona: si se recargan los puntos, el mapa queda donde la persona lo dejó.
let primeraCarga = true;

// ---------- Dibujar los puntos ----------
function dibujarPuntos(datos) {
  DryRoute.zona = datos.zona;
  if (primeraCarga) {
    DryRoute.mapa.fitBounds(limitesDeZona(DryRoute.zona), DryRoute.opcionesDeEncuadre());
    primeraCarga = false;
  }

  for (const capa of [capaAnegados, capaReportes, capaServicios, capaColegios]) {
    capa.clearLayers();
  }

  for (const punto of datos.anegados) {
    if (punto.activo) {
      // Anegado ahora: círculo con olas del tamaño del radio de bloqueo, para que se vea qué zona evita
      // la ruta, y una gota en el centro, que se ve aunque el mapa esté alejado y el círculo sea chico.
      L.circle([punto.lat, punto.lon], {
        radius: RADIO_BLOQUEO_M,
        renderer: rendererAgua,
        className: "zona-anegada",  // app.css lo rellena con las olas
        color: color("--anegado"),
        weight: 1.5
      })
        .bindPopup(popupAnegado(punto))
        .addTo(capaAnegados);
      L.marker([punto.lat, punto.lon], { icon: ICONO_ANEGADO, title: punto.nombre, zIndexOffset: 200 })
        .bindPopup(popupAnegado(punto))
        .addTo(capaAnegados);
    } else {
      // Punto de riesgo sin agua: puntito gris, discreto, porque la ruta sí puede pasar por ahí.
      L.circleMarker([punto.lat, punto.lon], {
        radius: 6,
        color: color("--superficie"),
        fillColor: color("--inactivo"),
        fillOpacity: 1,
        weight: 2
      })
        .bindPopup(textoPopup("Punto de riesgo (sin anegamiento)", punto.nombre + textoLluvia(punto)))
        .addTo(capaAnegados);
    }
  }

  // "|| []" por si el servidor todavía no envía esta lista (T12 de Vicente): así no se cae el mapa.
  for (const reporte of datos.reportes_pendientes || []) {
    let detalle = NOMBRE_TIPO_REPORTE[reporte.tipo] || "Problema reportado";
    if (reporte.descripcion) {
      detalle += ": " + reporte.descripcion;
    }
    detalle += ". " + reporte.confirmaciones + " de " + reporte.requeridas + " confirmaciones.";
    L.marker([reporte.lat, reporte.lon], { icon: ICONO_REPORTE_PENDIENTE, title: "Reporte sin confirmar" })
      .bindPopup(textoPopup("Reporte sin confirmar (la ruta aún no lo evita)", detalle))
      .addTo(capaReportes);
  }

  for (const punto of datos.evacuacion) {
    const popup = textoPopup(NOMBRE_TIPO[punto.tipo] || "Punto de evacuación", punto.nombre);
    if (punto.tipo === "colegio" || punto.tipo === "punto_encuentro") {
      // Son la gran mayoría (más de 200): como íconos taparían el mapa, van como puntos verdes pequeños
      L.circleMarker([punto.lat, punto.lon], {
        radius: 4,
        color: color("--superficie"),
        weight: 1,
        fillColor: color("--evacuacion"),
        fillOpacity: 1
      }).bindPopup(popup).addTo(capaColegios);
    } else {
      // Cruz para salud, casa para el resto: así se distinguen sin depender solo del color.
      const esSalud = punto.tipo === "hospital" || punto.tipo === "clinica";
      const icono = L.divIcon({
        className: "icono-evacuacion",
        html: esSalud ? "+" : "⌂",
        iconSize: [24, 24]
      });
      L.marker([punto.lat, punto.lon], { icon: icono, title: punto.nombre }).bindPopup(popup).addTo(capaServicios);
    }
  }
  mostrarSegunZoom();
  mostrarAnegadosActivos(datos.anegados.filter(function (p) { return p.activo; }));
}

// ---------- Anegamientos activos en el panel ----------
// Se muestran a lo más 5: con lluvia en toda la ciudad pueden ser más de 100 y taparían el formulario.
const MAXIMO_EN_LISTA = 5;

function textoCantidadAnegados(cantidad) {
  if (cantidad === 0) {
    return "Sin anegamientos activos";
  }
  return cantidad === 1 ? "1 anegamiento activo" : cantidad + " anegamientos activos";
}

// Por qué está anegado: cuánto llueve ahí o cuántas personas lo reportaron. Si lo marcó una persona
// en el admin no se dice nada.
function detalleAnegado(punto) {
  if (punto.activado_por_lluvia && punto.lluvia_mm !== null) {
    return String(punto.lluvia_mm).replace(".", ",") + " mm/h";
  }
  if (punto.fuente === "Reportes ciudadanos") {
    return punto.confirmaciones + " reportes";
  }
  return "";
}

function mostrarAnegadosActivos(activos) {
  document.getElementById("texto-anegados").textContent = textoCantidadAnegados(activos.length);

  const seccion = document.getElementById("seccion-anegados");
  const lista = document.getElementById("lista-anegados");
  lista.replaceChildren();
  seccion.hidden = activos.length === 0;

  for (const punto of activos.slice(0, MAXIMO_EN_LISTA)) {
    // Un botón por punto: al tocarlo, el mapa se acerca a ese lugar y abre su información
    const boton = document.createElement("button");
    boton.type = "button";
    const nombre = document.createElement("span");
    nombre.className = "nombre-anegado";
    nombre.textContent = punto.nombre;  // texto plano: el nombre viene de OpenStreetMap o de un reporte
    const detalle = document.createElement("span");
    detalle.className = "detalle-anegado";
    detalle.textContent = detalleAnegado(punto);
    boton.append(nombre, detalle);
    boton.addEventListener("click", function () {
      DryRoute.mapa.setView([punto.lat, punto.lon], 16);
      L.popup().setLatLng([punto.lat, punto.lon]).setContent(popupAnegado(punto)).openOn(DryRoute.mapa);
    });
    const elemento = document.createElement("li");
    elemento.appendChild(boton);
    lista.appendChild(elemento);
  }

  const restantes = activos.length - MAXIMO_EN_LISTA;
  if (restantes > 0) {
    const mas = document.createElement("li");
    mas.className = "mas-anegados";
    mas.textContent = "y " + restantes + " más en el mapa";
    lista.appendChild(mas);
  }
}

// ". Lluvia: 7,2 mm/h" si ya se consultó la lluvia sobre el punto (F3); si no, nada.
function textoLluvia(punto) {
  if (punto.lluvia_mm === null || punto.lluvia_mm === undefined) {
    return "";
  }
  return ". Lluvia: " + String(punto.lluvia_mm).replace(".", ",") + " mm/h";
}

// Los anegados que activaron los vecinos dicen qué problema reportaron y cuántos lo confirmaron,
// y los que encendió la lluvia dicen cuánto llueve ahí (F3).
function popupAnegado(punto) {
  if (punto.fuente === "Reportes ciudadanos") {
    const tipo = NOMBRE_TIPO_REPORTE[punto.tipo] || "Problema reportado";
    return textoPopup("Anegado ahora (reporte ciudadano)", tipo + ". " + punto.confirmaciones + " confirmaciones.");
  }
  if (punto.activado_por_lluvia) {
    return textoPopup("Anegado ahora (alerta de lluvia)", punto.nombre + textoLluvia(punto));
  }
  return textoPopup("Anegado ahora", punto.nombre + textoLluvia(punto));
}

function mostrarSegunZoom() {
  const zoom = DryRoute.mapa.getZoom();
  for (const [capa, zoomMinimo] of [[capaServicios, ZOOM_SERVICIOS], [capaColegios, ZOOM_COLEGIOS]]) {
    if (zoom >= zoomMinimo) {
      capa.addTo(DryRoute.mapa);
    } else {
      capa.remove();
    }
  }
}
DryRoute.mapa.on("zoomend", mostrarSegunZoom);

// ---------- Pedir los puntos al servidor ----------
function pedirPuntos() {
  return fetch("/api/puntos/").then(function (respuesta) {
    if (!respuesta.ok) {
      throw new Error("Respuesta " + respuesta.status);
    }
    return respuesta.json();
  });
}

// Si no llegan los puntos se avisa en el panel. Nunca se muestran datos inventados: en una emergencia,
// un mapa vacío con un aviso es más honesto que uno con puntos falsos.
function mostrarErrorDePuntos() {
  if (document.getElementById("error-puntos")) {
    return;
  }
  const caja = document.createElement("p");
  caja.id = "error-puntos";
  caja.className = "tarjeta tarjeta-error";
  caja.setAttribute("role", "alert");
  caja.textContent = "⚠ No pudimos cargar los puntos anegados. Revisa que el servidor esté funcionando y recarga la página.";
  document.getElementById("texto-anegados").textContent = "Puntos no disponibles";
  document.querySelector(".estado-zona").after(caja);
}

// Lo último que llegó del servidor, como texto: si en una revisión llega lo mismo no se redibuja,
// así no se cierra cada 15 segundos el popup que la persona tenga abierto (T15).
let ultimosPuntos = "";

// Al abrir la página
pedirPuntos()
  .then(function (datos) {
    ultimosPuntos = JSON.stringify(datos);
    dibujarPuntos(datos);
    // resultado.js anota cómo está la zona al abrir: así detecta un cambio desde la primera revisión
    if (DryRoute.alRecargarPuntos) {
      DryRoute.alRecargarPuntos(datos);
    }
  })
  .catch(function (error) {
    console.error("No se pudo cargar /api/puntos/.", error);
    mostrarErrorDePuntos();
  });

// Vuelve a pedir los puntos: lo usan reporte.js (después de enviar un reporte) y resultado.js (cada 15 s).
// Si cambió algo, resultado.js recalcula la ruta en DryRoute.alRecargarPuntos(datos).
// Si una revisión falla, el mapa queda como estaba.
DryRoute.recargarPuntos = function () {
  return pedirPuntos()
    .then(function (datos) {
      // Si al abrir no habían llegado los puntos y ahora sí, se quita el aviso de error
      const error = document.getElementById("error-puntos");
      if (error) {
        error.remove();
      }
      const texto = JSON.stringify(datos);
      if (texto !== ultimosPuntos) {
        ultimosPuntos = texto;
        dibujarPuntos(datos);
      }
      if (DryRoute.alRecargarPuntos) {
        DryRoute.alRecargarPuntos(datos);
      }
      return datos;
    })
    .catch(function (error) {
      console.warn("No se pudieron recargar los puntos.", error);
      return null;
    });
};
