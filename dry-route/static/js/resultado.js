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

// Ícono de app.css ("escudo", "ruta", "advertencia", "casa"...). Es decorativo: el texto de al lado ya dice lo mismo.
function crearIcono(nombre) {
  const icono = crear("span", "icono icono-" + nombre, "");
  icono.setAttribute("aria-hidden", "true");
  return icono;
}

// Título con ícono + texto: el estado nunca se comunica solo con color (docs/DISENO.md).
function crearTitulo(icono, texto) {
  const titulo = crear("h2", "tarjeta-titulo", "");
  titulo.append(crearIcono(icono), texto);
  return titulo;
}

// "Desde: Tu ubicación / Hasta: Metro Lo Ovalle": recuerda qué ruta se está mirando.
// Los textos son los de los campos de entrada.js (una dirección o "Punto marcado en el mapa").
function crearResumen(hasta) {
  const lista = crear("ul", "resumen-viaje", "");
  const filas = [
    ["marca-desde", "Desde", document.getElementById("input-origen").value || "Origen"],
    ["marca-hasta", "Hasta", hasta]
  ];
  for (const [marca, etiqueta, lugar] of filas) {
    const fila = document.createElement("li");
    const simbolo = crear("span", marca, "");
    simbolo.setAttribute("aria-hidden", "true");
    fila.append(simbolo, crear("span", "etiqueta", etiqueta), crear("span", "lugar", lugar));
    lista.appendChild(fila);
  }
  return lista;
}

// Ruta segura: "17 min" grande (lo que más importa al evacuar), la distancia y cuántos anegados evita.
function crearTarjetaSegura(r) {
  const tarjeta = crear("div", "tarjeta tarjeta-segura", "");
  tarjeta.appendChild(crearTitulo("escudo", "Ruta segura"));

  const cifras = crear("p", "tarjeta-cifras", "");
  const tiempo = crear("span", "cifra-principal", String(r.tiempo_min));
  tiempo.appendChild(crear("small", "", "min"));
  cifras.append(tiempo, crear("span", "cifra-secundaria", formatoDistancia(r.distancia_m)));
  tarjeta.appendChild(cifras);

  const evita = crear("p", "etiqueta-evita", "");
  evita.append(crearIcono("ruta"), textoPuntosEvitados(r.puntos_evitados.length));
  tarjeta.appendChild(evita);
  return tarjeta;
}

// Sin ruta segura o en zona de peligro: borde rojo con la advertencia y el mensaje del servidor.
function crearTarjetaSinRuta(titulo, mensaje, clase) {
  const tarjeta = crear("div", "tarjeta " + clase, "");
  const circulo = crear("span", "circulo-advertencia", "");
  circulo.appendChild(crearIcono("advertencia"));
  const texto = crear("div", "tarjeta-texto", "");
  // El mensaje lo escribe el servidor: explica qué pasó (por ejemplo, que no hay punto alcanzable).
  texto.append(crear("h2", "tarjeta-titulo", titulo), crear("p", "tarjeta-detalle", mensaje));
  tarjeta.append(circulo, texto);
  return tarjeta;
}

// "PUNTO DE EVACUACIÓN · Hospital Barros Luco · 1,1 km · 14 min"
function crearFilaEvacuacion(r) {
  const fila = crear("div", "fila-evacuacion", "");
  const circulo = crear("span", "circulo-casa", "");
  circulo.appendChild(crearIcono("casa"));
  const texto = crear("div", "fila-evacuacion-texto", "");
  texto.append(crear("span", "etiqueta", "Punto de evacuación"), crear("strong", "", r.punto_evacuacion.nombre));
  const cifras = crear("p", "fila-evacuacion-cifras", formatoDistancia(r.distancia_m));
  cifras.appendChild(crear("span", "", r.tiempo_min + " min"));
  fila.append(circulo, texto, cifras);
  return fila;
}

// La ruta va en SVG y no en el lienzo (preferCanvas de mapa.js): así el borde blanco puede llevar
// una sombra hecha con CSS (.ruta-borde en app.css), que la despega del mapa.
const rendererRuta = L.svg();

// La línea va dos veces: una blanca y gruesa abajo, y la azul encima.
// El borde blanco hace que la ruta se lea sobre cualquier calle del mapa.
function dibujarRuta(puntos) {
  const estilo = { opacity: 1, lineJoin: "round", lineCap: "round", renderer: rendererRuta };
  L.polyline(puntos, Object.assign({ color: colorCss("--superficie"), weight: 12, className: "ruta-borde" }, estilo))
    .addTo(capaResultado);
  L.polyline(puntos, Object.assign({ color: colorCss("--ruta"), weight: 7 }, estilo)).addTo(capaResultado);
}

