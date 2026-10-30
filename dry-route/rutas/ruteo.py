"""
Cálculo de la ruta segura (funcionalidad corazón). Reglas en docs/DECISIONES.md (D5).

Idea: el mapa de calles es un grafo (esquinas unidas por tramos). Quitamos las esquinas que quedan
a menos de 100 m de un punto anegado activo y buscamos el camino más corto en lo que queda (Dijkstra).
"""

import json
import math
from functools import cache

import networkx as nx
from django.conf import settings

ZONA = {"norte": -33.490, "sur": -33.545, "oeste": -70.680, "este": -70.635}  # igual que scripts/generar_datos.py
RADIO_BLOQUEO_M = 100
VELOCIDAD_KMH = 15  # velocidad urbana en contingencia (coincide con el prototipo del E2)


@cache
def cargar_grafo():
    """Lee grafo.json una sola vez (la primera consulta) y lo deja en memoria para las siguientes."""
    with open(settings.BASE_DIR / "data" / "grafo.json", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    grafo = nx.Graph()  # no dirigido: la ruta es referencial y no considera sentido de tránsito (D2)
    for nodo, (lat, lon) in datos["nodos"].items():
        grafo.add_node(nodo, lat=lat, lon=lon)
    for u, v, largo, nombre in datos["aristas"]:
        grafo.add_edge(u, v, largo=largo, nombre=nombre)
    return grafo


def distancia_m(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos coordenadas (fórmula de haversine)."""
    radio_tierra = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radio_tierra * math.asin(math.sqrt(a))


@cache
def nodo_mas_cercano(lat, lon):
    grafo = cargar_grafo()
    return min(grafo.nodes, key=lambda n: distancia_m(lat, lon, grafo.nodes[n]["lat"], grafo.nodes[n]["lon"]))


def distancia_a_tramo_m(punto, esquina_a, esquina_b):
    """Distancia en metros desde un punto al tramo recto entre dos esquinas.
    Hace falta porque un paso bajo nivel es un tramo largo: sus esquinas pueden quedar
    a más de 100 m del punto anegado aunque el tramo pase justo por encima."""
    # A esta escala (pocos km) se puede tratar el mapa como un plano, con metros como unidad
    metros_por_grado_lon = 111_320 * math.cos(math.radians(punto.lat))
    ax, ay = (esquina_a["lon"] - punto.lon) * metros_por_grado_lon, (esquina_a["lat"] - punto.lat) * 110_540
    bx, by = (esquina_b["lon"] - punto.lon) * metros_por_grado_lon, (esquina_b["lat"] - punto.lat) * 110_540
    dx, dy = bx - ax, by - ay
    largo2 = dx * dx + dy * dy
    # t indica el punto del tramo más cercano al punto anegado (0 = esquina A, 1 = esquina B)
    t = 0 if largo2 == 0 else max(0, min(1, -(ax * dx + ay * dy) / largo2))
    return math.hypot(ax + t * dx, ay + t * dy)


def tramos_cerca_de(punto):
    """Tramos de calle (pares de esquinas) que pasan a menos de RADIO_BLOQUEO_M del punto anegado."""
    grafo = cargar_grafo()
    return {frozenset((u, v)) for u, v in grafo.edges
            if distancia_a_tramo_m(punto, grafo.nodes[u], grafo.nodes[v]) < RADIO_BLOQUEO_M}


def tramos_de(camino):
    return {frozenset(par) for par in zip(camino, camino[1:])}


def esta_en_zona(lat, lon):
    return ZONA["sur"] <= lat <= ZONA["norte"] and ZONA["oeste"] <= lon <= ZONA["este"]


def calcular_ruta(origen, destino, anegados_activos, puntos_evacuacion):
    """origen y destino son (lat, lon). Devuelve un dict con la forma de GET /api/ruta/ (docs/API.md)."""
    grafo = cargar_grafo()
    nodo_origen = nodo_mas_cercano(*origen)
    nodo_destino = nodo_mas_cercano(*destino)

    # 1. Bloquear los tramos de calle que pasan cerca de cada punto anegado.
    #    Los que salen del origen no se bloquean: si estás dentro de la zona anegada, igual tienes que poder salir.
    bloqueados_por_punto = {punto: tramos_cerca_de(punto) for punto in anegados_activos}
    bloqueados = {t for t in set().union(*bloqueados_por_punto.values()) if nodo_origen not in t}
    grafo_seguro = nx.subgraph_view(grafo, filter_edge=lambda u, v: frozenset((u, v)) not in bloqueados)

    # Si el destino mismo está en la zona anegada, no existe una ruta segura hasta él
    destino_anegado = any(
        distancia_m(destino[0], destino[1], p.lat, p.lon) < RADIO_BLOQUEO_M for p in anegados_activos
    )

    # 2. Camino más corto (Dijkstra) en el grafo sin los tramos bloqueados.
    if not destino_anegado:
        try:
            camino = nx.shortest_path(grafo_seguro, nodo_origen, nodo_destino, weight="largo")
            camino_normal = nx.shortest_path(grafo, nodo_origen, nodo_destino, weight="largo")
            evitados = [p for p, tramos in bloqueados_por_punto.items() if tramos & tramos_de(camino_normal)]
            return armar_respuesta("segura", "Ruta segura encontrada.", grafo_seguro, camino, evitados, None)
        except nx.NetworkXNoPath:
            pass  # los bloqueos dejaron al destino aislado: seguimos con el punto de evacuación

    # 3. Sin ruta segura: el punto de evacuación alcanzable más cercano (por calles, no en línea recta).
    distancias, caminos = nx.single_source_dijkstra(grafo_seguro, nodo_origen, weight="largo")
    alcanzables = [p for p in puntos_evacuacion if nodo_mas_cercano(p.lat, p.lon) in distancias]
    if not alcanzables:
        return armar_respuesta("sin_ruta", "No hay una ruta segura ni un punto de evacuación alcanzable. "
                               "Busca un lugar alto y llama al 133.", grafo_seguro, [], [], None)
    elegido = min(alcanzables, key=lambda p: distancias[nodo_mas_cercano(p.lat, p.lon)])
    return armar_respuesta("sin_ruta", "No hay una ruta segura a tu destino. Te guiamos al punto de evacuación más cercano.",
                           grafo_seguro, caminos[nodo_mas_cercano(elegido.lat, elegido.lon)], [], elegido)


def armar_respuesta(estado, mensaje, grafo, camino, evitados, punto_evacuacion):
    distancia = nx.path_weight(grafo, camino, weight="largo") if len(camino) > 1 else 0
    return {
        "estado": estado,
        "mensaje": mensaje,
        "ruta": [[grafo.nodes[n]["lat"], grafo.nodes[n]["lon"]] for n in camino],
        "distancia_m": round(distancia),
        "tiempo_min": math.ceil(distancia / 1000 / VELOCIDAD_KMH * 60),
        "puntos_evitados": [{"id": p.id, "nombre": p.nombre, "lat": p.lat, "lon": p.lon} for p in evitados],
        "punto_evacuacion": None if punto_evacuacion is None else {
            "id": punto_evacuacion.id, "nombre": punto_evacuacion.nombre, "tipo": punto_evacuacion.tipo,
            "lat": punto_evacuacion.lat, "lon": punto_evacuacion.lon,
        },
    }
