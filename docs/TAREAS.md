# Plan hasta la entrega final (antes del lunes 16 de noviembre)

**Meta del equipo: dejar todo terminado y subido el domingo 15.** La pauta pide subir al Aula, hasta el **16 de noviembre**, el video de respaldo y el archivo de la presentación. La presentación en vivo es en clases, entre el 16 y el 30 de noviembre, en la fecha que informe el profesor. Pauta resumida y guion: [ENTREGA-FINAL.md](ENTREGA-FINAL.md).

Trabajamos igual que en el Entregable III: cada tarea es una rama, Claude no hace commits y Juan combina en `main`. Para pedirle ayuda a Claude: [TAREAS-POR-INTEGRANTE.md](TAREAS-POR-INTEGRANTE.md).

**Tres reglas nuevas, aprendidas en el Entregable III:**

1. **Chequeo diario a las 21:00 en el grupo:** cada uno escribe qué terminó y si algo lo bloquea. Toma 2 minutos.
2. **Cada tarea tiene un respaldo.** Si llega el plazo y no hay rama ni aviso, Juan le pasa la tarea al respaldo esa misma noche.
3. **El código se congela el viernes 13 a las 23:00.** Después solo se arreglan errores que impidan la demo, con el visto bueno de Juan.

## Calendario día a día

| Día | Juan | Vicente | Gonzalo | Cristóbal | Yusu | Al cerrar el día |
|---|---|---|---|---|---|---|
| **Dom 8** | Combina este plan en `main` y dirige la reunión de 20 min | Reunión; `git pull`; lee su sección | Reunión; `git pull`; lee su sección | Reunión; `git pull`; lee su sección | Reunión; `git pull`; lee su sección | Los 5 con `main` actualizado y su tarea clara |
| **Lun 9** | **T10** Modelo `Reporte` y admin (14:00); combina T10 y T11 | Empieza **T12** apenas T10 esté en `main` | **T11** Panel de reporte en la página (22:00) | Empieza **T13** con la respuesta de ejemplo de API.md | Empieza **T15** con datos de ejemplo | `Reporte` en la base de datos y panel visible en la página |
| **Mar 10** | Combina; apoya a Vicente; empieza **T16** | **T12** API de reportes y regla de 2 (20:00) | **T14** Dibujar reportes y recargar puntos (22:00) | **T13** Formulario de reporte (22:00) | Sigue **T15** | Se puede enviar un reporte desde el navegador y verlo en el mapa |
| **Mié 11** | **T16** Vencimiento y `preparar_demo` (14:00); dirige **T17** (23:00) | **T17**: prueba los escenarios y anota errores | **T17**: conecta y corrige su parte | **T17**: conecta y corrige su parte | **T15** Recálculo (14:00); **T17** | **Las 2 funcionalidades integradas en `main`** |
| **Jue 12** | **T18** dicta la sesión de traspaso (20:00); **T20** | **T19** organiza las pruebas con usuarios | **T22** diapositivas; consigue 1 usuario | **T23** guion; consigue 1 usuario | **T22** diapositivas; consigue 1 usuario | Todos entienden el proyecto completo |
| **Vie 13** | **T20** Correcciones (23:00) y **congela el código** | **T19** (18:00); **T21** diagrama ER (23:00) | **T22** primera versión (23:00); arregla lo que le toque | **T23** guion y preguntas (23:00); arregla lo que le toque | **T22** primera versión (23:00); arregla lo que le toque | **Código congelado**; diapositivas y guion en primera versión |
| **Sáb 14** | **T24** Ensayo 1 (16:00) | **T24** | **T24**; ajusta diapositivas | **T24**; ajusta guion | **T24**; **T25** video de respaldo (22:00) | Video grabado y subido; presentación ajustada |
| **Dom 15** | **T26** Ensayo 2 y simulacro de defensa (18:00); verifica T27 | **T26** | **T26** | **T26**; **T27** sube al Aula (23:00) | **T26** | **Todo subido al Aula** |
| **Lun 16** | Margen | Margen | Margen | Margen | Margen | Enlace del video probado en incógnito. Sin cambios de código |

## Dependencias

- **T12** necesita **T10**. **T13** necesita los `id` de **T11**, y **T15** necesita `DryRoute.calcularRuta` de **T13**.
- El front **no espera al backend**: usa las respuestas de ejemplo de [API.md](API.md) y se conecta a lo real en T17.

