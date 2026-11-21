// alertas.js — Alertas de lluvia (F3, DECISIONES D14)
// Llena la franja de lluvia (#alerta-lluvia, junto a "N anegamientos activos") con GET /api/alertas/ y la
// vuelve a pedir cada minuto.
// Solo muestra el estado: los pasos bajo nivel que enciende la lluvia los dibuja mapa.js, y si cambian
// mientras hay una ruta en pantalla, resultado.js la recalcula sola (T15). Ver docs/API.md.

window.DryRoute = window.DryRoute || {};

const franjaLluvia = document.getElementById("alerta-lluvia");
const SEGUNDOS_ENTRE_ALERTAS = 60;

// La licencia de los datos de Open-Meteo (CC BY 4.0) pide nombrarlos: va junto a la de OpenStreetMap
DryRoute.mapa.attributionControl.addAttribution('Lluvia: <a href="https://open-meteo.com/">Open-Meteo</a>');

// "2026-11-20T20:45:00-03:00" -> "20:45". La hora ya viene en hora de Chile desde el servidor.
function horaCorta(fechaIso) {
  return fechaIso.slice(11, 16);
}

// Cambia el texto y el color de la franja. El nivel va también en el ícono y en el texto,
// porque el estado nunca se comunica solo con color (docs/DISENO.md).
function mostrarFranja(nivel, icono, texto) {
  franjaLluvia.className = "franja-lluvia franja-" + nivel;
  const simbolo = document.createElement("span");
  simbolo.className = "franja-icono";
  simbolo.setAttribute("aria-hidden", "true");  // el lector de pantalla ya lee el texto
  simbolo.textContent = icono;
  franjaLluvia.replaceChildren(simbolo, document.createTextNode(texto));
}

function mostrarAlertas(datos) {
  if (!datos.al_dia) {
    // El comando actualizar_alertas no ha corrido en los últimos 30 minutos (o nunca)
    const texto = datos.actualizado
      ? "Datos de lluvia no disponibles. Mostrando el último estado."
      : "Datos de lluvia no disponibles.";
    mostrarFranja("sin-datos", "?", texto);
    return;
  }
  const actualizado = " · actualizado " + horaCorta(datos.actualizado);
  if (datos.vigentes.length === 0) {
    mostrarFranja("normal", "✓", "Sin alertas de lluvia en la zona" + actualizado);
    return;
  }
  // La más reciente primero (el servidor las ordena). El título lo arma alertas.py: "Lluvia 7 mm/h · 3 pasos…"
  const alerta = datos.vigentes[0];
  const fuente = alerta.fuente === "Simulación" ? " · simulación" : "";
  mostrarFranja(alerta.nivel, alerta.nivel === "aviso" ? "☁" : "⚠", alerta.titulo + actualizado + fuente);
}

function pedirAlertas() {
  fetch("/api/alertas/")
    .then(function (respuesta) {
      if (!respuesta.ok) {
        throw new Error("Respuesta " + respuesta.status);
      }
      return respuesta.json();
    })
    .then(mostrarAlertas)
    .catch(function (error) {
      // Sin conexión con el servidor: el mapa queda con lo último que llegó
      console.warn("No se pudo cargar /api/alertas/.", error);
      mostrarFranja("sin-datos", "?", "Datos de lluvia no disponibles. Mostrando el último estado.");
    });
}

pedirAlertas();
// Cada minuto basta: Open-Meteo actualiza cada 15 minutos y el comando corre cada 10.
// Si la pestaña está escondida no se pregunta, igual que con los puntos (resultado.js).
setInterval(function () {
  if (!document.hidden) {
    pedirAlertas();
  }
}, SEGUNDOS_ENTRE_ALERTAS * 1000);
