"""
Genera los datos de Dry Routes desde OpenStreetMap (tarea T1).

Escribe cuatro archivos en dry-route/data/:
  - zona.json              límites de la zona cubierta (la app los lee de aquí)
  - grafo.json             calles de la zona (nodos = esquinas, aristas = tramos de calle)
  - puntos_anegados.json   pasos bajo nivel: los puntos que se pueden anegar
  - puntos_evacuacion.json hospitales, bomberos, Carabineros, colegios y puntos de encuentro

Se corre UNA vez por zona (necesita internet). La app después solo lee los JSON.
Uso, desde la raíz del repo:
    pip install -r requirements-datos.txt
    python scripts/generar_datos.py sur        (o: demo, santiago)
"""

import json
import sys
from pathlib import Path

import networkx as nx
import osmnx as ox

# Zonas que se pueden generar (DECISIONES D3). La de la entrega se elige al correr el script.
ZONAS = {
    "demo": {"norte": -33.490, "sur": -33.545, "oeste": -70.680, "este": -70.635},      # eje Gran Avenida (E3)
    "sur": {"norte": -33.470, "sur": -33.590, "oeste": -70.720, "este": -70.600},       # comunas del sector sur
    "santiago": {"norte": -33.360, "sur": -33.630, "oeste": -70.800, "este": -70.500},  # Gran Santiago
}

CARPETA_DATOS = Path(__file__).resolve().parent.parent / "dry-route" / "data"

# Tipos de OSM -> tipos de punto de evacuación de docs/API.md
TIPOS_EVACUACION = {
    "hospital": "hospital",
    "clinic": "clinica",
    "fire_station": "bomberos",
    "police": "carabineros",
    "school": "colegio",
    "assembly_point": "punto_encuentro",
}


def primero(valor):
    """OSM a veces junta varios valores en una lista (al unir tramos) y el orden cambia entre descargas.
    Usamos el menor para que cada corrida dé el mismo nombre y el mismo osm_id (cargar_datos depende de eso)."""
    return min(valor) if isinstance(valor, list) else valor


def es_paso_bajo_nivel(datos_tramo):
    """Un tramo es paso bajo nivel si OSM lo marca como túnel o bajo el nivel del suelo (layer < 0)."""
    tuneles = datos_tramo.get("tunnel", [])
    capas = datos_tramo.get("layer", [])
    tuneles = tuneles if isinstance(tuneles, list) else [tuneles]
    capas = capas if isinstance(capas, list) else [capas]
    es_tunel = any(t in ("yes", "building_passage") for t in tuneles)
    bajo_suelo = any(str(c).lstrip("-").isdigit() and int(c) < 0 for c in capas)
    return es_tunel or bajo_suelo


def calle_que_cruza(grafo, u, v, calle, distancia_m=200):
    """Busca el nombre de otra calle cerca del paso bajo nivel (la que pasa por encima).
    Mira los tramos que salen de las esquinas a menos de 200 m de los extremos del paso."""
    cercanos = set()
    for extremo in (u, v):
        # cutoff: Dijkstra se detiene a los 200 m. Antes usábamos truncate_graph_dist de OSMnx, que da lo
        # mismo pero mide hasta TODAS las esquinas y copia el grafo entero: con Santiago tardaba casi una hora.
        cercanos |= set(nx.single_source_dijkstra_path_length(grafo, extremo, cutoff=distancia_m, weight="length"))
    nombres = set()
    for nodo in cercanos:
        for _, _, datos in grafo.edges(nodo, data=True):
            nombre = primero(datos.get("name", ""))
            if nombre and nombre != calle and not es_paso_bajo_nivel(datos):
                nombres.add(nombre)
    # Preferimos las avenidas: son las que la gente usa para ubicarse.
    avenidas = sorted(n for n in nombres if n.startswith(("Avenida", "Gran Avenida")))
    return (avenidas or sorted(nombres) or [None])[0]


def quitar_duplicados(puntos, distancia_m=150):
    """Una avenida de doble calzada viene en OSM como dos tramos paralelos, así que un mismo
    paso bajo nivel aparece dos veces a unos 20 m. Si tienen el mismo nombre y están cerca, dejamos uno."""
    unicos = []
    for punto in puntos:
        repetido = any(
            otro["nombre"] == punto["nombre"]
            and ox.distance.great_circle(otro["lat"], otro["lon"], punto["lat"], punto["lon"]) < distancia_m
            for otro in unicos
        )
        if not repetido:
            unicos.append(punto)
    return unicos


