// resultado.js — Yusu (T5)
// Muestra la respuesta de GET /api/ruta/: dibuja la ruta en el mapa y llena la tarjeta de resultado.
// Define DryRoute.mostrarResultado, DryRoute.mostrarError y DryRoute.limpiarResultado (ver docs/API.md).
// Necesita que mapa.js se haya cargado antes, porque usa DryRoute.mapa.

window.DryRoute = window.DryRoute || {};

const cajaResultado = document.getElementById("resultado");
const formulario = document.getElementById("form-ruta");

// Todo lo que dibuja este archivo va en una sola capa: así se borra de una vez con "Nueva ruta",
// sin tocar los puntos que dibujó mapa.js.
const capaResultado = L.layerGroup().addTo(DryRoute.mapa);

// Lee un color de app.css, así los colores se definen en un solo lugar.
function colorCss(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

// 650 -> "650 m", 4200 -> "4,2 km" (con coma decimal, como se escribe en Chile).
function formatoDistancia(metros) {
  if (metros < 1000) {
    return metros + " m";
  }
  return (metros / 1000).toFixed(1).replace(".", ",") + " km";
}

function textoPuntosEvitados(cantidad) {
  if (cantidad === 0) {
    return "No hay puntos anegados en tu camino";
  }
  if (cantidad === 1) {
    return "Evita 1 punto anegado";
  }
  return "Evita " + cantidad + " puntos anegados";
}

// Crea un elemento con texto plano. Los nombres vienen de OpenStreetMap,
// así que nunca los metemos como HTML (un nombre con "<" podría romper la página).
function crear(etiqueta, clase, texto) {
  const elemento = document.createElement(etiqueta);
  elemento.className = clase;
  elemento.textContent = texto;
  return elemento;
}

// Título con ícono + texto: el estado nunca se comunica solo con color (docs/DISENO.md).
function crearTitulo(icono, texto) {
  const titulo = crear("h2", "tarjeta-titulo", "");
  const simbolo = crear("span", "tarjeta-icono", icono);
  simbolo.setAttribute("aria-hidden", "true"); // el lector de pantalla ya lee el texto
  titulo.appendChild(simbolo);
  titulo.appendChild(document.createTextNode(" " + texto));
  return titulo;
}

// La línea va dos veces: una blanca y gruesa abajo, y la verde encima.
// El borde blanco hace que la ruta se lea sobre cualquier calle del mapa.
function dibujarRuta(puntos) {
  L.polyline(puntos, { color: colorCss("--superficie"), weight: 10, opacity: 1 }).addTo(capaResultado);
  L.polyline(puntos, { color: colorCss("--ruta"), weight: 6, opacity: 1 }).addTo(capaResultado);
}

// Marcador más grande encima del que ya dibujó mapa.js, para que se note cuál es el elegido.
function resaltarPuntoEvacuacion(punto) {
  const esSalud = punto.tipo === "hospital" || punto.tipo === "clinica";
  const icono = L.divIcon({
    className: "icono-evacuacion icono-evacuacion-resaltado",
    html: esSalud ? "+" : "⌂",
    iconSize: [40, 40]
  });
  L.marker([punto.lat, punto.lon], { icon: icono, title: punto.nombre, zIndexOffset: 1000 })
    // autoPan: false para que el popup no mueva el mapa después de encuadrar la ruta.
    .bindPopup(crear("strong", "", "Ir aquí: " + punto.nombre), { autoPan: false })
    .addTo(capaResultado)
    .openPopup();
}

// Usamos style.display y no el atributo hidden porque app.css le pone display: flex al
// formulario, y esa regla le gana a hidden (el formulario no se escondería).
function mostrarFormulario(visible) {
  formulario.style.display = visible ? "" : "none";
}

// El panel muestra el formulario o el resultado, nunca los dos (docs/DISENO.md).
function mostrarTarjeta(tarjeta, conBotonNuevaRuta) {
  if (conBotonNuevaRuta) {
    const boton = crear("button", "boton boton-principal", "Nueva ruta");
    boton.type = "button";
    boton.addEventListener("click", DryRoute.limpiarResultado);
    tarjeta.appendChild(boton);
  }
  cajaResultado.replaceChildren(tarjeta);
  cajaResultado.hidden = false;
}

// r es la respuesta 200 de /api/ruta/, con estado "segura" o "sin_ruta".
DryRoute.mostrarResultado = function (r) {
  DryRoute.limpiarResultado(); // borra una ruta anterior, si había
  const tarjeta = document.createElement("div");

  if (r.estado === "segura") {
    tarjeta.className = "tarjeta tarjeta-segura";
    tarjeta.appendChild(crearTitulo("✓", "Ruta segura"));
    tarjeta.appendChild(crear("p", "tarjeta-datos",
      formatoDistancia(r.distancia_m) + " · " + r.tiempo_min + " min"));
    tarjeta.appendChild(crear("p", "tarjeta-detalle", textoPuntosEvitados(r.puntos_evitados.length)));
  } else {
    tarjeta.className = "tarjeta tarjeta-sin-ruta";
    tarjeta.appendChild(crearTitulo("⚠", "No hay ruta segura a tu destino"));
    // El mensaje lo escribe el servidor: explica qué pasó (por ejemplo, que no hay punto alcanzable).
    tarjeta.appendChild(crear("p", "tarjeta-detalle", r.mensaje));
    if (r.punto_evacuacion) {
      tarjeta.appendChild(crear("p", "tarjeta-datos",
        "Ir al punto de evacuación: " + r.punto_evacuacion.nombre));
      tarjeta.appendChild(crear("p", "tarjeta-detalle",
        "A " + formatoDistancia(r.distancia_m) + " · " + r.tiempo_min + " min"));
    }
  }

  // El encuadre incluye la ruta y, si hay, el punto de evacuación: así ambos quedan a la vista.
  const encuadre = L.latLngBounds(r.ruta);
  // Con "sin_ruta" la ruta puede venir vacía si no hay ningún punto alcanzable.
  if (r.ruta.length > 0) {
    dibujarRuta(r.ruta);
  }
  if (r.estado === "sin_ruta" && r.punto_evacuacion) {
    encuadre.extend([r.punto_evacuacion.lat, r.punto_evacuacion.lon]);
  }
  if (encuadre.isValid()) {
    // El padding deja espacio para que nada quede pegado al borde del mapa.
    DryRoute.mapa.fitBounds(encuadre, { padding: [40, 40], maxZoom: 17 });
  }
  // Va después de fitBounds para que el popup se abra ya en el encuadre final.
  if (r.estado === "sin_ruta" && r.punto_evacuacion) {
    resaltarPuntoEvacuacion(r.punto_evacuacion);
  }

  mostrarFormulario(false);
  mostrarTarjeta(tarjeta, true);
};

// Para errores (respuesta 400, sin conexión, dirección no encontrada) el formulario sigue visible:
// la persona tiene que corregir el origen o el destino, así que no le escondemos los campos.
DryRoute.mostrarError = function (mensaje) {
  capaResultado.clearLayers();
  mostrarFormulario(true);
  const tarjeta = document.createElement("div");
  tarjeta.className = "tarjeta tarjeta-error";
  tarjeta.setAttribute("role", "alert"); // un error se anuncia de inmediato, no "cuando se pueda"
  tarjeta.appendChild(crearTitulo("⚠", "No pudimos calcular la ruta"));
  tarjeta.appendChild(crear("p", "tarjeta-detalle", mensaje));
  mostrarTarjeta(tarjeta, false);
  // En el celular el panel es bajo y el error queda debajo del formulario: lo traemos a la vista.
  tarjeta.scrollIntoView({ block: "nearest" });
};

// Vuelve al estado inicial: sin ruta dibujada, sin tarjeta y con el formulario a la vista.
// No borra el origen ni el destino: eso le toca a entrada.js (Cristóbal).
DryRoute.limpiarResultado = function () {
  capaResultado.clearLayers();
  cajaResultado.replaceChildren();
  cajaResultado.hidden = true;
  mostrarFormulario(true);
};
