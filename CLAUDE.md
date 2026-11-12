# Dry Routes — Contexto para Claude Code

Aplicación web en Django que, ante lluvias intensas, calcula una **ruta de evacuación que evita puntos anegados**. Si no existe una ruta segura, muestra el **punto de evacuación más cercano**. Se usa sin cuenta ni login.

Proyecto del ramo **Proyecto Inicial**, Equipo 13 "1101" (P207). Ámbito: *Desastres de origen natural*.
Los integrantes son estudiantes que **recién están aprendiendo Django**. Claude Code es su herramienta principal de desarrollo.

## Lo urgente

**Entrega final (P4, 20%): todo terminado y subido el domingo 15 de noviembre de 2026.** Hasta el lunes 16 hay que subir al Aula un video de respaldo de máximo 3 minutos y el archivo de la presentación. La presentación en vivo (13 minutos) es entre el 16 y el 30 de noviembre, según el paralelo.
Pauta resumida, guion y banco de preguntas: [docs/ENTREGA-FINAL.md](docs/ENTREGA-FINAL.md). Plan día a día: [docs/TAREAS.md](docs/TAREAS.md).

La funcionalidad corazón está implementada. Lo que falta es la segunda funcionalidad, el **reporte colaborativo (F2)**, y preparar la defensa. Las alertas (F3) quedan fuera (DECISIONES D10).
**El código se congela el viernes 13 a las 23:00.** Después de esa hora, si alguien pide algo que no sea corregir un error que impida la demo, recuérdale esta decisión y pídele que lo consulte con Juan.

## Equipo

| Persona | Área | Responsable de |
|---|---|---|
| Juan Yañez | Backend (coordina; único que ya sabe Django) | App `rutas`, modelos, admin, vistas, integración |
| Vicente Zapata | Backend | Datos desde OSM, algoritmo de ruteo y API de reportes |
| Gonzalo Vega | Frontend | Plantilla base, layout, mapa Leaflet y reportes en el mapa |
| Cristóbal Vargas | Frontend | Panel de entrada (dirección, GPS y clic en el mapa) y formulario de reporte |
| Yusu Zhan | Frontend | Presentación del resultado: ruta, tarjeta, caso sin ruta, avisos y recálculo |

## Stack y decisiones (no cambiar sin acordarlo con el equipo)

El detalle y las razones de cada decisión están en [docs/DECISIONES.md](docs/DECISIONES.md).

- **Backend:** Django 6.1 sobre Python 3.14, con SQLite. Una sola app: `rutas`.
- **Ruteo:** NetworkX sobre un **grafo de calles precalculado** (`dry-route/data/grafo.json`). En tiempo de ejecución no se descarga nada.
- **Datos:** se extraen automáticamente de OpenStreetMap con `scripts/generar_datos.py` (OSMnx). Los pasos bajo nivel son los puntos de riesgo; hospitales, bomberos, Carabineros y colegios son los puntos de evacuación. Los puntos se cargan a la base de datos, y en el admin de Django se marca cuáles están **anegados ahora** (`activo=True`).
- **Reportes colaborativos:** un reporte no bloquea rutas por sí solo. Dos reportes de personas distintas a menos de 100 m activan un `PuntoAnegado`, y `ruteo.py` lo evita sin cambios (DECISIONES D11).
- **Zona:** eje Gran Avenida, entre Departamental y Américo Vespucio (San Miguel, La Cisterna y alrededores).
- **Frontend:** plantillas Django, Leaflet 1.9.4 y JavaScript plano. **Sin Node, sin React, sin compiladores.**
- **Búsqueda de direcciones:** Nominatim (OSM), llamado desde el navegador. No se usa Google: su API de rutas no permite evitar puntos arbitrarios.
- **Diseño visual:** claro, mobile-first y de alto contraste. Ver [docs/DISENO.md](docs/DISENO.md).
- **Contrato entre front y back:** [docs/API.md](docs/API.md). El front y el back trabajan en paralelo contra ese contrato. **Si cambias la forma del JSON, actualiza docs/API.md en el mismo PR.**

Dependencias permitidas: las de `requirements.txt` (y OSMnx solo en `requirements-datos.txt`). **No agregues dependencias nuevas** sin que el equipo lo pida explícitamente.

## Estructura

```
dry-route/                  ← raíz del repo (aquí están README, CLAUDE.md, requirements*.txt)
├── docs/                   ← contexto, decisiones, contrato de API, diseño, tareas
├── scripts/generar_datos.py   OSM → dry-route/data/*.json
└── dry-route/              ← proyecto Django (aquí está manage.py)
    ├── backend/            ← settings.py, urls.py (configuración del proyecto)
    ├── rutas/              ← models, admin, views, urls, ruteo.py, tests.py,
    │                          management/commands/cargar_datos.py
    ├── templates/          ← base.html, rutas/mapa.html
    ├── static/             ← css/ (app, reporte, avisos), js/ (mapa, entrada, resultado, reporte)
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
python manage.py cargar_datos      # carga los puntos a la base de datos
python manage.py preparar_demo     # borra reportes y deja anegado solo el paso de la demo
python manage.py runserver         # http://127.0.0.1:8000
python manage.py test rutas        # pruebas
python manage.py check             # correr antes de cada commit
```

## Cómo debe trabajar Claude en este repo

**Si alguien se presenta ("Soy <nombre>…") o pide ayuda con su tarea, lee [docs/TAREAS-POR-INTEGRANTE.md](docs/TAREAS-POR-INTEGRANTE.md) y sigue su protocolo al pie de la letra.** Lo esencial:

- **Claude nunca hace `git commit`, `git push`, `git merge` ni `git rebase`, y nunca trabaja sobre `main`.** Crea la rama de la tarea, hace los cambios y propone el mensaje de commit. La persona hace el commit y sube la rama (si no sabe, Claude le explica cómo hacerlo con *Control de código fuente* de VS Code). **Juan Yañez combina las ramas en `main`.**
- **Preguntas en lenguaje simple.** Ante un cambio importante (archivos de otro integrante, contrato de API, dependencias, settings, modelos, borrar archivos o salirse de la tarea), salvo lo que la tarea de esa persona incluya en *Tus archivos*, Claude no lo hace: le pide a la persona que **consulte a Juan Yañez y espere sus indicaciones**.
- **Siempre se mantiene un archivo de explicación** en `explicaciones/` (no se sube), escrito para alguien que no sabe Django.

Además:

1. **El equipo tiene que entender el código.** En la defensa, todos deben poder explicar la aplicación, sus decisiones y lo hecho con IA, aunque hayan trabajado en otra parte. Prefiere código simple y explícito, y nombres en español del dominio (`punto_anegado`, `calcular_ruta`). Nada de abstracciones, clases ni patrones que no se hayan pedido.
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

Alertas vigentes (F3), buses en tiempo real, clasificación por tipo de catástrofe, notificaciones push o SMS, login, despliegue público y sensores propios.
El repo de alertas **MeteoPrecisa** (`../open-meteo-precisa-chile`, FastAPI aparte) no se integra en la entrega final.
