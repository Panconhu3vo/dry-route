// entrada.js — Cristóbal (T4)
// Panel de entrada: fija el origen y el destino con el GPS, buscando una dirección o con clic en el mapa,
// y al presionar "Calcular ruta" le pide la ruta al servidor.
// Define DryRoute.origen y DryRoute.destino ({lat, lon} o null). Usa DryRoute.mapa, DryRoute.zona y las
// funciones de resultado.js (ver docs/API.md), por eso se carga después de mapa.js y resultado.js.
//
// Ojo: los tres archivos JS comparten los nombres globales. Si aquí declaramos una función o constante con
// el mismo nombre que en mapa.js o resultado.js, una pisa a la otra. Por eso los nombres son distintos.

window.DryRoute = window.DryRoute || {};

DryRoute.origen = null;
DryRoute.destino = null;

const formularioRuta = document.getElementById("form-ruta");
const inputOrigen = document.getElementById("input-origen");
const inputDestino = document.getElementById("input-destino");
const botonGps = document.getElementById("btn-gps");
const botonCalcular = document.getElementById("btn-calcular");

const NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";

const MENSAJE_GPS_FUERA = "Tu ubicación está fuera de la zona cubierta. Marca tu origen en el mapa."; // DECISIONES D9
const MENSAJE_PUNTO_FUERA = "Ese punto está fuera de la zona cubierta. Marca un punto dentro del área.";
const MENSAJE_NO_ENCONTRADA = "No encontramos esa dirección. Prueba con calle y número, o marca el punto en el mapa.";

// Guardamos las cosas de origen y destino en objetos con las mismas claves ("origen" y "destino"),
// así una sola función sirve para los dos campos.
const camposTexto = { origen: inputOrigen, destino: inputDestino };
const marcadores = { origen: null, destino: null };

// El origen es un círculo azul y el destino una bandera verde (docs/DISENO.md): cambian la forma y no solo el color.
// Los estilos van aquí y no en app.css porque ese archivo es de Gonzalo.
const ICONO_ORIGEN = L.divIcon({
  className: "",
  html: '<div style="width:22px;height:22px;border-radius:50%;background:var(--agua);' +
        'border:3px solid var(--superficie);box-shadow:0 0 0 6px rgb(11 99 196 / 0.3)"></div>',
  iconSize: [22, 22]
});
const ICONO_DESTINO = L.divIcon({
  className: "",
  html: '<div style="font-size:34px;line-height:1;color:var(--ruta);' +
        'text-shadow:0 0 3px var(--superficie),0 0 3px var(--superficie)">⚑</div>',
  iconSize: [34, 34],
  iconAnchor: [8, 32] // el palo de la bandera queda justo sobre el punto marcado
});

// ---------- Mensajes del panel (buscando, no encontrada, fuera de zona) ----------
// Lo creamos desde aquí para no tener que cambiar mapa.html, que es de Gonzalo.
const mensajeEntrada = document.createElement("p");
mensajeEntrada.setAttribute("role", "status"); // el lector de pantalla lo lee cuando cambia
mensajeEntrada.style.margin = "0";
mensajeEntrada.hidden = true;
formularioRuta.insertBefore(mensajeEntrada, botonCalcular);

function mostrarMensaje(texto, esError) {
  // Un error lleva ícono y negrita además del color rojo: nunca solo color (docs/DISENO.md).
  mensajeEntrada.textContent = esError ? "⚠ " + texto : texto;
  mensajeEntrada.style.color = esError ? "var(--peligro)" : "var(--texto)";
  mensajeEntrada.style.fontWeight = esError ? "700" : "400";
  mensajeEntrada.hidden = false;
}

function ocultarMensaje() {
  mensajeEntrada.hidden = true;
}

// ---------- Zona cubierta ----------
// Se lee DryRoute.zona cada vez (y no una sola vez al inicio) porque mapa.js la actualiza
// cuando llega la respuesta de /api/puntos/.
function estaEnZona(lat, lon) {
  const zona = DryRoute.zona;
  return lat <= zona.norte && lat >= zona.sur && lon >= zona.oeste && lon <= zona.este;
}

// ---------- Origen y destino ----------
// cual es "origen" o "destino".
function fijarPunto(cual, lat, lon, texto) {
  DryRoute[cual] = { lat: lat, lon: lon };
  camposTexto[cual].value = texto;
  if (marcadores[cual]) {
    marcadores[cual].setLatLng([lat, lon]);
  } else {
    marcadores[cual] = crearMarcador(cual, lat, lon);
  }
  ocultarMensaje();
  DryRoute.limpiarResultado(); // una ruta o un error anterior ya no corresponden a estos puntos
  actualizarBotonCalcular();
}