def guardar(nombre_archivo, datos, compacto=False):
    ruta = CARPETA_DATOS / nombre_archivo
    with open(ruta, "w", encoding="utf-8") as archivo:
        if compacto:
            json.dump(datos, archivo, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
    print(f"  {ruta.name}: {ruta.stat().st_size / 1024:.0f} KB")


def generar_grafo(rectangulo):
    print("Descargando calles de OpenStreetMap...")
    # "layer" no viene por defecto en OSMnx y lo necesitamos para detectar pasos bajo nivel.
    ox.settings.useful_tags_way = ox.settings.useful_tags_way + ["layer"]
    grafo = ox.graph_from_bbox(rectangulo, network_type="drive")
    # Solo la parte conectada más grande: así no quedan calles "islas" a las que nunca se puede llegar.
    grafo = ox.truncate.largest_component(grafo)
    # Sin sentido de tránsito: cada calle aparece una vez (decisión de Vicente, DECISIONES D2).
    return ox.convert.to_undirected(grafo)


def exportar_grafo(grafo):
    nodos = {str(n): [round(d["y"], 6), round(d["x"], 6)] for n, d in grafo.nodes(data=True)}

    # Entre dos esquinas puede haber más de un tramo (ej. una calle y su caletera): guardamos el más corto.
    tramos = {}
    for u, v, datos in grafo.edges(data=True):
        clave = tuple(sorted((str(u), str(v))))
        largo = round(datos["length"], 1)
        if clave not in tramos or largo < tramos[clave][2]:
            tramos[clave] = [clave[0], clave[1], largo, primero(datos.get("name", "")) or ""]

    guardar("grafo.json", {"nodos": nodos, "aristas": list(tramos.values())}, compacto=True)
    print(f"    {len(nodos)} nodos, {len(tramos)} aristas")


def exportar_puntos_anegados(grafo):
    puntos = {}
    for u, v, datos in grafo.edges(data=True):
        if not es_paso_bajo_nivel(datos):
            continue
        osm_id = f"way/{primero(datos['osmid'])}"  # texto: en OSM un way y un node pueden tener el mismo número
        if osm_id in puntos:
            continue
        # Punto medio del tramo: si OSM trae la forma de la calle se usa; si no, el medio entre las dos esquinas.
        if "geometry" in datos:
            medio = datos["geometry"].interpolate(0.5, normalized=True)
            lat, lon = medio.y, medio.x
        else:
            lat = (grafo.nodes[u]["y"] + grafo.nodes[v]["y"]) / 2
            lon = (grafo.nodes[u]["x"] + grafo.nodes[v]["x"]) / 2
        calle = primero(datos.get("name", "")) or "sin nombre"
        # Se agrega la calle que cruza, para distinguir dos pasos de la misma avenida en el admin.
        cruce = calle_que_cruza(grafo, u, v, calle)
        nombre = f"Paso bajo nivel {calle} / {cruce}" if cruce else f"Paso bajo nivel {calle}"
        puntos[osm_id] = {
            "osm_id": osm_id,
            "nombre": nombre,
            "tipo": "paso_bajo_nivel",
            "lat": round(lat, 6),
            "lon": round(lon, 6),
        }
    puntos = quitar_duplicados(list(puntos.values()))
    guardar("puntos_anegados.json", puntos)
    print(f"    {len(puntos)} pasos bajo nivel")


def descargar_puntos_evacuacion(rectangulo):
    print("Descargando puntos de evacuación...")
    etiquetas = {
        "amenity": ["hospital", "clinic", "fire_station", "police", "school"],
        "emergency": "assembly_point",
    }
    return ox.features_from_bbox(rectangulo, tags=etiquetas)


def exportar_puntos_evacuacion(elementos):
    puntos = []
    for (tipo_elemento, numero), fila in elementos.iterrows():
        tipo_osm = fila.get("amenity") if isinstance(fila.get("amenity"), str) else fila.get("emergency")
        tipo = TIPOS_EVACUACION.get(tipo_osm)
        if tipo is None:
            continue
        # Un hospital suele venir como polígono (el edificio): usamos un punto que cae dentro de él.
        punto = fila.geometry.representative_point()
        nombre = fila.get("name") if isinstance(fila.get("name"), str) else f"{tipo.replace('_', ' ').capitalize()} sin nombre"
        puntos.append({
            "osm_id": f"{tipo_elemento}/{numero}",
            "nombre": nombre,
            "tipo": tipo,
            "lat": round(punto.y, 6),
            "lon": round(punto.x, 6),
        })
    guardar("puntos_evacuacion.json", puntos)
    print(f"    {len(puntos)} puntos de evacuación")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ZONAS:
        sys.exit(f"Indica la zona: python scripts/generar_datos.py <{'|'.join(ZONAS)}>")
    zona = ZONAS[sys.argv[1]]
    rectangulo = (zona["oeste"], zona["sur"], zona["este"], zona["norte"])  # OSMnx pide el rectángulo en este orden
    # Una zona grande tarda más en responder: damos hasta 10 minutos antes de rendirnos
    ox.settings.requests_timeout = 600

    # Primero todo lo que necesita internet. Si una descarga falla, no se alcanza a escribir ningún archivo
    # y la app sigue con los datos anteriores completos (sin mezclar dos zonas).
    grafo = generar_grafo(rectangulo)
    elementos_evacuacion = descargar_puntos_evacuacion(rectangulo)

    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)
    exportar_grafo(grafo)
    exportar_puntos_anegados(grafo)
    exportar_puntos_evacuacion(elementos_evacuacion)
    guardar("zona.json", zona)
    print(f"Listo: zona '{sys.argv[1]}'.")
