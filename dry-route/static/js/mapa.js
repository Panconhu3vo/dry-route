// mapa.js — Gonzalo (T3 y T14)
// Crea el mapa, guarda la zona cubierta y dibuja los puntos anegados, los de evacuación y los reportes pendientes.
// Define DryRoute.mapa, DryRoute.zona y DryRoute.recargarPuntos(), que usan los demás archivos (ver docs/API.md).

// Un solo objeto global compartido por los tres archivos JS, para no ensuciar la página con variables sueltas.
window.DryRoute = window.DryRoute || {};

// Datos de ejemplo con la misma forma que GET /api/puntos/ (docs/API.md).
// Se usan solo si el servidor todavía no tiene ese endpoint (T2 de Juan). Se quitan en T7.
const PUNTOS_DE_EJEMPLO = {
  zona: { norte: -33.490, sur: -33.545, oeste: -70.680, este: -70.635 },
  anegados: [
    { id: 1, nombre: "Paso bajo nivel Gran Avenida / Departamental", tipo: "paso_bajo_nivel", activo: true, fuente: "OpenStreetMap", confirmaciones: 0, lat: -33.5019, lon: -70.6526 },
    { id: 2, nombre: "Punto de riesgo de ejemplo (sin anegamiento)", tipo: "paso_bajo_nivel", activo: false, fuente: "OpenStreetMap", confirmaciones: 0, lat: -33.5250, lon: -70.6600 },
    { id: 9, nombre: "Reporte ciudadano: calle anegada", tipo: "anegamiento", activo: true, fuente: "Reportes ciudadanos", confirmaciones: 2, lat: -33.5101, lon: -70.6566 }
  ],
  evacuacion: [
    { id: 7, nombre: "Hospital Barros Luco", tipo: "hospital", lat: -33.5047, lon: -70.6560 },
    { id: 8, nombre: "Punto de evacuación de ejemplo", tipo: "bomberos", lat: -33.5300, lon: -70.6650 }
  ],
  reportes_pendientes: [
    { id: 12, tipo: "arbol_caido", descripcion: "Árbol sobre la calzada", lat: -33.5150, lon: -70.6580, fecha_hora: "2026-11-11T18:30:00-03:00", confirmaciones: 1, requeridas: 2 }
  ]
};

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

// ---------- Crear el mapa ----------
DryRoute.zona = PUNTOS_DE_EJEMPLO.zona; // valor provisional hasta que responda el servidor
// preferCanvas: los círculos y puntos se pintan en un solo lienzo en vez de uno por uno.
// Con miles de puntos de evacuación (zona ampliada, T28) el mapa se mueve fluido igual.
DryRoute.mapa = L.map("mapa", { preferCanvas: true });
DryRoute.mapa.fitBounds(limitesDeZona(DryRoute.zona));

// Teselas estándar de OpenStreetMap. La atribución es obligatoria por su licencia.
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

// Triángulo ámbar con "!", como una señal de advertencia: forma, color y símbolo distintos
// del círculo rojo (anegado) y del círculo ámbar con que reporte.js marca el lugar elegido.
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
    DryRoute.mapa.fitBounds(limitesDeZona(DryRoute.zona));
    primeraCarga = false;
  }

  for (const capa of [capaAnegados, capaReportes, capaServicios, capaColegios]) {
    capa.clearLayers();
  }

  for (const punto of datos.anegados) {
    if (punto.activo) {
      // Anegado ahora: círculo rojo del tamaño del radio de bloqueo, para que se vea qué zona evita la ruta.
      L.circle([punto.lat, punto.lon], {
        radius: RADIO_BLOQUEO_M,
        color: color("--peligro"),
        fillColor: color("--peligro"),
        fillOpacity: 0.35,
        weight: 2
      })
        .bindPopup(popupAnegado(punto))
        .addTo(capaAnegados);
    } else {
      // Punto de riesgo sin agua: puntito gris, discreto, porque la ruta sí puede pasar por ahí.
      L.circleMarker([punto.lat, punto.lon], {
        radius: 5,
        color: color("--inactivo"),
        fillColor: color("--inactivo"),
        fillOpacity: 0.9,
        weight: 1
      })
        .bindPopup(textoPopup("Punto de riesgo (sin anegamiento)", punto.nombre))
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
        fillColor: color("--ruta"),
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
}

// Los anegados que activaron los vecinos dicen qué problema reportaron y cuántos lo confirmaron.
function popupAnegado(punto) {
  if (punto.fuente === "Reportes ciudadanos") {
    const tipo = NOMBRE_TIPO_REPORTE[punto.tipo] || "Problema reportado";
    return textoPopup("Anegado ahora (reporte ciudadano)", tipo + ". " + punto.confirmaciones + " confirmaciones.");
  }
  return textoPopup("Anegado ahora", punto.nombre);
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

// Al abrir la página: si el endpoint aún no existe o falla, usa los de ejemplo
// para que el front se pueda probar sin esperar al backend.
// Lo último que llegó del servidor, como texto: si en una revisión llega lo mismo no se redibuja,
// así no se cierra cada 15 segundos el popup que la persona tenga abierto (T15).
let ultimosPuntos = "";

pedirPuntos()
  .catch(function (error) {
    console.warn("No se pudo cargar /api/puntos/, se usan datos de ejemplo.", error);
    return PUNTOS_DE_EJEMPLO;
  })
  .then(function (datos) {
    ultimosPuntos = JSON.stringify(datos);
    dibujarPuntos(datos);
    // resultado.js anota cómo está la zona al abrir: así detecta un cambio desde la primera revisión
    if (DryRoute.alRecargarPuntos) {
      DryRoute.alRecargarPuntos(datos);
    }
  });

// Vuelve a pedir los puntos: lo usan reporte.js (después de enviar un reporte) y resultado.js (cada 15 s).
// Si cambió algo, resultado.js recalcula la ruta en DryRoute.alRecargarPuntos(datos).
// Aquí no usamos los datos de ejemplo: si falla, es mejor dejar el mapa como estaba que mostrar datos falsos.
DryRoute.recargarPuntos = function () {
  return pedirPuntos()
    .then(function (datos) {
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
