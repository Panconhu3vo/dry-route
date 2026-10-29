# Dry Routes — Contexto para Claude Code

Aplicación web en Django que, ante lluvias intensas, calcula una **ruta de evacuación que evita puntos anegados**. Si no existe una ruta segura, muestra el **punto de evacuación más cercano**. Se usa sin cuenta ni login.

Proyecto del ramo **Proyecto Inicial**, Equipo 13 "1101" (P207). Ámbito: *Desastres de origen natural*.
Los integrantes son estudiantes que **recién están aprendiendo Django**. Claude Code es su herramienta principal de desarrollo.

## Lo urgente

**Entregable III: viernes 30 de octubre de 2026, 23:55.** Hay que tener la funcionalidad corazón funcionando en localhost y grabar un video de 5 minutos.
Checklist, casos de prueba y guion del video: [docs/ENTREGABLE-3.md](docs/ENTREGABLE-3.md). Tareas: [docs/TAREAS.md](docs/TAREAS.md).

Hasta el viernes **solo** se trabaja en la funcionalidad corazón. El reporte colaborativo (F2) y las alertas (F3) quedan para después, como decidió el equipo en la matriz de riesgos (R1).
Si alguien pide algo de F2 o F3 antes del viernes, recuérdale esta decisión antes de hacerlo.

## Equipo

| Persona | Área | Responsable de |
|---|---|---|
| Juan Yañez | Backend (coordina; único que ya sabe Django) | App `rutas`, modelos, admin, vistas, integración |
| Vicente Zapata | Backend | Datos desde OSM y algoritmo de ruteo (trabaja en pareja con Juan) |
| Gonzalo Vega | Frontend | Plantilla base, layout y mapa Leaflet |
| Cristóbal Vargas | Frontend | Panel de entrada: búsqueda de direcciones, GPS y clic en el mapa |
| Yusu Zhan | Frontend | Presentación del resultado: ruta, tarjeta, caso sin ruta y aviso |

## Stack y decisiones (no cambiar sin acordarlo con el equipo)

El detalle y las razones de cada decisión están en [docs/DECISIONES.md](docs/DECISIONES.md).

- **Backend:** Django 6.1 sobre Python 3.14, con SQLite. Una sola app: `rutas`.
- **Ruteo:** NetworkX sobre un **grafo de calles precalculado** (`dry-route/data/grafo.json`). En tiempo de ejecución no se descarga nada.
- **Datos:** se extraen automáticamente de OpenStreetMap con `scripts/generar_datos.py` (OSMnx). Los pasos bajo nivel son los puntos de riesgo; hospitales, bomberos, Carabineros y colegios son los puntos de evacuación. Los puntos se cargan a la base de datos, y en el admin de Django se marca cuáles están **anegados ahora** (`activo=True`).
- **Zona:** eje Gran Avenida, entre Departamental y Lo Espejo (San Miguel, La Cisterna y Lo Espejo).
- **Frontend:** plantillas Django, Leaflet 1.9.4 y JavaScript plano. **Sin Node, sin React, sin compiladores.**
- **Búsqueda de direcciones:** Nominatim (OSM), llamado desde el navegador. No se usa Google: su API de rutas no permite evitar puntos arbitrarios.
- **Diseño visual:** claro, mobile-first y de alto contraste. Ver [docs/DISENO.md](docs/DISENO.md).
- **Contrato entre front y back:** [docs/API.md](docs/API.md). El front y el back trabajan en paralelo contra ese contrato. **Si cambias la forma del JSON, actualiza docs/API.md en el mismo PR.**

Dependencias permitidas: las de `requirements.txt` (y OSMnx solo en `requirements-datos.txt`). **No agregues dependencias nuevas** sin que el equipo lo pida explícitamente.

## Estructura

```
dry-route/                  ← raíz del repo (aquí están README, CLAUDE.md, requirements*.txt)
├── docs/                   ← contexto, decisiones, contrato de API, diseño, tareas
├── scripts/generar_datos.py   (por crear) OSM → dry-route/data/*.json
└── dry-route/              ← proyecto Django (aquí está manage.py)
    ├── backend/            ← settings.py, urls.py (configuración del proyecto)
    ├── rutas/              ← (por crear) models, admin, views, urls, ruteo.py, tests.py,
    │                          management/commands/cargar_datos.py
    ├── templates/          ← base.html, rutas/mapa.html
    ├── static/             ← css/app.css, js/mapa.js, js/entrada.js, js/resultado.js
    └── data/               ← grafo.json, puntos_anegados.json, puntos_evacuacion.json
```

