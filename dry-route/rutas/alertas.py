"""
Alertas de lluvia (tercera funcionalidad). Reglas en docs/DECISIONES.md (D14).

Idea: cada cierto tiempo se pregunta a Open-Meteo cuánto llueve sobre la zona. Los pasos bajo nivel donde
llueve sobre el umbral se encienden solos (activo=True) y se apagan solos cuando la lluvia baja. Como
ruteo.py ya evita todo PuntoAnegado activo, las rutas cambian sin tocar el algoritmo, igual que con los reportes.
"""

import json
import logging
import math
from datetime import timedelta
from urllib.parse import urlencode
from urllib.request import urlopen

from django.db import transaction
from django.utils import timezone

from .models import Alerta, PuntoAnegado
from .reportes import reportes_vigentes
from .ruteo import ZONA, distancia_m

logger = logging.getLogger(__name__)

# Valor inicial, SIN CALIBRAR: 4 mm/h es lluvia moderada (la clasificación usual va de 2,5 a 7,6 mm/h).
# Hay que ajustarlo comparando con lo que de verdad pasa en los pasos bajo nivel. Se cambia con --umbral.
UMBRAL_MM_POR_HORA = 4
# Desde el doble del umbral (8 mm/h, lluvia fuerte) la alerta pasa a "alarma"
FACTOR_ALARMA = 2
# Los datos de lluvia valen 30 minutos: si el comando deja de correr, la alerta se cierra sola y la
# franja del mapa avisa que los datos no están al día. Conviene correr el comando cada 10 minutos.
MINUTOS_VIGENCIA_DATOS = 30
# La zona se divide en 4 x 4 celdas (~7 km de lado) y se pregunta por el centro de cada una. Los modelos
# globales que cubren Santiago tienen ~10 km de resolución: preguntar por cada paso bajo nivel (185)
# daría casi los mismos números y gastaría 185 consultas del límite gratuito en vez de 16.
CELDAS_POR_LADO = 4
# Con --simular y --cerca, llueve solo a menos de 2 km del lugar (alrededor de la USM caen 2 a 5 pasos)
RADIO_SIMULACION_M = 2000
SEGUNDOS_ESPERA = 10
URL_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
FUENTE_OPEN_METEO = "Open-Meteo"
FUENTE_SIMULACION = "Simulación"
# Solo se cierran solas las alertas que abrió este proceso: si alguien crea una a mano en el admin, se respeta
FUENTES_AUTOMATICAS = [FUENTE_OPEN_METEO, FUENTE_SIMULACION]


def puntos_con_riesgo_de_lluvia():
    """Los pasos bajo nivel: son los que se anegan con lluvia intensa. Los puntos que crearon los reportes
    (un árbol caído, por ejemplo) y las simulaciones de la demo no dependen de la lluvia."""
    return list(PuntoAnegado.objects.filter(tipo="paso_bajo_nivel"))


def celda_de(lat, lon):
    """(fila, columna) de la celda de la zona donde cae el punto, de 0 a CELDAS_POR_LADO - 1."""
    alto = (ZONA["norte"] - ZONA["sur"]) / CELDAS_POR_LADO
    ancho = (ZONA["este"] - ZONA["oeste"]) / CELDAS_POR_LADO
    fila = min(max(math.floor((lat - ZONA["sur"]) / alto), 0), CELDAS_POR_LADO - 1)
    columna = min(max(math.floor((lon - ZONA["oeste"]) / ancho), 0), CELDAS_POR_LADO - 1)
    return fila, columna


def centro_de(celda):
    fila, columna = celda
    alto = (ZONA["norte"] - ZONA["sur"]) / CELDAS_POR_LADO
    ancho = (ZONA["este"] - ZONA["oeste"]) / CELDAS_POR_LADO
    return round(ZONA["sur"] + (fila + 0.5) * alto, 4), round(ZONA["oeste"] + (columna + 0.5) * ancho, 4)


