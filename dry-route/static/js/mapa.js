// mapa.js — Gonzalo (T3)
// Crea el mapa, guarda la zona cubierta y dibuja los puntos anegados y de evacuación.
// Define DryRoute.mapa y DryRoute.zona, que usan resultado.js y entrada.js (ver docs/API.md).

// Un solo objeto global compartido por los tres archivos JS, para no ensuciar la página con variables sueltas.
window.DryRoute = window.DryRoute || {};

// Datos de ejemplo con la misma forma que GET /api/puntos/ (docs/API.md).
// Se usan solo si el servidor todavía no tiene ese endpoint (T2 de Juan). Se quitan en T7.
const PUNTOS_DE_EJEMPLO = {
  zona: { norte: -33.490, sur: -33.545, oeste: -70.680, este: -70.635 },
  anegados: [
    { id: 1, nombre: "Paso bajo nivel Gran Avenida / Departamental", tipo: "paso_bajo_nivel", activo: true, lat: -33.5019, lon: -70.6526 },
    { id: 2, nombre: "Punto de riesgo de ejemplo (sin anegamiento)", tipo: "paso_bajo_nivel", activo: false, lat: -33.5250, lon: -70.6600 }
  ],
  evacuacion: [
    { id: 7, nombre: "Hospital Barros Luco", tipo: "hospital", lat: -33.5047, lon: -70.6560 },
    { id: 8, nombre: "Punto de evacuación de ejemplo", tipo: "bomberos", lat: -33.5300, lon: -70.6650 }
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
DryRoute.mapa = L.map("mapa");
DryRoute.mapa.fitBounds(limitesDeZona(DryRoute.zona));

// Teselas estándar de OpenStreetMap. La atribución es obligatoria por su licencia.
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(DryRoute.mapa);

// ---------- Dibujar los puntos ----------
function dibujarPuntos(datos) {
  DryRoute.zona = datos.zona;
  DryRoute.mapa.fitBounds(limitesDeZona(DryRoute.zona));

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
        .bindPopup(textoPopup("Anegado ahora", punto.nombre))
        .addTo(DryRoute.mapa);
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
        .addTo(DryRoute.mapa);
    }
  }

  for (const punto of datos.evacuacion) {
    // Cruz para salud, casa para el resto: así se distinguen sin depender solo del color.
    const esSalud = punto.tipo === "hospital" || punto.tipo === "clinica";
    const icono = L.divIcon({
      className: "icono-evacuacion",
      html: esSalud ? "+" : "⌂",
      iconSize: [26, 26]
    });
    L.marker([punto.lat, punto.lon], { icon: icono, title: punto.nombre })
      .bindPopup(textoPopup(NOMBRE_TIPO[punto.tipo] || "Punto de evacuación", punto.nombre))
      .addTo(DryRoute.mapa);
  }
}

// Pide los puntos al servidor. Si el endpoint aún no existe o falla, usa los de ejemplo
// para que el front se pueda probar sin esperar al backend.
fetch("/api/puntos/")
  .then(function (respuesta) {
    if (!respuesta.ok) {
      throw new Error("Respuesta " + respuesta.status);
    }
    return respuesta.json();
  })
  .catch(function (error) {
    console.warn("No se pudo cargar /api/puntos/, se usan datos de ejemplo.", error);
    return PUNTOS_DE_EJEMPLO;
  })
  .then(dibujarPuntos);