function quitarPunto(cual) {
  DryRoute[cual] = null;
  if (marcadores[cual]) {
    marcadores[cual].remove();
    marcadores[cual] = null;
  }
  DryRoute.limpiarResultado();
  actualizarBotonCalcular();
}

function crearMarcador(cual, lat, lon) {
  const marcador = L.marker([lat, lon], {
    icon: cual === "origen" ? ICONO_ORIGEN : ICONO_DESTINO,
    title: cual === "origen" ? "Origen" : "Destino",
    draggable: true,
    zIndexOffset: 500 // encima de los puntos de mapa.js, para poder agarrarlo
  }).addTo(DryRoute.mapa);

  // Leaflet llama "lng" a la longitud; nosotros la guardamos como "lon", igual que en docs/API.md.
  marcador.on("dragend", function () {
    const posicion = marcador.getLatLng();
    if (estaEnZona(posicion.lat, posicion.lng)) {
      fijarPunto(cual, posicion.lat, posicion.lng, "Punto marcado en el mapa");
    } else {
      // Fuera de la zona no hay calles en el grafo: devolvemos el marcador a donde estaba.
      marcador.setLatLng([DryRoute[cual].lat, DryRoute[cual].lon]);
      mostrarMensaje(MENSAJE_PUNTO_FUERA, true);
    }
  });
  return marcador;
}

// ---------- Clic en el mapa ----------
// Primer clic: origen. Segundo clic: destino. Si ya están los dos, el clic cambia el destino.
DryRoute.mapa.on("click", function (evento) {
  const lat = evento.latlng.lat;
  const lon = evento.latlng.lng;
  if (!estaEnZona(lat, lon)) {
    mostrarMensaje(MENSAJE_PUNTO_FUERA, true);
    return;
  }
  const cual = DryRoute.origen === null ? "origen" : "destino";
  fijarPunto(cual, lat, lon, "Punto marcado en el mapa");
});