def pedir_a_open_meteo(coordenadas):
    """Una sola consulta HTTP con todas las coordenadas. Devuelve una lista con la respuesta de cada una,
    en el mismo orden. Es lo único que habría que cambiar para usar otra fuente (DMC, MeteoPrecisa)."""
    parametros = urlencode({
        "latitude": ",".join(str(lat) for lat, _ in coordenadas),
        "longitude": ",".join(str(lon) for _, lon in coordenadas),
        "current": "precipitation",   # lluvia caída en los últimos 15 minutos, en mm
        "hourly": "precipitation",    # lluvia de cada hora, en mm (= mm/h)
        "forecast_hours": 3,          # la hora actual y las dos siguientes
        "timezone": "America/Santiago",
    })
    with urlopen(f"{URL_OPEN_METEO}?{parametros}", timeout=SEGUNDOS_ESPERA) as respuesta:
        datos = json.load(respuesta)
    # Con una sola coordenada Open-Meteo devuelve un objeto y no una lista
    if isinstance(datos, dict):
        datos = [datos]
    # Las coordenadas que devuelve son las de su propia grilla, no las pedidas: por eso se ordena por
    # location_id (la posición en la consulta). La primera respuesta no lo trae: vale 0.
    return sorted(datos, key=lambda d: d.get("location_id", 0))


def consultar_lluvia(puntos):
    """{id del punto: {"ahora": mm/h, "pronostico": mm/h}} con la lluvia real, en una sola consulta.
    "pronostico" es la hora más lluviosa de las próximas 3. Devuelve None si Open-Meteo no responde."""
    celdas = sorted({celda_de(p.lat, p.lon) for p in puntos})
    if not celdas:
        return {}
    try:
        respuestas = pedir_a_open_meteo([centro_de(celda) for celda in celdas])
        lluvia_por_celda = {}
        for celda, datos in zip(celdas, respuestas, strict=True):
            lluvia_por_celda[celda] = {
                # Lo de los últimos 15 minutos, por 4, da la intensidad en mm por hora
                "ahora": round(datos["current"]["precipitation"] * 4, 1),
                "pronostico": round(max(datos["hourly"]["precipitation"]), 1),
            }
    # Sin internet, Open-Meteo caído (OSError) o una respuesta con otra forma: se avisa en la consola y no
    # se cambia nada. Es más seguro dejar el último estado conocido que apagar todos los puntos.
    except (OSError, ValueError, KeyError, TypeError) as error:
        logger.warning("No se pudo consultar la lluvia en Open-Meteo: %s", error)
        return None
    return {p.id: lluvia_por_celda[celda_de(p.lat, p.lon)] for p in puntos}


def simular_lluvia(puntos, mm_por_hora, cerca=None, radio_m=RADIO_SIMULACION_M):
    """Lo mismo que consultar_lluvia, pero inventado y sin internet: para la demo y las pruebas.
    Si viene cerca=(lat, lon), solo llueve a menos de radio_m de ese lugar; en el resto, 0."""
    lluvia = {}
    for punto in puntos:
        llueve_aqui = cerca is None or distancia_m(cerca[0], cerca[1], punto.lat, punto.lon) <= radio_m
        mm = mm_por_hora if llueve_aqui else 0
        lluvia[punto.id] = {"ahora": mm, "pronostico": mm}
    return lluvia


def texto_pasos(cantidad):
    return "1 paso bajo nivel" if cantidad == 1 else f"{cantidad} pasos bajo nivel"


