# Pruebas con usuarios (T19)

Guía para que los 5 integrantes hagan la prueba **de la misma forma**. Responsable: Vicente. Plazo: vie 13, 18:00.

**Objetivo:** saber si una persona que nunca vio Dry Routes puede, **sin ayuda**, calcular una ruta segura y reportar un problema. Lo que encontremos alimenta las correcciones de T20 (Juan).

## Quiénes y cuándo

- Cada integrante consigue **1 persona** que no sea del equipo y que no haya visto la app. Mejor si no estudia informática.
- **Cuándo:** jueves 12 o viernes 13 en la mañana, con `main` actualizado después de la integración (T17). **Ojalá el jueves**, para que Juan tenga tiempo de corregir.
- **Duración:** unos 15 minutos por persona.

## Modalidad

- **Presencial (la principal):** la persona usa tu computador y tú miras a su lado.
- **Videollamada (solo si no se puede presencial):** la app corre únicamente en tu computador (localhost), así que la persona **debe tomar el control de tu mouse**, por ejemplo con "Solicitar control remoto" de Zoom. Si solo mira y te dice dónde hacer clic, la prueba **no sirve**: estarías usando la app tú.
- Anota la modalidad en la hoja.

## Antes de cada prueba (5 min)

1. `git pull` en `main`, luego `python manage.py migrate` y `python manage.py runserver`.
2. Deja el escenario de la demo:
   - Si ya existe el comando de Juan (T16): `python manage.py preparar_demo`.
   - Si no existe: en http://127.0.0.1:8000/admin/ borra todos los **Reportes**, borra los puntos anegados con fuente "Reportes ciudadanos" y deja activo **solo** el paso *Avenida Departamental / Gran Avenida*.
3. **Repite el paso 2 antes de cada persona.** Si no, el reporte de la persona anterior sigue ahí, y el de la nueva lo confirmaría (son sesiones distintas).
4. Abre http://127.0.0.1:8000 en una **ventana de incógnito** y déjala a pantalla completa.
5. Ten a mano el cronómetro del celular y una copia de la hoja de anotación.

## Qué decirle a la persona (léelo tal cual)

> "Gracias por ayudarnos. Estamos probando una página web, **no te estamos probando a ti**: si algo no te resulta, es culpa de la página y eso es justo lo que queremos encontrar.
> Te voy a pedir dos cosas. Mientras las haces, intenta **decir en voz alta lo que piensas**: qué buscas, qué esperas que pase, qué te confunde.
> No te voy a ayudar, porque necesito ver si la página se entiende sola. Si en algún momento quieres rendirte, dime 'me rindo' y pasamos a lo siguiente. No anoto tu nombre ni ningún dato tuyo."

## Reglas para quien observa

- **No ayudes ni expliques.** Tampoco señales la pantalla ni digas "casi" o "por ahí no".
- Si pregunta algo, devuélvele la pregunta: *"¿Qué crees tú que pasaría?"*
- Si lleva **más de 1 minuto trabado**, dale **una** pista corta (por ejemplo, *"¿Qué hay en el panel de la izquierda?"*) y anota **"con ayuda"** y qué pista diste.
- Máximo **5 minutos por tarea**. Si se acaba el tiempo, anota **"no lo logró"** y pasa a la siguiente.
- Anota las frases textuales que diga ("¿y esto qué es?", "no sé dónde apretar"). Son lo más valioso.

## Las dos tareas

Léele cada tarea en voz alta y **empieza el cronómetro cuando termines de leer**. Detenlo cuando la persona logre el objetivo o diga "me rindo".

### Tarea 1: calcular una ruta

> "Está lloviendo muy fuerte en Santiago. Estás en el **CESFAM Barros Luco** y necesitas llegar a la **Cuarta Compañía de Bomberos Metropolitano Sur**. Usa la página para saber por dónde ir de forma segura."

- **Logrado cuando:** aparece la ruta en el mapa con su tarjeta de resultado.
- **Fíjate en:** si encuentra cómo marcar el origen y el destino, si entiende el círculo rojo y si lee el aviso "Ruta referencial".

### Tarea 2: reportar un problema

> "Ahora imagina que, cerca del CESFAM Barros Luco, ves una calle con tanta agua que no se puede pasar. Usa la página para avisarles a otras personas."

- **Logrado cuando:** aparece el mensaje *"Reporte recibido. Falta que otra persona confirme este lugar."*
- **Fíjate en:** si encuentra el botón para reportar, si entiende que debe marcar el lugar en el mapa y si entiende el mensaje de que falta otra confirmación.

## Preguntas al final (2 min)

1. Del 1 (muy difícil) al 5 (muy fácil): ¿qué tan fácil fue la tarea 1? ¿Y la tarea 2?
2. ¿Qué crees que significaba el **círculo rojo** del mapa?
3. ¿Confiarías en esta ruta en una emergencia real? ¿Por qué?
4. ¿Qué fue lo que más te confundió?
5. ¿Qué cambiarías o agregarías?

## Hoja de anotación (una por persona)

Copia esto en un mensaje o en papel, llénalo **al terminar la prueba** (no después, porque se olvida) y envíaselo a **Vicente** (lista de errores) y a **Cristóbal** (tabla de resultados).

```
Integrante que observó:
Persona: 1 / 2 / 3 / 4 / 5     (sin nombre)     Edad aprox.:      ¿Usa mapas en el celular? sí / no
Modalidad: presencial / videollamada con control remoto
Fecha y hora:

TAREA 1 · Calcular ruta
  Tiempo: __ min __ s
  Resultado: sola / con ayuda / no lo logró
  Pista que diste (si hubo):
  Dónde se trabó:
  Frases textuales:

TAREA 2 · Reportar un problema
  Tiempo: __ min __ s
  Resultado: sola / con ayuda / no lo logró
  Pista que diste (si hubo):
  Dónde se trabó:
  Frases textuales:

PREGUNTAS FINALES
  Facilidad tarea 1 (1-5):     Facilidad tarea 2 (1-5):
  ¿Qué significaba el círculo rojo?:
  ¿Confiaría en la ruta? ¿Por qué?:
  Lo que más le confundió:
  Qué cambiaría:

Errores técnicos que viste (algo que no funcionó, mensaje raro, la página se quedó pegada):
```

## Después de las pruebas: lista de errores para T20

Vicente junta las 5 hojas y clasifica cada problema en uno de tres niveles:

| Nivel | Qué significa | Qué pasa con él |
|---|---|---|
| **1. Bloquea** | La persona no pudo terminar una tarea, o algo dejó de funcionar | Juan lo corrige sí o sí en T20 |
| **2. Confunde** | Lo logró, pero se trabó, necesitó ayuda o se demoró mucho | Se corrige si alcanza el tiempo |
| **3. Sugerencia** | Una idea para mejorar | Queda para después: el código se congela el viernes 13 a las 23:00 |

Un problema que aparece en **2 o más personas** sube de prioridad dentro de su nivel. La lista se le entrega a Juan el **viernes 13 antes de las 18:00**.

## Prueba piloto

Antes de la primera persona real, Vicente prueba esta guía completa con un compañero del equipo, idealmente el **miércoles en la noche**, apenas esté la integración. Sirve para revisar que:

- se pueda buscar o encontrar en el mapa el **CESFAM Barros Luco** y la **Cuarta Compañía de Bomberos Metropolitano Sur**;
- la ruta de la tarea 1 efectivamente rodee el paso de Departamental;
- el reporte funcione desde la página.

Si algo falla, se ajusta esta guía **antes** de las pruebas reales.