---

## Segunda funcionalidad: reporte colaborativo

### T10 · Modelo `Reporte` y admin — *Juan* (respaldo: Vicente) — lun 9, 14:00

- [ ] Modelo `Reporte` con los campos de [DECISIONES.md](DECISIONES.md) D11, y migración.
- [ ] Admin de reportes: lista con tipo, estado, fecha y punto; filtro por estado; acción **Descartar**.
- [ ] `PuntoAnegado.tipo` admite también los tipos de reporte.
- [ ] La vista `mapa` entrega la cookie CSRF (`@ensure_csrf_cookie`), necesaria para que el navegador pueda enviar reportes.

### T11 · Panel de reporte en la página — *Gonzalo* (respaldo: Yusu) — lun 9, 22:00

- [ ] En `mapa.html`, todos los `id` nuevos de [API.md](API.md#contrato-interno-del-frontend). El botón `btn-reportar` queda **fuera** de `form-ruta`, para poder reportar con una ruta en pantalla.
- [ ] Cargar `reporte.js` después de `entrada.js`, más `css/reporte.css` y `css/avisos.css` (de Cristóbal y Yusu; así cada uno es dueño de sus estilos y no se repite lo que faltó en el E3).
- [ ] En `app.css`: `[hidden] { display: none !important; }`, para que `hidden` funcione también en los formularios.

### T12 · API de reportes y regla de 2 reportes — *Vicente* (respaldo: Juan) — mar 10, 20:00

- [ ] `rutas/reportes.py` con la regla de D11, en funciones cortas que puedas explicar.
- [ ] `POST /api/reportes/` y las nuevas claves de `GET /api/puntos/`, **exactamente** como en [API.md](API.md).
- [ ] `rutas/tests.py` con estas pruebas:
  - 1 reporte **no** bloquea rutas.
  - 2 reportes de **personas distintas** a menos de 100 m activan un punto, y la ruta lo evita.
  - 2 reportes de la **misma sesión** no cuentan.
  - Un reporte cerca de un paso bajo nivel activa ese paso; no crea otro punto.
  - Tipo inválido y punto fuera de la zona devuelven 400.

### T13 · Formulario de reporte — *Cristóbal* (respaldo: Gonzalo) — mar 10, 22:00

`static/js/reporte.js` y `static/css/reporte.css`:

- [ ] **Reportar un problema** abre el formulario: oculta `form-ruta` y `resultado`, y al cerrar los deja como estaban.
- [ ] Mientras se reporta, el clic en el mapa marca el lugar y no cambia el origen ni el destino (`DryRoute.modoReporte`, respetado en `entrada.js`).
- [ ] Elegir tipo, descripción opcional y **Enviar** (habilitado solo con un lugar marcado). Envía con `X-CSRFToken`, leído de la cookie `csrftoken`.
- [ ] Muestra `mensaje` en `reporte-mensaje`, incluidos los errores 400, y llama a `DryRoute.recargarPuntos()`.
- [ ] En `entrada.js`: separar el cálculo en `DryRoute.calcularRuta()`, para que Yusu pueda recalcular.
- [ ] Nombres globales únicos en `reporte.js`: si se repite uno de otro archivo, el navegador descarta el archivo completo.

### T14 · Dibujar reportes y recargar puntos — *Gonzalo* (respaldo: Yusu) — mar 10, 22:00

`static/js/mapa.js`:

- [ ] `DryRoute.recargarPuntos()`: vuelve a pedir `/api/puntos/`, redibuja sin duplicar marcadores y llama a `DryRoute.alRecargarPuntos(datos)` si existe.
- [ ] `reportes_pendientes` en ámbar con popup "1 de 2 confirmaciones". Nunca solo color: usar también forma o ícono ([DISENO.md](DISENO.md)).
- [ ] Los anegados con `fuente = "Reportes ciudadanos"` llevan popup con el tipo y las confirmaciones.
- [ ] Leyenda actualizada.

### T15 · Confirmación y recálculo de la ruta — *Yusu* (respaldo: Cristóbal) — mié 11, 14:00

`static/js/resultado.js` y `static/css/avisos.css`. Corresponde a la pantalla 5 del prototipo:

- [ ] `DryRoute.alRecargarPuntos(datos)`: si cambiaron los anegados activos y hay una ruta en pantalla, recalcula con `DryRoute.calcularRuta()`.
- [ ] Aviso visible: *"Nuevo reporte en la zona. Ruta recalculada."*
- [ ] Revisar cada 15 segundos con `DryRoute.recargarPuntos()`, para que otra ventana vea los cambios sin recargar. **Si no alcanza, esto es lo primero que se recorta:** queda el recálculo al enviar un reporte.

### T16 · Vencimiento, descartados y `preparar_demo` — *Juan* (respaldo: Vicente) — mié 11, 14:00

- [ ] Un punto activado por reportes se desactiva cuando no le quedan reportes vigentes (vencidos a las 6 horas o descartados). No afecta a los puntos activados a mano.
- [ ] Comando `python manage.py preparar_demo`: borra reportes y puntos creados por reportes, desactiva todo y activa el paso Departamental / Gran Avenida.
- [ ] Pruebas de vencimiento y de descartar.

### T17 · Integración y limpieza — *Juan coordina, todos* — mié 11, 23:00

- [ ] Combinar todo en `main` y hacer el recorrido completo desde un clon limpio siguiendo el README.
- [ ] Quitar los datos de ejemplo de `mapa.js`: hoy, si falla `/api/puntos/`, muestra puntos falsos sin avisar. Debe mostrar un error.
- [ ] README con la segunda funcionalidad y `preparar_demo`.
- [ ] `CLAUDE.md` y [CONTEXTO.md](CONTEXTO.md) alineados con lo implementado.

## Calidad y comprensión

### T18 · Sesión de traspaso — *Juan dicta, todos* — jue 12, 20:00 (1 hora)

Pendiente desde R2, y la pauta exige que **todos** entiendan la aplicación. Se recorre una consulta completa (navegador → URL → vista → modelo → respuesta) y se revisan los archivos de `explicaciones/`.

### T19 · Pruebas con 5 usuarios — *Vicente organiza; cada uno consigue 1 persona* — vie 13, 18:00

Compromiso de R5, nunca realizado.

- [ ] Cada persona prueba dos tareas: calcular una ruta y reportar un problema.
- [ ] Anotar, sin datos personales: si lo logró, dónde se confundió y qué sugiere.
- [ ] Resumen en [ENTREGA-FINAL.md](ENTREGA-FINAL.md), con la lista de errores para T20.

### T20 · Correcciones y congelar — *Juan asigna* — vie 13, 23:00

- [ ] Solo errores y problemas de uso encontrados en T17 y T19. Nada de funciones nuevas.
- [ ] `python manage.py test rutas` en verde. **Código congelado.**

## Presentación

### T21 · Diagrama ER actualizado — *Vicente* — vie 13, 23:00

Debe reflejar lo implementado y explicar un cambio respecto del E2. Ver [ENTREGA-FINAL.md](ENTREGA-FINAL.md).

### T22 · Diapositivas — *Yusu + Gonzalo* — primera versión vie 13, 23:00; final sáb 14

Pitch de **máximo 5 diapositivas**, más las de apoyo del relato técnico. PDF o PowerPoint.

### T23 · Guion y banco de preguntas — *Cristóbal* — vie 13, 23:00

Guion de los 13 minutos, con **todos** interviniendo, y banco de preguntas por tema.

### T24 · Ensayo 1 — *todos* — sáb 14, 16:00

Cronometrado, con `preparar_demo`, en el computador y con la conexión que se usará en clases.

### T25 · Video de respaldo — *Yusu* — sáb 14, 22:00

Máximo **3 minutos**: funcionalidad corazón y reporte colaborativo. Probar el enlace en incógnito.

### T26 · Ensayo 2 y simulacro de defensa — *todos* — dom 15, 18:00

Completo, cronometrado y con 3 minutos de preguntas cruzadas. Cada integrante responde al menos una pregunta sobre una parte que **no** hizo.

### T27 · Subir al Aula — *Cristóbal; Juan verifica* — dom 15, 23:00

Enlace del video y archivo de la presentación. El lunes 16 queda solo como margen.

---

## Fuera de la entrega final

Alertas vigentes con MeteoPrecisa (F3), buses en tiempo real, despliegue público, login, notificaciones y guardar `Consulta` y `Ruta` en la base de datos.