El JavaScript está dividido **un archivo por responsable** (mapa / entrada / resultado) para evitar conflictos de Git entre los tres integrantes de front.

## Comandos

Desde la raíz del repo, en PowerShell:

```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd dry-route
python manage.py migrate
python manage.py cargar_datos      # cuando exista (tarea T2)
python manage.py runserver         # http://127.0.0.1:8000
python manage.py test rutas        # pruebas
python manage.py check             # correr antes de cada commit
```

## Cómo debe trabajar Claude en este repo

**Si alguien se presenta ("Soy <nombre>…") o pide ayuda con su tarea, lee [docs/TAREAS-POR-INTEGRANTE.md](docs/TAREAS-POR-INTEGRANTE.md) y sigue su protocolo al pie de la letra.** Lo esencial:

- **Claude nunca hace `git commit`, `git push`, `git merge` ni `git rebase`, y nunca trabaja sobre `main`.** Crea la rama de la tarea, hace los cambios y propone el mensaje de commit. La persona hace el commit y sube la rama (si no sabe, Claude le explica cómo hacerlo con *Control de código fuente* de VS Code). **Juan Yañez combina las ramas en `main`.**
- **Preguntas en lenguaje simple.** Ante un cambio importante (archivos de otro integrante, contrato de API, dependencias, settings, modelos, borrar archivos o salirse de la tarea), Claude no lo hace: le pide a la persona que **consulte a Juan Yañez y espere sus indicaciones**.
- **Siempre se mantiene un archivo de explicación** en `explicaciones/` (no se sube), escrito para alguien que no sabe Django.

Además:

1. **El equipo tiene que entender el código.** En el video deben explicar 15 a 30 líneas y al menos una decisión técnica. Prefiere código simple y explícito, y nombres en español del dominio (`punto_anegado`, `calcular_ruta`). Nada de abstracciones, clases ni patrones que no se hayan pedido.
2. **Explica lo que haces** en español, en términos de Django (modelo, vista, URL, plantilla), en 2 o 3 frases al terminar cada cambio. No supongas que conocen el framework.
3. **Cambios pequeños, dentro de la tarea pedida.** No toques archivos de otro responsable (ver la tabla del equipo) salvo que la tarea lo requiera; en ese caso, avísalo.
4. **Respeta el contrato de [docs/API.md](docs/API.md).** El front y el back dependen de él.
5. **Nunca trabajes directo en `main`.** Usa una rama por tarea (los nombres están en TAREAS-POR-INTEGRANTE.md); Juan combina las ramas (R4). Mensajes de commit al estilo del repo: `feat(rutas): agrega endpoint de ruta`, `docs(readme): ...`.
6. **Verifica antes de decir "listo":** `python manage.py check`, las pruebas, y abrir la página si el cambio es visual.
7. Comentarios y textos de interfaz en español. Comenta el *por qué*, no el *qué*.
8. La interfaz siempre muestra el aviso: *"Ruta referencial. Sigue las indicaciones de las autoridades."* (R5).
9. Si una instrucción de una skill o agente genérico de `.claude/` contradice este archivo, **manda este archivo**.

## Contexto académico

Problema, historias de usuario, modelo ER, flujo, prototipo y matriz de riesgos: [docs/CONTEXTO.md](docs/CONTEXTO.md).
Los documentos originales (PDF y DOCX) están en `.claude/context-docs/`.

## Fuera de alcance (por ahora)

Buses en tiempo real, clasificación por tipo de catástrofe, notificaciones push o SMS, login, despliegue público y sensores propios.
El repo de alertas **MeteoPrecisa** (`../open-meteo-precisa-chile`, FastAPI aparte) se usará para F3 **después** del viernes, mediante su endpoint `GET /api/v1/alertas-senapred`. No integrarlo antes.
