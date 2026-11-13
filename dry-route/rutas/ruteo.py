"""
Cálculo de la ruta segura (funcionalidad corazón). Reglas en docs/DECISIONES.md (D5).

Idea: el mapa de calles es un grafo (esquinas unidas por tramos). Quitamos las esquinas que quedan
a menos de 100 m de un punto anegado activo y buscamos el camino más corto en lo que queda (Dijkstra).
"""

import json
import math
from collections import defaultdict
from functools import cache, lru_cache
from types import SimpleNamespace

import networkx as nx
from django.conf import settings


def leer_zona():
    """La zona cubierta la escribe scripts/generar_datos.py junto con el grafo: así se cambia en un solo lugar."""
    with open(settings.BASE_DIR / "data" / "zona.json", encoding="utf-8") as archivo:
        return json.load(archivo)


ZONA = leer_zona()
RADIO_BLOQUEO_M = 100
# El mapa se divide en una cuadrícula de celdas de ~500 m para no medir contra todas las esquinas (T28)
TAMANO_CELDA = 0.005  # grados
# ~130 m expresados en grados de latitud o longitud aquí: cubre el radio de bloqueo con holgura
MARGEN_GRADOS = 0.0012
# Para buscar el punto de evacuación no se recorre toda la ciudad: solo los puntos a menos de 5 km en
# línea recta, y la búsqueda por calles se detiene a los 10 km. En Santiago siempre hay alguno mucho más cerca.
RADIO_EVACUACION_M = 5_000
CORTE_EVACUACION_M = 10_000
VELOCIDAD_KMH = 15  # velocidad urbana en contingencia (coincide con el prototipo del E2)
# Si estás dentro de una zona anegada, la ruta puede cruzar agua para salir, pero cada metro ahí "cuesta" 20 veces más
PENALIZACION_ZONA_ANEGADA = 20


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


def celda_de(lat, lon):
    return math.floor(lat / TAMANO_CELDA), math.floor(lon / TAMANO_CELDA)


@cache
def esquinas_por_celda():
    """{celda: [esquinas que caen en ella]}. Se arma una sola vez, la primera vez que se usa."""
    celdas = defaultdict(list)
    for nodo, datos in cargar_grafo().nodes(data=True):
        celdas[celda_de(datos["lat"], datos["lon"])].append(nodo)
    return celdas


def esquinas_alrededor(fila, columna, radio):
    """Esquinas del cuadrado de celdas de lado 2*radio+1 centrado en (fila, columna)."""
    celdas = esquinas_por_celda()
    return [nodo for f in range(fila - radio, fila + radio + 1) for c in range(columna - radio, columna + radio + 1)
            for nodo in celdas.get((f, c), [])]


# Con límite: las coordenadas vienen del usuario, y sin tope cada consulta distinta quedaría en memoria
# para siempre. 10.000 alcanza para todos los puntos de evacuación de Santiago más las consultas.
@lru_cache(maxsize=10_000)
def nodo_mas_cercano(lat, lon):
    """La esquina del grafo más cercana a (lat, lon). Mira primero la celda del punto y va ampliando
    el cuadrado de celdas hasta encontrar esquinas. Después mira un anillo más, porque la más cercana
    puede estar justo al otro lado del borde de una celda."""
    grafo = cargar_grafo()
    fila, columna = celda_de(lat, lon)
    radio = 0
    while radio < 200 and not esquinas_alrededor(fila, columna, radio):  # 200 celdas = más que toda la zona
        radio += 1
    candidatas = esquinas_alrededor(fila, columna, radio + 1)
    return min(candidatas, key=lambda n: distancia_m(lat, lon, grafo.nodes[n]["lat"], grafo.nodes[n]["lon"]))


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
    return tramos_cerca_de_coordenadas(punto.lat, punto.lon)


# Las calles no se mueven: para un mismo lugar el resultado es siempre el mismo, así que se guarda
@lru_cache(maxsize=10_000)
def tramos_cerca_de_coordenadas(lat, lon):
    grafo = cargar_grafo()
    lugar = SimpleNamespace(lat=lat, lon=lon)  # distancia_a_tramo_m espera algo con .lat y .lon
    cercanos = set()
    for u, v in grafo.edges:
        a, b = grafo.nodes[u], grafo.nodes[v]
        # Filtro rápido: si el punto queda fuera del rectángulo que encierra al tramo (más un margen),
        # el tramo no puede pasar a menos de 100 m y no vale la pena hacer la cuenta completa.
        if not (min(a["lat"], b["lat"]) - MARGEN_GRADOS <= lat <= max(a["lat"], b["lat"]) + MARGEN_GRADOS
                and min(a["lon"], b["lon"]) - MARGEN_GRADOS <= lon <= max(a["lon"], b["lon"]) + MARGEN_GRADOS):
            continue
        if distancia_a_tramo_m(lugar, a, b) < RADIO_BLOQUEO_M:
            cercanos.add(frozenset((u, v)))
    return frozenset(cercanos)


def tramos_de(camino):
    return {frozenset(par) for par in zip(camino, camino[1:])}


def vecinos_de(tramos):
    """{esquina: {esquinas vecinas}} a partir de un conjunto de tramos.
    Dijkstra pregunta por miles de tramos: buscar así es más rápido que armar un frozenset en cada pregunta."""
    vecinos = defaultdict(set)
    for tramo in tramos:
        extremos = tuple(tramo)
        u, v = extremos[0], extremos[-1]
        vecinos[u].add(v)
        vecinos[v].add(u)
    return vecinos