// Círculo azul grande sobre el punto elegido, con cruz (salud) o casa: es el final de la ruta.
function resaltarPuntoEvacuacion(punto) {
  const esSalud = punto.tipo === "hospital" || punto.tipo === "clinica";
  const icono = L.divIcon({
    className: "icono-evacuacion-resaltado",
    html: '<span class="icono icono-' + (esSalud ? "cruz" : "casa") + '"></span>',
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
// elementos: lo que va en el resultado, en orden (resumen, tarjeta, fila del punto de evacuación...).
function mostrarTarjeta(elementos, conBotonNuevaRuta) {
  if (conBotonNuevaRuta) {
    const boton = crear("button", "boton boton-secundario", "Nueva ruta");
    boton.type = "button";
    boton.addEventListener("click", DryRoute.limpiarResultado);
    elementos.push(boton);
  }
  cajaResultado.replaceChildren(...elementos);
  cajaResultado.hidden = false;
}

// r es la respuesta 200 de /api/ruta/, con estado "segura", "sin_ruta" o "en_peligro".
DryRoute.mostrarResultado = function (r) {
  DryRoute.limpiarResultado(); // borra una ruta anterior, si había
  const elementos = [];

  if (r.estado === "segura") {
    elementos.push(crearResumen(document.getElementById("input-destino").value || "Destino"));
    elementos.push(crearTarjetaSegura(r));
  } else {
    // "en_peligro": el origen está en una zona anegada y la prioridad es salir, no llegar al destino
    const titulo = r.estado === "en_peligro" ? "Estás en una zona de peligro" : "No hay ruta segura a tu destino";
    elementos.push(crearTarjetaSinRuta(titulo, r.mensaje, "tarjeta-sin-ruta"));
    if (r.punto_evacuacion) {
      elementos.push(crearFilaEvacuacion(r));
    }
  }

  // Si esta ruta viene de un recálculo automático (T15), se avisa arriba de todo
  if (avisoRecalculoPendiente) {
    const aviso = crear("p", "aviso-recalculo", "↻ Cambiaron los puntos anegados de la zona. Ruta recalculada.");
    aviso.setAttribute("role", "status");
    elementos.unshift(aviso);
    avisoRecalculoPendiente = false;
  }

  // El encuadre incluye la ruta y, si hay, el punto de evacuación: así ambos quedan a la vista.
  const encuadre = L.latLngBounds(r.ruta);
  // Con "sin_ruta" la ruta puede venir vacía si no hay ningún punto alcanzable.
  if (r.ruta.length > 0) {
    dibujarRuta(r.ruta);
  }
  if (r.estado !== "segura" && r.punto_evacuacion) {
    encuadre.extend([r.punto_evacuacion.lat, r.punto_evacuacion.lon]);
  }

  mostrarFormulario(false);
  mostrarTarjeta(elementos, true);
  hayRutaEnPantalla = true;

  if (encuadre.isValid()) {
    // Deja libre lo que tapa el mapa (la leyenda o la cabecera, ver mapa.js), para que nada quede escondido.
    // Va después de mostrar la tarjeta: en el celular el panel cambia de alto y con él, el espacio del mapa.
    DryRoute.mapa.invalidateSize();
    DryRoute.mapa.fitBounds(encuadre, Object.assign(DryRoute.opcionesDeEncuadre(), { maxZoom: 17 }));
  }
  // Va después de fitBounds para que el popup se abra ya en el encuadre final.
  if (r.estado !== "segura" && r.punto_evacuacion) {
    resaltarPuntoEvacuacion(r.punto_evacuacion);
  }
};

// Para errores (respuesta 400, sin conexión, dirección no encontrada) el formulario sigue visible:
// la persona tiene que corregir el origen o el destino, así que no le escondemos los campos.
DryRoute.mostrarError = function (mensaje) {
  capaResultado.clearLayers();
  hayRutaEnPantalla = false;
  avisoRecalculoPendiente = false;
  mostrarFormulario(true);
  const tarjeta = crearTarjetaSinRuta("No pudimos calcular la ruta", mensaje, "tarjeta-error");
  tarjeta.setAttribute("role", "alert"); // un error se anuncia de inmediato, no "cuando se pueda"
  mostrarTarjeta([tarjeta], false);
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
  hayRutaEnPantalla = false;
  // En el celular el panel cambió de alto: Leaflet tiene que volver a medir el mapa para dibujarlo completo
  DryRoute.mapa.invalidateSize();
};

// ---------- Recálculo automático (T15, pantalla 5 del prototipo) ----------
// Si cambian los puntos anegados (otra persona confirmó un reporte, alguien activó un punto en el admin,
// un reporte venció o cambió la lluvia) y hay una ruta en pantalla, la ruta se recalcula sola y se avisa.
const SEGUNDOS_ENTRE_REVISIONES = 15;
let firmaAnegados = null;          // ids de los anegados activos la última vez, como texto: "3,9,15"
let hayRutaEnPantalla = false;
let avisoRecalculoPendiente = false;

function firmaDeAnegados(datos) {
  return datos.anegados.filter(function (p) { return p.activo; })
    .map(function (p) { return p.id; })
    .sort(function (a, b) { return a - b; })
    .join(",");
}

// mapa.js la llama cada vez que trae los puntos del servidor (al abrir la página y en cada revisión).
DryRoute.alRecargarPuntos = function (datos) {
  const firma = firmaDeAnegados(datos);
  // La primera vez solo se anota cómo estaba la zona: todavía no hay con qué comparar
  const cambio = firmaAnegados !== null && firma !== firmaAnegados;
  firmaAnegados = firma;
  if (cambio && hayRutaEnPantalla && DryRoute.calcularRuta) {
    avisoRecalculoPendiente = true;
    DryRoute.calcularRuta();
  }
};

// Cada 15 segundos se vuelven a pedir los puntos, para que esta ventana se entere de lo que reportan otras
// personas. Si la pestaña está escondida no se pregunta: nadie está mirando el mapa.
setInterval(function () {
  if (!document.hidden) {
    DryRoute.recargarPuntos();
  }
}, SEGUNDOS_ENTRE_REVISIONES * 1000);
