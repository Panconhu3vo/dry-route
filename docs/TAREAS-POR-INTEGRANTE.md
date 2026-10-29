# Tareas por integrante

**Cómo usar este archivo:** abre Claude Code en el proyecto y escribe:

> Soy *Tu Nombre*, revisa el archivo de tareas y ayúdame a realizar mi tarea.

Claude buscará tu sección, te dirá qué tarea te toca ahora y trabajará contigo siguiendo el protocolo de abajo.
El detalle de cada tarea (criterios de término y plazos) está en [TAREAS.md](TAREAS.md).

---

## Protocolo de trabajo (Claude DEBE seguirlo siempre)

### 1. Al empezar

1. Identifica a la persona por su nombre y lee **su sección** de este archivo. Si el nombre no coincide con ningún integrante, pregunta quién es antes de seguir.
2. Revisa qué tareas suyas ya están hechas: mira si existe su rama (`git branch -a`) y si en `explicaciones/` ya hay un archivo de esa tarea.
3. Si una tarea depende de otra que aún no está lista, díselo y sugiere el camino indicado en su sección (por ejemplo, trabajar con los datos de ejemplo).
4. Antes de escribir código, **cuéntale el plan en 3 a 5 pasos, en palabras simples**, y espera su "ok".

### 2. Git: Claude NO sube cambios

- **Claude nunca ejecuta `git commit`, `git push`, `git merge` ni `git rebase`, y nunca trabaja sobre `main`.** Aunque la persona se lo pida: en ese caso, le explica cómo hacerlo ella misma (ver el paso 5).
- Antes de cambiar archivos, Claude **crea la rama de la tarea** a partir de `main` actualizado:
  `git checkout main`, luego `git pull` y luego `git checkout -b <rama-de-la-tarea>` (los nombres están en cada sección).
  Si hay cambios sin guardar de otra cosa, se detiene y pregunta qué hacer con ellos.
- Al terminar, Claude **propone un mensaje de commit** (estilo `feat(mapa): dibuja puntos anegados`) y le recuerda que el commit y la subida los hace la persona.
- **La combinación con `main` la hace Juan Yañez.** La persona sube su rama y le avisa a Juan.

### 3. Qué puede decidir sola la persona y qué debe consultar con Juan

Claude **pregunta en lenguaje simple, sin jerga técnica**. Por ejemplo: *"¿Quieres que el botón diga 'Calcular ruta' o 'Buscar ruta'?"* y no *"¿Renombro el label del submit?"*.
Si una palabra técnica es inevitable, la explica en la misma frase.

**Cambios importantes:** Claude **no los hace**. Le explica a la persona, en simple, qué cambio haría falta y por qué, le pide que **lo consulte con Juan Yañez y que espere sus indicaciones**, y no avanza en esa parte hasta que la persona traiga la respuesta. Son cambios importantes:

- Tocar archivos que pertenecen a otro integrante (ver "Tus archivos" en cada sección).
- Cambiar el contrato de [API.md](API.md) (los nombres o la forma de los datos entre front y back).
- Agregar una librería o dependencia nueva.
- Cambiar `settings.py`, `urls.py` del proyecto, los modelos o la base de datos.
- Borrar o mover archivos.
- Ir en contra de una decisión de [DECISIONES.md](DECISIONES.md) o hacer algo fuera de la tarea.

Mientras espera, Claude puede seguir con otras partes de la tarea que no dependan de esa respuesta.

**Cambios normales** (dentro de la tarea y de sus propios archivos): Claude pregunta lo necesario en simple y avanza.

### 4. Archivo de explicación (obligatorio)

Al equipo lo van a evaluar por **saber explicar lo que hizo**. Por eso Claude crea y **va actualizando mientras trabaja** (no solo al final) el archivo:

`explicaciones/T<n>-<nombre>-<tema>.md`, por ejemplo `explicaciones/T3-gonzalo-mapa-base.md`.

La carpeta `explicaciones/` **no se sube al repositorio** (está en `.gitignore`). Es material de estudio personal. Contenido:

