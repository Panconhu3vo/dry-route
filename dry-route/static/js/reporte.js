// reporte.js — Cristóbal (T13)
// Formulario "Reportar un problema": la persona marca en el mapa dónde hay un problema (calle anegada,
// árbol caído...), elige el tipo y lo envía a POST /api/reportes/ (ver docs/API.md).
// Define DryRoute.modoReporte, que entrada.js respeta para no mover el origen ni el destino.
// Usa DryRoute.mapa y DryRoute.recargarPuntos (mapa.js), y estaEnZona (entrada.js).
// Por eso se carga al final.
//
// Los nombres de este archivo llevan la palabra "Reporte" para no repetir ninguno de los otros
// archivos JS: si un nombre se repite, el navegador descarta este archivo completo.

window.DryRoute = window.DryRoute || {};

// true mientras el formulario está abierto: el clic en el mapa marca el lugar del problema.
DryRoute.modoReporte = false;

const panelReporte = document.getElementById("panel");
const botonReportar = document.getElementById("btn-reportar");
const formularioReporte = document.getElementById("form-reporte");
const selectTipoReporte = document.getElementById("select-tipo-reporte");
const inputDescripcionReporte = document.getElementById("input-descripcion-reporte");
const botonEnviarReporte = document.getElementById("btn-enviar-reporte");
const botonCancelarReporte = document.getElementById("btn-cancelar-reporte");
const mensajeReporte = document.getElementById("reporte-mensaje");

// Guardamos el texto que puso Gonzalo en el botón ("Cancelar") para devolverlo al abrir otra vez.
const TEXTO_CANCELAR_REPORTE = botonCancelarReporte.textContent;

// Un círculo ámbar con "!": forma, color y símbolo distintos del origen y del destino (docs/DISENO.md).
const ICONO_LUGAR_REPORTE = L.divIcon({
  className: "icono-lugar-reporte",
  html: "!",
  iconSize: [30, 30]
});

let lugarReporte = null;     // {lat, lon} del problema, o null si todavía no se marca
let marcadorReporte = null;

// El servidor acepta hasta 200 caracteres (docs/API.md). Así el navegador no deja escribir más.
inputDescripcionReporte.maxLength = 200;

// ---------- Mensajes ----------
// tipo es "info", "exito" o "error". reporte.css le da el color según data-tipo;
// el ícono va en el texto para no depender solo del color.
function mostrarMensajeReporte(texto, tipo) {
  const iconos = { info: "", exito: "✓ ", error: "⚠ " };
  mensajeReporte.textContent = iconos[tipo] + texto;
  mensajeReporte.dataset.tipo = tipo;
}

// ---------- Abrir y cerrar ----------
// En vez de esconder form-ruta y resultado uno por uno, le ponemos la clase "reportando" al panel y
// reporte.css los esconde. Así, si resultado.js los cambia mientras el formulario está abierto
// (por ejemplo, al recalcular la ruta), al cerrar aparecen tal como quedaron, sin que los pisemos.
function abrirFormularioReporte() {
  panelReporte.classList.add("reportando");
  formularioReporte.hidden = false;
  DryRoute.modoReporte = true;
  botonCancelarReporte.textContent = TEXTO_CANCELAR_REPORTE;
  mostrarMensajeReporte("Toca el mapa en el lugar del problema.", "info");
}

function cerrarFormularioReporte() {
  formularioReporte.hidden = true;
  panelReporte.classList.remove("reportando");
  DryRoute.modoReporte = false;
  quitarLugarReporte();
  selectTipoReporte.selectedIndex = 0;
  inputDescripcionReporte.value = "";
  mensajeReporte.textContent = "";
  delete mensajeReporte.dataset.tipo;
}

// ---------- Lugar del problema ----------
function quitarLugarReporte() {
  lugarReporte = null;
  if (marcadorReporte) {
    marcadorReporte.remove();
    marcadorReporte = null;
  }
  botonEnviarReporte.disabled = true;
}

