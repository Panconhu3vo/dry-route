"""
Reporte colaborativo (segunda funcionalidad). Reglas en docs/DECISIONES.md (D11).

Idea: un reporte solo queda "pendiente" y no cambia las rutas. Cuando otra persona (otra sesión del
navegador) reporta a menos de 100 m, los dos se confirman y se activa un PuntoAnegado. Como ruteo.py ya
evita todo PuntoAnegado activo, la ruta cambia sin tocar el algoritmo.
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from .models import PuntoAnegado, Reporte
from .ruteo import distancia_m

HORAS_VIGENCIA_REPORTE = 6
RADIO_REPORTE_M = 100
REPORTES_REQUERIDOS = 2
FUENTE_REPORTES = "Reportes ciudadanos"


def reportes_vigentes():
    """Reportes de las últimas 6 horas que no fueron descartados en el admin."""
    limite = timezone.now() - timedelta(hours=HORAS_VIGENCIA_REPORTE)
    return Reporte.objects.filter(fecha_hora__gte=limite).exclude(estado_verificacion="descartado")


def cerca_de(elementos, lat, lon):
    """Los reportes o puntos que están a menos de 100 m de (lat, lon)."""
    return [e for e in elementos if distancia_m(lat, lon, e.lat, e.lon) < RADIO_REPORTE_M]


def ya_reporto(sesion, lat, lon):
    """True si esta misma persona ya reportó cerca de aquí: no puede confirmar su propio reporte."""
    return any(r.sesion == sesion for r in cerca_de(reportes_vigentes(), lat, lon))


def punto_para(reporte, otros):
    """Elige qué PuntoAnegado se activa al confirmar un lugar."""
    # 1. Si el lugar ya estaba confirmado por reportes anteriores, se suma a ese mismo punto
    for otro in otros:
        if otro.punto is not None:
            return otro.punto
    # 2. Si hay un paso bajo nivel (u otro punto) cerca, se activa ese y no se crea uno repetido
    cercanos = cerca_de(PuntoAnegado.objects.all(), reporte.lat, reporte.lon)
    if cercanos:
        return min(cercanos, key=lambda p: distancia_m(reporte.lat, reporte.lon, p.lat, p.lon))
    # 3. Si no hay nada, se crea un punto nuevo en el lugar reportado
    return PuntoAnegado.objects.create(
        osm_id=f"reporte/{reporte.id}",
        nombre=f"Reporte ciudadano: {reporte.get_tipo_display().lower()}",
        tipo=reporte.tipo,
        lat=reporte.lat,
        lon=reporte.lon,
        fuente=FUENTE_REPORTES,
    )


@transaction.atomic  # todo o nada: no queda un reporte confirmado con el punto a medio activar
def registrar_reporte(tipo, descripcion, lat, lon, sesion):
    """Guarda el reporte y, si otra persona reportó cerca, confirma el lugar.
    Devuelve el reporte guardado (con estado_verificacion y punto ya actualizados)."""
    otros = [r for r in cerca_de(reportes_vigentes(), lat, lon) if r.sesion != sesion]
    reporte = Reporte.objects.create(tipo=tipo, descripcion=descripcion, lat=lat, lon=lon, sesion=sesion)
    if len(otros) + 1 < REPORTES_REQUERIDOS:
        return reporte  # queda pendiente: un solo reporte no bloquea rutas

    punto = punto_para(reporte, otros)
    punto.activo = True
    punto.save()
    for r in [reporte, *otros]:
        r.estado_verificacion = "confirmado"
        r.punto = punto
        r.save()
    return reporte


def confirmaciones_por_punto():
    """{id del punto: cantidad de reportes vigentes que lo confirman}. Los puntos sin reportes no aparecen."""
    filas = reportes_vigentes().filter(punto__isnull=False).values("punto").annotate(cantidad=Count("id"))
    return {fila["punto"]: fila["cantidad"] for fila in filas}


def reportes_pendientes():
    """Reportes vigentes que aún esperan a una segunda persona. Se dibujan en el mapa pero no bloquean rutas."""
    return [
        {
            "id": r.id,
            "tipo": r.tipo,
            "descripcion": r.descripcion,
            "lat": r.lat,
            "lon": r.lon,
            "fecha_hora": timezone.localtime(r.fecha_hora).isoformat(timespec="seconds"),
            # Siempre 1: si hubiera otro reporte de otra persona cerca, ya estaría confirmado
            "confirmaciones": 1,
            "requeridas": REPORTES_REQUERIDOS,
        }
        for r in reportes_vigentes().filter(estado_verificacion="pendiente")
    ]
