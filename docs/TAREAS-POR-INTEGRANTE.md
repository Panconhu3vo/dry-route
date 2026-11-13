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

**Excepción:** lo que aparece en "Tus archivos" dentro de la sección de la persona ya está autorizado para su tarea, aunque sea un modelo o una URL.

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
(esto va a la tabla de Uso de IA de ENTREGA-FINAL.md: pásalo al grupo).
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
| 1 | **T10** Modelo `Reporte` y admin | `feat/t10-modelo-reporte` | lun 9, 14:00 |
| 2 | **T16** Vencimiento, descartados y `preparar_demo` | `feat/t16-vencimiento-demo` | mié 11, 14:00 |
| 3 | **T17** Integración y limpieza (coordinas) | `fix/t17-integracion` | mié 11, 23:00 |
| 4 | **T18** Sesión de traspaso (la dictas) | — | jue 12, 20:00 |
| 5 | **T20** Correcciones y congelar el código | `fix/...` según el caso | vie 13, 23:00 |
| 6 | **T28** Ampliar la cobertura: sector sur y luego todo Santiago | `feat/t28-ampliar-cobertura` | vie 13, 14:00 (sur) y 18:00 (Santiago) |

- **Tus archivos:** `dry-route/rutas/` (`models.py`, `admin.py`, `migrations/`, la vista `mapa` de `views.py`, comandos), `dry-route/backend/`.
- **Eres respaldo de:** T12. Además, cada noche revisas el chequeo de las 21:00 y reasignas lo atrasado.
- **En la presentación:** caso de prueba y dificultad significativa.

## Vicente Zapata — Backend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T12** API de reportes y regla de 2 reportes | `feat/t12-api-reportes` | mar 10, 20:00 |
| 2 | **T19** Pruebas con 5 usuarios (organizas) | `docs/t19-pruebas-usuarios` | vie 13, 18:00 |
| 3 | **T21** Diagrama ER actualizado | `docs/t21-diagrama-er` | vie 13, 23:00 |

- **Tus archivos:** `dry-route/rutas/reportes.py` (nuevo), `dry-route/rutas/tests.py`, `dry-route/rutas/urls.py`, y en `views.py` la vista de reportes y `api_puntos`. También `docs/img/`.
- **Depende de:** T12 necesita el modelo de T10 (lunes a las 14:00). Mientras tanto, lee [DECISIONES.md](DECISIONES.md) D11 y [API.md](API.md).
- **Eres respaldo de:** T10 y T16.
- **En la presentación:** diagrama ER y un cambio de diseño justificado.

## Gonzalo Vega — Frontend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T11** Panel de reporte en la página | `feat/t11-panel-reporte` | lun 9, 22:00 |
| 2 | **T14** Dibujar reportes y recargar puntos | `feat/t14-dibujar-reportes` | mar 10, 22:00 |
| 3 | **T22** Diapositivas (con Yusu) | — | vie 13, 23:00 |

- **Tus archivos:** `dry-route/templates/`, `dry-route/static/css/app.css`, `dry-route/static/js/mapa.js`.
- **Importante:** T11 va primero porque Cristóbal y Yusu usan esos `id`. Respeta la lista de [API.md](API.md#contrato-interno-del-frontend).
- **Eres respaldo de:** T13.
- **En la presentación:** demo de la funcionalidad corazón.

## Cristóbal Vargas — Frontend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T13** Formulario de reporte | `feat/t13-formulario-reporte` | mar 10, 22:00 |
| 2 | **T23** Guion y banco de preguntas | `docs/t23-guion` | vie 13, 23:00 |
| 3 | **T27** Subir video y presentación al Aula | — | dom 15, 23:00 |

- **Tus archivos:** `dry-route/static/js/reporte.js` (nuevo), `dry-route/static/js/entrada.js`, `dry-route/static/css/reporte.css` (nuevo), `docs/ENTREGA-FINAL.md`.
- **Depende de:** los `id` de T11 (lunes a las 22:00). Mientras tanto, usa las respuestas de ejemplo de [API.md](API.md).
- **Eres respaldo de:** T15.
- **En la presentación:** pitch.

## Yusu Zhan — Frontend

| Orden | Tarea | Rama | Plazo |
|---|---|---|---|
| 1 | **T15** Confirmación y recálculo de la ruta | `feat/t15-recalculo` | mié 11, 14:00 |
| 2 | **T22** Diapositivas (con Gonzalo) | — | vie 13, 23:00 |
| 3 | **T25** Video de respaldo (máximo 3 minutos) | — | sáb 14, 22:00 |

- **Tus archivos:** `dry-route/static/js/resultado.js`, `dry-route/static/css/avisos.css` (nuevo).
- **Depende de:** `DryRoute.calcularRuta` de T13. Mientras no exista, prueba con una función de ejemplo.
- **Eres respaldo de:** T11 y T14.
- **En la presentación:** demo del reporte colaborativo y la persistencia.

## Todos

- Lunes a miércoles: chequeo a las 21:00 en el grupo.
- **Jue 12, 20:00:** sesión de traspaso (T18).
- **Sáb 14, 16:00:** ensayo 1 (T24). **Dom 15, 18:00:** ensayo 2 y simulacro de defensa (T26).
- Cada uno consigue **1 persona** para las pruebas de T19 y estudia su archivo de `explicaciones/`.