// ---------- Usar mi ubicación (GPS) ----------
botonGps.addEventListener("click", function () {
  if (!navigator.geolocation) {
    mostrarMensaje("Tu navegador no permite usar tu ubicación. Marca tu origen en el mapa.", true);
    return;
  }
  mostrarMensaje("Buscando tu ubicación…", false);
  botonGps.disabled = true; // evita pedir la ubicación varias veces seguidas

  // getCurrentPosition no responde al tiro: recibe una función para cuando hay ubicación y otra para cuando falla.
  navigator.geolocation.getCurrentPosition(
    function (posicion) {
      botonGps.disabled = false;
      const lat = posicion.coords.latitude;
      const lon = posicion.coords.longitude;
      if (!estaEnZona(lat, lon)) {
        mostrarMensaje(MENSAJE_GPS_FUERA, true);
        return;
      }
      fijarPunto("origen", lat, lon, "Mi ubicación");
      DryRoute.mapa.setView([lat, lon], 16);
    },
    function () {
      botonGps.disabled = false;
      mostrarMensaje("No pudimos obtener tu ubicación. Revisa el permiso del navegador o marca tu origen en el mapa.", true);
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

// ---------- Búsqueda de direcciones (Nominatim) ----------
// Nominatim pide máximo 1 consulta por segundo y prohíbe buscar mientras se escribe (DECISIONES D7).
// Por eso solo se busca al presionar Enter, y guardamos la hora de la última búsqueda.
let horaUltimaBusqueda = 0;

// Una lista de resultados debajo de cada campo, creada desde aquí (mapa.html es de Gonzalo).
function crearListaResultados(input) {
  const lista = document.createElement("div");
  lista.style.display = "flex";
  lista.style.flexDirection = "column";
  lista.style.gap = "8px";
  input.parentElement.appendChild(lista);
  return lista;
}
const listasResultados = {
  origen: crearListaResultados(inputOrigen),
  destino: crearListaResultados(inputDestino)
};

// "Gran Avenida 5000, San Miguel, Provincia de Santiago, Región Metropolitana, 8900000, Chile"
// -> "Gran Avenida 5000, San Miguel, Provincia de Santiago". Lo demás no ayuda a elegir y ocupa espacio.
function nombreCorto(nombreCompleto) {
  return nombreCompleto.split(", ").slice(0, 3).join(", ");
}

function buscarDireccion(cual) {
  const texto = camposTexto[cual].value.trim();
  if (texto === "") {
    return;
  }
  if (Date.now() - horaUltimaBusqueda < 1000) {
    mostrarMensaje("Espera un segundo antes de buscar otra vez.", false);
    return;
  }
  horaUltimaBusqueda = Date.now();

  const zona = DryRoute.zona;
  const parametros = new URLSearchParams({
    q: texto,
    format: "jsonv2",
    countrycodes: "cl",
    // viewbox va como oeste,norte,este,sur; con bounded=1 solo devuelve lugares dentro de la zona.
    viewbox: zona.oeste + "," + zona.norte + "," + zona.este + "," + zona.sur,
    bounded: "1",
    limit: "5",
    "accept-language": "es"
  });

  mostrarMensaje("Buscando…", false);
  fetch(NOMINATIM_URL + "?" + parametros)
    .then(function (respuesta) {
      if (!respuesta.ok) {
        throw new Error("Respuesta " + respuesta.status);
      }
      return respuesta.json();
    })
    .then(function (lugares) {
      if (lugares.length === 0) {
        mostrarMensaje(MENSAJE_NO_ENCONTRADA, true);
        return;
      }
      ocultarMensaje();
      mostrarOpciones(cual, lugares);
    })
    .catch(function () {
      mostrarMensaje("No pudimos buscar la dirección. Marca el punto en el mapa.", true);
    });
}

function mostrarOpciones(cual, lugares) {
  const lista = listasResultados[cual];
  lista.replaceChildren(); // borra las opciones de una búsqueda anterior
  for (const lugar of lugares) {
    const opcion = document.createElement("button");
    opcion.type = "button";
    opcion.className = "boton boton-secundario";
    opcion.style.textAlign = "left";
    opcion.style.fontWeight = "400";
    // textContent y no innerHTML: el nombre viene de OpenStreetMap y no lo tratamos como HTML.
    opcion.textContent = nombreCorto(lugar.display_name);
    opcion.addEventListener("click", function () {
      lista.replaceChildren();
      // Nominatim entrega lat y lon como texto ("-33.50"), por eso los pasamos a número.
      fijarPunto(cual, Number(lugar.lat), Number(lugar.lon), opcion.textContent);
      DryRoute.mapa.setView([Number(lugar.lat), Number(lugar.lon)], 16);
    });
    lista.appendChild(opcion);
  }
}

for (const cual of ["origen", "destino"]) {
  camposTexto[cual].addEventListener("keydown", function (evento) {
    if (evento.key === "Enter") {
      evento.preventDefault(); // que Enter no recargue la página
      buscarDireccion(cual);
    }
  });
  // Si la persona escribe algo nuevo, el punto anterior ya no corresponde a lo que dice el campo.
  camposTexto[cual].addEventListener("input", function () {
    if (DryRoute[cual] !== null) {
      quitarPunto(cual);
    }
    listasResultados[cual].replaceChildren();
  });
}

// Por si el navegador intenta enviar el formulario igual: esta página no se recarga nunca.
formularioRuta.addEventListener("submit", function (evento) {
  evento.preventDefault();
});

// ---------- Calcular ruta ----------
function actualizarBotonCalcular() {
  botonCalcular.disabled = DryRoute.origen === null || DryRoute.destino === null;
}

// {lat: -33.5, lon: -70.65} -> "-33.500000,-70.650000", el formato lat,lon que pide /api/ruta/.
// Seis decimales son unos 10 cm: más precisión no sirve de nada.
function coordenadaComoTexto(punto) {
  return punto.lat.toFixed(6) + "," + punto.lon.toFixed(6);
}

botonCalcular.addEventListener("click", function () {
  const url = "/api/ruta/?origen=" + coordenadaComoTexto(DryRoute.origen) +
              "&destino=" + coordenadaComoTexto(DryRoute.destino);
  ocultarMensaje();
  botonCalcular.disabled = true; // evita mandar el mismo pedido dos veces mientras esperamos
  botonCalcular.textContent = "Calculando…";

  fetch(url)
    .then(function (respuesta) {
      // La ruta (200) y el error de entrada (400) traen JSON. Cualquier otra respuesta es una falla del servidor.
      if (respuesta.ok || respuesta.status === 400) {
        return respuesta.json().then(function (datos) {
          if (respuesta.ok) {
            DryRoute.mostrarResultado(datos);
          } else {
            DryRoute.mostrarError(datos.mensaje);
          }
        });
      }
      DryRoute.mostrarError("El servidor tuvo un problema. Intenta de nuevo en un momento.");
    })
    .catch(function () {
      DryRoute.mostrarError("No pudimos conectar con el servidor. Revisa tu conexión e intenta de nuevo.");
    })
    .finally(function () {
      botonCalcular.textContent = "Calcular ruta";
      actualizarBotonCalcular();
    });
});