def esta_en_zona(lat, lon):
    return ZONA["sur"] <= lat <= ZONA["norte"] and ZONA["oeste"] <= lon <= ZONA["este"]


def cerca_de_anegado(lat, lon, anegados_activos):
    return any(distancia_m(lat, lon, p.lat, p.lon) < RADIO_BLOQUEO_M for p in anegados_activos)


def calcular_ruta(origen, destino, anegados_activos, puntos_evacuacion):
    """origen y destino son (lat, lon). Devuelve un dict con la forma de GET /api/ruta/ (docs/API.md)."""
    grafo = cargar_grafo()
    nodo_origen = nodo_mas_cercano(*origen)
    nodo_destino = nodo_mas_cercano(*destino)

    # 1. Bloquear los tramos de calle que pasan cerca de cada punto anegado.
    #    Los que salen del origen no se bloquean: si estás dentro de la zona anegada, igual tienes que poder salir.
    bloqueados_por_punto = {punto: tramos_cerca_de(punto) for punto in anegados_activos}
    bloqueados = {t for t in set().union(*bloqueados_por_punto.values()) if nodo_origen not in t}
    vecinos_bloqueados = vecinos_de(bloqueados)

    def largo_seguro(u, v, datos):
        # None le dice a NetworkX que el tramo no existe: así se "quitan" los tramos con agua
        return None if v in vecinos_bloqueados.get(u, ()) else datos["largo"]

    # Nunca se guía a un punto de evacuación que esté dentro de una zona anegada
    evacuacion_segura = [p for p in puntos_evacuacion if not cerca_de_anegado(p.lat, p.lon, anegados_activos)]

    # 2. Si el origen está en una zona anegada, salir es lo primero: se ignora el destino y se guía al
    #    punto de evacuación más cercano. Para salir se puede cruzar el agua, pero penalizada.
    if cerca_de_anegado(*origen, anegados_activos):
        vecinos_con_agua = vecinos_de(set().union(*bloqueados_por_punto.values()))

        def costo(u, v, datos):
            return datos["largo"] * (PENALIZACION_ZONA_ANEGADA if v in vecinos_con_agua.get(u, ()) else 1)

        return ir_a_evacuacion("en_peligro", "Estás en una zona anegada. Sal por esta ruta al punto de evacuación más cercano.",
                               grafo, nodo_origen, evacuacion_segura, costo)

    # 3. Camino más corto (Dijkstra) en el grafo sin los tramos bloqueados.
    #    Si el destino mismo está en la zona anegada, no existe una ruta segura hasta él.
    if not cerca_de_anegado(*destino, anegados_activos):
        try:
            # Bidireccional: busca desde el origen y desde el destino a la vez y se juntan al medio.
            # Da el mismo largo que el Dijkstra normal, pero recorre cerca de la mitad de las calles.
            _, camino = nx.bidirectional_dijkstra(grafo, nodo_origen, nodo_destino, weight=largo_seguro)
            evitados = []
            if bloqueados_por_punto:  # sin puntos anegados no hay nada que evitar ni que comparar
                _, camino_normal = nx.bidirectional_dijkstra(grafo, nodo_origen, nodo_destino, weight="largo")
                evitados = [p for p, tramos in bloqueados_por_punto.items() if tramos & tramos_de(camino_normal)]
            return armar_respuesta("segura", "Ruta segura encontrada.", grafo, camino, evitados, None)
        except nx.NetworkXNoPath:
            pass  # los bloqueos dejaron al destino aislado: seguimos con el punto de evacuación

    # 4. Sin ruta segura al destino: el punto de evacuación más cercano, solo por tramos sin agua.
    return ir_a_evacuacion("sin_ruta", "No hay una ruta segura a tu destino. Te guiamos al punto de evacuación más cercano.",
                           grafo, nodo_origen, evacuacion_segura, largo_seguro)


def ir_a_evacuacion(estado, mensaje, grafo, nodo_origen, puntos_evacuacion, peso):
    """Ruta al punto de evacuación alcanzable más cercano, medido por calles (no en línea recta)."""
    origen = grafo.nodes[nodo_origen]
    cercanos = [p for p in puntos_evacuacion
                if distancia_m(origen["lat"], origen["lon"], p.lat, p.lon) < RADIO_EVACUACION_M]
    # cutoff: la búsqueda por calles se detiene a los 10 km en vez de recorrer toda la ciudad
    distancias, caminos = nx.single_source_dijkstra(grafo, nodo_origen, cutoff=CORTE_EVACUACION_M, weight=peso)
    alcanzables = [p for p in cercanos if nodo_mas_cercano(p.lat, p.lon) in distancias]
    if not alcanzables:
        return armar_respuesta(estado, "No hay un punto de evacuación alcanzable. Busca un lugar alto y llama al 133.",
                               grafo, [], [], None)
    elegido = min(alcanzables, key=lambda p: distancias[nodo_mas_cercano(p.lat, p.lon)])
    return armar_respuesta(estado, mensaje, grafo, caminos[nodo_mas_cercano(elegido.lat, elegido.lon)], [], elegido)


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
