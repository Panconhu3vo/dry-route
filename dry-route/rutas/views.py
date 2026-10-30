from django.http import JsonResponse
from django.shortcuts import render

from .models import PuntoAnegado, PuntoEvacuacion
from .ruteo import ZONA, calcular_ruta, esta_en_zona


def mapa(request):
    return render(request, "rutas/mapa.html")


def api_puntos(request):
    """GET /api/puntos/: los puntos que el mapa dibuja al abrirse (docs/API.md)."""
    return JsonResponse({
        "zona": ZONA,
        "anegados": list(PuntoAnegado.objects.values("id", "nombre", "tipo", "activo", "lat", "lon")),
        "evacuacion": list(PuntoEvacuacion.objects.values("id", "nombre", "tipo", "lat", "lon")),
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

    resultado = calcular_ruta(origen, destino,
                              anegados_activos=list(PuntoAnegado.objects.filter(activo=True)),
                              puntos_evacuacion=list(PuntoEvacuacion.objects.all()))
    return JsonResponse(resultado)