// entrada.js también escucha el clic en el mapa, pero no hace nada mientras DryRoute.modoReporte es true.
DryRoute.mapa.on("click", function (evento) {
  if (!DryRoute.modoReporte) {
    return;
  }
  const lat = evento.latlng.lat;
  const lon = evento.latlng.lng;
  if (!estaEnZona(lat, lon)) {
    mostrarMensajeReporte("Ese lugar está fuera de la zona cubierta. Marca un punto dentro del área.", "error");
    return;
  }
  lugarReporte = { lat: lat, lon: lon };
  // Otro clic mueve el marcador: así se corrige sin tener que arrastrar con el dedo.
  if (marcadorReporte) {
    marcadorReporte.setLatLng([lat, lon]);
  } else {
    marcadorReporte = L.marker([lat, lon], { icon: ICONO_LUGAR_REPORTE, title: "Lugar del problema", zIndexOffset: 600 })
      .addTo(DryRoute.mapa);
  }
  botonEnviarReporte.disabled = false;
  mostrarMensajeReporte("Lugar marcado. Elige el tipo de problema y presiona Enviar.", "info");
});

// ---------- Enviar ----------
// Django rechaza cualquier POST que no traiga la "llave" CSRF, para que otra página no pueda enviar
// reportes a nombre de la persona. La vista / la deja en la cookie csrftoken y aquí la leemos.
// document.cookie es un solo texto, por ejemplo "csrftoken=abc123; otra=xyz".
function leerCookieReporte(nombre) {
  for (const parte of document.cookie.split(";")) {
    const limpia = parte.trim();
    if (limpia.startsWith(nombre + "=")) {
      return decodeURIComponent(limpia.slice(nombre.length + 1));
    }
  }
  return "";
}

botonEnviarReporte.addEventListener("click", function () {
  if (lugarReporte === null) {
    return;
  }
  botonEnviarReporte.disabled = true; // evita mandar el mismo reporte dos veces mientras esperamos
  mostrarMensajeReporte("Enviando…", "info");

  fetch("/api/reportes/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": leerCookieReporte("csrftoken")
    },
    body: JSON.stringify({
      tipo: selectTipoReporte.value,
      descripcion: inputDescripcionReporte.value.trim(),
      lat: lugarReporte.lat,
      lon: lugarReporte.lon
    })
  })
    .then(function (respuesta) {
      // Recibido (201) y error de entrada (400) traen un mensaje en JSON para la persona.
      if (respuesta.status === 201 || respuesta.status === 400) {
        return respuesta.json().then(function (datos) {
          if (respuesta.status === 201) {
            mostrarMensajeReporte(datos.mensaje, "exito");
            quitarLugarReporte(); // para otro reporte hay que marcar un lugar nuevo
            botonCancelarReporte.textContent = "Cerrar";
            // mapa.js vuelve a pedir los puntos: el reporte aparece en el mapa y, si se confirmó,
            // resultado.js recalcula la ruta. Preguntamos si existe por si mapa.js aún no la tiene (T14).
            if (DryRoute.recargarPuntos) {
              DryRoute.recargarPuntos();
            }
          } else {
            mostrarMensajeReporte(datos.mensaje, "error");
            botonEnviarReporte.disabled = false; // puede corregir el lugar o el tipo e intentar de nuevo
          }
        });
      }
      // Otra respuesta: por ejemplo 403 si falta la cookie csrftoken, o 500 si falla el servidor.
      mostrarMensajeReporte("No pudimos enviar el reporte. Recarga la página e intenta de nuevo.", "error");
      botonEnviarReporte.disabled = false;
    })
    .catch(function () {
      mostrarMensajeReporte("No pudimos conectar con el servidor. Revisa tu conexión e intenta de nuevo.", "error");
      botonEnviarReporte.disabled = lugarReporte === null;
    });
});

// ---------- Botones ----------
botonReportar.addEventListener("click", abrirFormularioReporte);
botonCancelarReporte.addEventListener("click", cerrarFormularioReporte);

// Con un solo campo de texto, Enter envía el formulario y recarga la página. Lo evitamos:
// el reporte se manda solo con el botón Enviar, después de marcar el lugar.
formularioReporte.addEventListener("submit", function (evento) {
  evento.preventDefault();
});
