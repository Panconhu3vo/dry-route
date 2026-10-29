# Dry Routes

Aplicación web que, durante lluvias intensas, calcula una **ruta de evacuación que evita los puntos anegados** (pasos bajo nivel). Si no existe una ruta segura, indica el **punto de evacuación más cercano**. Se usa sin registro.

Proyecto del ramo Proyecto Inicial: Equipo 13 "1101" (P207). Integrantes: Juan Yañez, Vicente Zapata, Cristóbal Vargas, Gonzalo Vega y Yusu Zhan.

> **Ruta referencial.** Esta herramienta es un prototipo académico. En una emergencia real, sigue las indicaciones de las autoridades.

## Requisitos

- Python 3.14 (probado en Windows 11)
- Git

## Cómo ejecutarla (localhost)

En PowerShell, desde la carpeta donde quieras el proyecto:

```powershell
git clone https://github.com/Panconhu3vo/dry-route.git
cd dry-route

python -m venv venv
venv\Scripts\Activate.ps1            # si PowerShell lo bloquea: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt

cd dry-route
python manage.py migrate
python manage.py cargar_datos        # carga los puntos anegados y de evacuación (disponible desde la tarea T2)
python manage.py createsuperuser     # para entrar al admin y simular anegamientos
python manage.py runserver
```

Abre http://127.0.0.1:8000.

## Probar la funcionalidad corazón

1. Entra a http://127.0.0.1:8000/admin/ → **Puntos anegados** → marca **activo** en el paso bajo nivel que quieras simular como anegado.
2. Vuelve a http://127.0.0.1:8000, elige el origen y el destino (con búsqueda o con un clic en el mapa) y presiona **Calcular ruta**.
3. Los casos de prueba del Entregable III están en [docs/ENTREGABLE-3.md](docs/ENTREGABLE-3.md).

Los datos (grafo de calles, pasos bajo nivel y puntos de evacuación) ya vienen en `dry-route/data/`, extraídos de © OpenStreetMap contributors. Para regenerarlos: `pip install -r requirements-datos.txt` y luego `python scripts/generar_datos.py`.

## Documentación

| Archivo                                  | Contenido                                                    |
| ---------------------------------------- | ------------------------------------------------------------ |
| [CLAUDE.md](CLAUDE.md)                   | Contexto para Claude Code (y resumen general para el equipo) |
| [docs/TAREAS.md](docs/TAREAS.md)         | Tareas y plazos hasta el Entregable III                      |
| [docs/TAREAS-POR-INTEGRANTE.md](docs/TAREAS-POR-INTEGRANTE.md) | Qué le toca a cada uno y cómo trabajar con Claude |
| [docs/API.md](docs/API.md)               | Contrato entre frontend y backend                            |
| [docs/DECISIONES.md](docs/DECISIONES.md) | Decisiones técnicas y sus razones                            |
| [docs/DISENO.md](docs/DISENO.md)         | Guía visual                                                  |
| [docs/CONTEXTO.md](docs/CONTEXTO.md)     | Problema, historias de usuario, modelo ER y riesgos          |

## Cómo trabajamos con Git

Abre Claude Code y escribe: *"Soy &lt;tu nombre&gt;, revisa el archivo de tareas y ayúdame a realizar mi tarea"*. El detalle está en [docs/TAREAS-POR-INTEGRANTE.md](docs/TAREAS-POR-INTEGRANTE.md).

1. Claude crea la rama de tu tarea (por ejemplo `feat/t3-mapa-base`) y hace los cambios contigo. **Claude no hace commits ni sube nada.**
2. **Tú** haces el commit y subes la rama desde *Control de código fuente* en VS Code.
3. Le avisas a **Juan**, que revisa y combina la rama en `main`. Nadie sube cambios directo a `main`.

## Fuentes

- Repositorio de alertas meteorológicas (se usará para la funcionalidad 3): [github.com/elpabloultron/open-meteo-precisa-chile](https://github.com/elpabloultron/open-meteo-precisa-chile)
- Datos de calles: [OpenStreetMap](https://www.openstreetmap.org/copyright). Búsqueda de direcciones: [Nominatim](https://nominatim.org/).