@transaction.atomic  # todo o nada: no quedan puntos actualizados a medias
def actualizar_puntos(umbral_mm=UMBRAL_MM_POR_HORA, simular_mm=None, cerca=None, radio_m=RADIO_SIMULACION_M):
    """Enciende los pasos bajo nivel donde llueve sobre el umbral y apaga los que encendió la lluvia y ya
    bajaron. Abre, actualiza o cierra la alerta. Devuelve un resumen, o None si no hubo datos de lluvia."""
    puntos = puntos_con_riesgo_de_lluvia()
    if simular_mm is None:
        lluvia = consultar_lluvia(puntos)
        fuente = FUENTE_OPEN_METEO
        if lluvia is None:
            return None  # Open-Meteo falló: queda el último estado
    else:
        lluvia = simular_lluvia(puntos, simular_mm, cerca, radio_m)
        fuente = FUENTE_SIMULACION

    ahora = timezone.now()
    # Si dos vecinos confirmaron el lugar, la lluvia no lo apaga aunque haya parado: el agua puede seguir ahí
    confirmados_por_vecinos = set(reportes_vigentes().filter(punto__isnull=False).values_list("punto", flat=True))
    encendidos = apagados = 0
    for punto in puntos:
        mm = lluvia[punto.id]["ahora"]
        punto.lluvia_mm = mm
        punto.actualizado = ahora
        if mm >= umbral_mm and not punto.activo:
            # Solo se marca si estaba apagado: un punto encendido a mano o por reportes sigue siendo de ellos
            punto.activo = True
            punto.activado_por_lluvia = True
            encendidos += 1
        elif mm < umbral_mm and punto.activado_por_lluvia and punto.id not in confirmados_por_vecinos:
            punto.activo = False
            punto.activado_por_lluvia = False
            apagados += 1
    PuntoAnegado.objects.bulk_update(puntos, ["lluvia_mm", "actualizado", "activo", "activado_por_lluvia"])

    lluvia_ahora = max((d["ahora"] for d in lluvia.values()), default=0)
    lluvia_pronostico = max((d["pronostico"] for d in lluvia.values()), default=0)
    con_riesgo = sum(1 for d in lluvia.values() if d["ahora"] >= umbral_mm)
    alerta = actualizar_alerta(umbral_mm, lluvia_ahora, lluvia_pronostico, con_riesgo, fuente, ahora)
    return {"encendidos": encendidos, "apagados": apagados, "lluvia_max_mm": lluvia_ahora,
            "pronostico_max_mm": lluvia_pronostico, "con_riesgo": con_riesgo, "alerta": alerta}


def actualizar_alerta(umbral_mm, lluvia_ahora, lluvia_pronostico, con_riesgo, fuente, ahora):
    """Deja abierta a lo más una alerta automática, con el nivel que corresponde a la lluvia de ahora."""
    if lluvia_ahora >= umbral_mm * FACTOR_ALARMA:
        nivel = "alarma"
    elif lluvia_ahora >= umbral_mm:
        nivel = "alerta"
    elif lluvia_pronostico >= umbral_mm:
        nivel = "aviso"  # todavía no llueve fuerte, pero se espera: no se corta ninguna ruta
    else:
        nivel = None

    if nivel == "aviso":
        titulo = f"Se espera lluvia de {round(lluvia_pronostico)} mm/h en las próximas horas"
        descripcion = "Todavía no se cortan rutas. Revisa el mapa antes de salir."
    else:
        titulo = f"Lluvia {round(lluvia_ahora)} mm/h · {texto_pasos(con_riesgo)} con riesgo"
        descripcion = f"Las rutas evitan los pasos bajo nivel donde llueve {umbral_mm} mm/h o más."

    abiertas = Alerta.objects.filter(activa=True, fuente__in=FUENTES_AUTOMATICAS)
    if nivel is None:
        abiertas.update(activa=False, vigente_hasta=ahora)  # paró la lluvia: se cierra la alerta
        return None
    # Si cambió el nivel se cierra la alerta anterior y se abre otra: así el admin guarda la historia
    abiertas.exclude(nivel=nivel).update(activa=False, vigente_hasta=ahora)
    alerta = abiertas.filter(nivel=nivel).first() or Alerta(nivel=nivel)
    alerta.titulo = titulo
    alerta.descripcion = descripcion
    alerta.fuente = fuente
    alerta.vigente_hasta = ahora + timedelta(minutes=MINUTOS_VIGENCIA_DATOS)
    alerta.save()
    return alerta


def alertas_vigentes():
    return Alerta.objects.filter(activa=True, vigente_hasta__gte=timezone.now())
