import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import PuntoAnegado, PuntoEvacuacion, Reporte
from .reportes import (REPORTES_REQUERIDOS, confirmaciones_por_punto, desactivar_puntos_vencidos, registrar_reporte,
                       reportes_pendientes, ya_reporto)
from .ruteo import ZONA, calcular_ruta, esta_en_zona


# Sin esta cookie, Django rechazaría el POST con el que el navegador envía un reporte
@ensure_csrf_cookie
def mapa(request):
    # La zona va en la página: así el mapa se encuadra al tiro, sin esperar a /api/puntos/
    return render(request, "rutas/mapa.html", {"zona": ZONA})


def api_puntos(request):
    """GET /api/puntos/: los puntos que el mapa dibuja al abrirse (docs/API.md)."""
    desactivar_puntos_vencidos()
    confirmaciones = confirmaciones_por_punto()
    anegados = list(PuntoAnegado.objects.values("id", "nombre", "tipo", "activo", "fuente", "lat", "lon"))
    for punto in anegados:
        punto["confirmaciones"] = confirmaciones.get(punto["id"], 0)
    return JsonResponse({
        "zona": ZONA,
        "anegados": anegados,
        "evacuacion": list(PuntoEvacuacion.objects.values("id", "nombre", "tipo", "lat", "lon")),
        "reportes_pendientes": reportes_pendientes(),
    })


def leer_coordenada(texto):
    """'-33.50,-70.65' -> (-33.5, -70.65). Devuelve None si el formato no es lat,lon."""
    try:
        lat, lon = (float(parte) for parte in texto.split(","))
        return lat, lon
    except (AttributeError, ValueError):
        return None


def api_ruta(request):
    """GET /api/ruta/?origen=lat,lon&destino=lat,lon: calcula la ruta segura (docs/API.md)."""
    origen = leer_coordenada(request.GET.get("origen"))
    destino = leer_coordenada(request.GET.get("destino"))
    if origen is None or destino is None:
        return JsonResponse({"error": "parametros_invalidos",
                             "mensaje": "Falta el origen o el destino. Márcalos en el mapa."}, status=400)
    if not esta_en_zona(*origen) or not esta_en_zona(*destino):
        return JsonResponse({"error": "fuera_de_zona",
                             "mensaje": "El origen o el destino está fuera de la zona cubierta. Marca un punto dentro del área."},
                            status=400)

    desactivar_puntos_vencidos()  # para no evitar un lugar cuyos reportes ya vencieron
    resultado = calcular_ruta(origen, destino,
                              anegados_activos=list(PuntoAnegado.objects.filter(activo=True)),
                              puntos_evacuacion=list(PuntoEvacuacion.objects.all()))
    return JsonResponse(resultado)


def error_400(error, mensaje):
    return JsonResponse({"error": error, "mensaje": mensaje}, status=400)


def sesion_de(request):
    """Clave de la sesión del navegador: sin login, es lo que distingue a una persona de otra (D11)."""
    if request.session.session_key is None:
        # Guardar un dato obliga a Django a crear la sesión y a mandarle su cookie al navegador.
        # Sin cookie, cada reporte llegaría con una sesión nueva y una persona podría confirmarse sola.
        request.session["reporta"] = True
        request.session.save()
    return request.session.session_key


@require_POST
def api_reportes(request):
    """POST /api/reportes/: recibe un reporte en JSON y aplica la regla de los 2 reportes (docs/API.md)."""
    try:
        datos = json.loads(request.body)
        tipo = str(datos["tipo"])
        lat, lon = float(datos["lat"]), float(datos["lon"])
        descripcion = str(datos.get("descripcion") or "").strip()
    except (ValueError, KeyError, TypeError):
        return error_400("parametros_invalidos", "Faltan datos del reporte. Marca el lugar y elige el tipo.")
    if len(descripcion) > 200:
        return error_400("parametros_invalidos", "La descripción puede tener como máximo 200 caracteres.")
    if tipo not in dict(Reporte.TIPOS):
        return error_400("tipo_invalido", "Elige un tipo de problema de la lista.")
    if not esta_en_zona(lat, lon):
        return error_400("fuera_de_zona", "El lugar está fuera de la zona cubierta. Marca un punto dentro del área.")

    sesion = sesion_de(request)
    if ya_reporto(sesion, lat, lon):
        return error_400("ya_reportado", "Ya reportaste este lugar. Falta que otra persona lo confirme.")

    reporte = registrar_reporte(tipo, descripcion, lat, lon, sesion)
    if reporte.punto is None:
        confirmaciones = 1
        mensaje = "Reporte recibido. Falta que otra persona confirme este lugar."
    else:
        confirmaciones = confirmaciones_por_punto()[reporte.punto.id]
        mensaje = "Reporte confirmado. Las rutas ya evitan este lugar."
    return JsonResponse({
        "id": reporte.id,
        "estado": reporte.estado_verificacion,
        "confirmaciones": confirmaciones,
        "requeridas": REPORTES_REQUERIDOS,
        "punto_id": reporte.punto.id if reporte.punto else None,
        "mensaje": mensaje,
    }, status=201)
