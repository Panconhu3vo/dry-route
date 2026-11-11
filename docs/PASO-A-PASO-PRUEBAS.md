# Prueba con usuarios (T19): paso a paso

Versión corta para tener abierta durante la prueba. El detalle (modalidad, reglas, hoja de anotación y
clasificación de errores) está en [PRUEBAS-USUARIOS.md](PRUEBAS-USUARIOS.md).

**Durante la prueba no hay que escribirle nada a Claude:** quien usa la página es la persona invitada.
Claude solo ayuda **antes**, a dejar la página encendida.

---

## ANTES de que llegue la persona (10 min)

### 1. Encender la página

**Opción fácil:** abre Claude Code en el proyecto y escribe:

> Soy *Tu Nombre*, voy a hacer la prueba de usuarios de T19. Actualiza main, enciende la página y deja el escenario de demo listo.

**Opción manual:** en la terminal de VS Code, desde la carpeta del proyecto:

```powershell
git checkout main
git pull
venv\Scripts\Activate.ps1
cd dry-route
python manage.py migrate
python manage.py preparar_demo
python manage.py runserver
```

> Si `preparar_demo` da error porque todavía no existe (es la tarea T16 de Juan), sáltalo y haz el paso 2.

### 2. Dejar el escenario (solo si no usaste `preparar_demo`)

Entra a http://127.0.0.1:8000/admin/ y:

- Borra todos los **Reportes**.
- En **Puntos anegados**, borra los que digan "Reporte ciudadano".
- Deja marcado como activo **solo** el paso *Avenida Departamental / Gran Avenida*.

### 3. Abrir la página para la persona

Abre **una ventana de incógnito** (`Ctrl + Shift + N`), entra a http://127.0.0.1:8000 y déjala a pantalla
completa. Ten listo el cronómetro del celular.

> **Antes de cada persona nueva, repite el paso 2** (o `preparar_demo`). Si no, su reporte se mezcla con el
> de la persona anterior y lo confirmaría.

---

## DURANTE la prueba (15 min)

### 4. Léele esto a la persona

> "Gracias por ayudarnos. Estamos probando una página, no a ti: si algo no te resulta, es culpa de la página.
> Te voy a pedir dos cosas. Mientras las haces, di en voz alta lo que piensas. No te voy a ayudar, porque
> necesito ver si la página se entiende sola. Si quieres rendirte, di 'me rindo'. No anoto tu nombre."

### 5. Tarea 1: calcular una ruta

Léela y parte el cronómetro:

> "Está lloviendo muy fuerte. Estás en el **CESFAM Barros Luco** y necesitas llegar a la **Cuarta Compañía
> de Bomberos Metropolitano Sur**. Usa la página para saber por dónde ir de forma segura."

- **Termina cuando:** aparece la ruta en el mapa.
- **Máximo:** 5 minutos.

### 6. Tarea 2: reportar un problema

Léela y parte el cronómetro:

> "Ahora imagina que, cerca del CESFAM Barros Luco, ves una calle con tanta agua que no se puede pasar.
> Usa la página para avisarles a otras personas."

- **Termina cuando:** aparece "Reporte recibido…".
- **Máximo:** 5 minutos.

### Reglas mientras observas

- No ayudes, no señales la pantalla y no digas "casi".
- Si te pregunta algo, responde: *"¿Qué crees tú que pasaría?"*
- Si lleva **más de 1 minuto trabada**, dale **una** pista corta y anótala como "con ayuda".
- Anota las frases textuales que diga (por ejemplo, "no sé dónde apretar").

### 7. Preguntas finales

1. Del 1 (muy difícil) al 5 (muy fácil), ¿qué tan fácil fue la tarea 1? ¿Y la 2?
2. ¿Qué crees que significaba el círculo rojo?
3. ¿Confiarías en esta ruta en una emergencia real? ¿Por qué?
4. ¿Qué te confundió más?
5. ¿Qué cambiarías?

---

## DESPUÉS de la prueba

### 8. Enviar la hoja de anotación

Llena la [hoja de anotación](PRUEBAS-USUARIOS.md#hoja-de-anotación-una-por-persona) **apenas termines** y envíala:

- a **Vicente**, que arma la lista de errores para Juan (T20);
- a **Cristóbal**, que llena la tabla de resultados en ENTREGA-FINAL.md.

**Plazo:** ojalá el **jueves 12**; como máximo, el viernes 13 antes de las 12:00.