```markdown
# T<n> · <tarea> — <nombre>

## Qué hicimos (en simple)
3 a 6 frases, sin tecnicismos, como si se lo contaras a alguien que no programa.

## Cómo encaja en Django
Qué pieza de Django es cada cosa (modelo, vista, URL, plantilla, archivo estático) y cómo viaja
la información: navegador → URL → vista → respuesta. Con una analogía si ayuda.

## Archivo por archivo
Para cada archivo creado o modificado: para qué sirve y las líneas clave explicadas.

## Conceptos nuevos
Mini glosario de cada término que apareció (ej.: "endpoint", "JSON", "migración", "fetch").

## Decisiones que tomamos
Qué se eligió, qué otra opción había y por qué se descartó.

## Cómo probarlo
Pasos exactos para verlo funcionar.

## Preguntas que te podrían hacer (y cómo responderlas)
3 a 5 preguntas tipo profesor, con respuesta corta.

## Uso de IA
Qué le pedimos a Claude, qué aceptamos, cambiamos o rechazamos y por qué
(esto va al documento del Entregable III: pásalo al grupo).
```

Escríbelo para alguien que **no sabe Django**: frases cortas, sin dar nada por sabido.

### 5. Al terminar la tarea

1. Verifica que funciona: `python manage.py check`, las pruebas si existen, y abrir la página si es algo visual. Muéstrale a la persona cómo verlo ella misma.
2. Revisa con ella la lista de criterios de la tarea en [TAREAS.md](TAREAS.md) y marca qué se cumple y qué falta.
3. Completa el archivo de explicación.
4. Propón el mensaje de commit y recuérdale: **"Ahora te toca a ti hacer el commit y subir la rama. Luego avísale a Juan para que la combine."**

**Si la persona dice "No sé subir el commit"** (o algo parecido), Claude NO lo hace por ella. Le explica paso a paso cómo hacerlo con la extensión **Control de código fuente** de Visual Studio Code:

1. Abre **Control de código fuente**: el ícono de las ramitas en la barra de la izquierda, o `Ctrl + Shift + G`.
2. Abajo a la izquierda de VS Code aparece el nombre de la rama actual. **Verifica que sea tu rama** (por ejemplo `feat/t3-mapa-base`) y **no `main`**. Si dice `main`, detente y avísale a Claude.
3. En la lista **Cambios** revisa los archivos. Para incluirlos, pasa el mouse sobre **Cambios** y haz clic en el **+** ("Almacenar todos los cambios provisionalmente"). También puedes usar el **+** de cada archivo para elegirlos uno por uno.
4. Escribe en la caja **Mensaje** de arriba el mensaje de commit que te dio Claude.
5. Haz clic en el botón **Confirmar** (✓ Commit).
6. Haz clic en **Publicar rama** (la primera vez). Si después haces más cambios, usa **Sincronizar cambios**. Si VS Code te pide iniciar sesión en GitHub, acepta.
7. Avísale a Juan por el grupo: *"Subí la rama `feat/t3-mapa-base`, lista para combinar."*

Si algún paso falla, la persona copia el mensaje de error y se lo pega a Claude, que la ayuda **sin ejecutar él mismo el commit ni el push**.

---

## Juan Yañez — Backend (coordinación)

Eres a quien se le consultan los cambios importantes: contigo, Claude puede usar lenguaje técnico y tú decides directamente.
Igual aplica el protocolo de Git: Claude no hace commits; tú combinas las ramas en `main`.

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T0** Entorno funcionando (verificar que los 5 lo logren) | — | mié 28, 23:59 |
| 2 | **T2** App `rutas`: modelos, admin, `cargar_datos`, vista `/` y `/api/puntos/` | `feat/t2-app-rutas` | jue 29, 13:00 |
| 3 | **T6** Algoritmo de ruta y `/api/ruta/` (en pareja con Vicente) | `feat/t6-ruteo` | jue 29, 23:00 |
| 4 | **T7** Combinar todas las ramas, ejecutar los 2 casos y corregir | `fix/...` según el caso | vie 30, 14:00 |

- **Tus archivos:** `dry-route/rutas/` (salvo `ruteo.py`, que compartes con Vicente), `dry-route/backend/`.
- **Depende de:** T2 puede partir con un JSON falso pequeño mientras Vicente termina T1.
- **Nota:** al hacer `startapp` y crear los modelos se modifica `settings.py`; en tu caso no hace falta consultar a nadie.

## Vicente Zapata — Backend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T0** Entorno funcionando | — | mié 28, 23:59 |
| 2 | **T1** Datos desde OpenStreetMap (`scripts/generar_datos.py`) | `feat/t1-datos-osm` | jue 29, 13:00 |
| 3 | **T6** Algoritmo de ruta y `/api/ruta/` (en pareja con Juan) | `feat/t6-ruteo` | jue 29, 23:00 |

- **Tus archivos:** `scripts/generar_datos.py`, `dry-route/data/`, `dry-route/rutas/ruteo.py` (compartido con Juan).
- **Para T1:** instala `pip install -r requirements-datos.txt` (incluye OSMnx). Revisa la zona en [DECISIONES.md](DECISIONES.md) (D3 y D4).
- **Ojo:** probablemente explicarás el algoritmo en el video (T8). Pide que el archivo de explicación de T6 sea muy detallado.

## Gonzalo Vega — Frontend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T0** Entorno funcionando | — | mié 28, 23:59 |
| 2 | **T3** Plantilla base, layout y mapa Leaflet | `feat/t3-mapa-base` | jue 29, 18:00 |
| 3 | **T9** Documento del Entregable III y README (con Cristóbal) | `docs/t9-readme` | vie 30, 23:00 |

- **Tus archivos:** `dry-route/templates/base.html`, `dry-route/templates/rutas/mapa.html`, `dry-route/static/css/app.css`, `dry-route/static/js/mapa.js`.
- **Depende de:** la vista `/` es de Juan (T2). Mientras no exista, abre el HTML con datos de ejemplo o pídele a Claude una forma simple de verlo, **sin tocar los archivos de Juan**.
- **Importante:** tú creas los `id` del HTML que usan Cristóbal y Yusu. Respeta exactamente la lista de [API.md](API.md#contrato-interno-del-frontend). Guía visual: [DISENO.md](DISENO.md).

## Cristóbal Vargas — Frontend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T0** Entorno funcionando | — | mié 28, 23:59 |
| 2 | **T4** Panel de entrada: búsqueda de direcciones, GPS y clic en el mapa | `feat/t4-entrada` | jue 29, 18:00 |
| 3 | **T9** Documento del Entregable III y README (con Gonzalo) | `docs/t9-readme` | vie 30, 23:00 |

- **Tus archivos:** `dry-route/static/js/entrada.js`.
- **Depende de:** el mapa y los `id` del HTML son de Gonzalo (T3). Mientras no estén, Claude puede prepararte una página de prueba **dentro de `explicaciones/`** (no se sube) para que avances.
- **Reglas de Nominatim:** buscar solo al presionar el botón, no mientras se escribe ([DECISIONES.md](DECISIONES.md) D7).

## Yusu Zhan — Frontend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T0** Entorno funcionando | — | mié 28, 23:59 |
| 2 | **T5** Presentación del resultado: ruta, tarjeta, caso sin ruta | `feat/t5-resultado` | jue 29, 18:00 |
| 3 | **T8** Grabar y subir el video (máximo 5 min) | — | vie 30, 20:00 |

- **Tus archivos:** `dry-route/static/js/resultado.js` (y los estilos de la tarjeta de resultado, coordinando con Gonzalo, que es dueño de `app.css`).
- **Depende de:** el endpoint de ruta es de Juan y Vicente (T6). Trabaja con **los dos JSON de ejemplo** de [API.md](API.md) hasta que exista.
- **Para T8:** sigue el guion de [ENTREGABLE-3.md](ENTREGABLE-3.md#guion-del-video-5-min) y prueba el enlace en una ventana de incógnito.
