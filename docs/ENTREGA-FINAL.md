# Entrega final — Presentación (20%)

Pauta original: `.claude/context-docs/Entregable Final (Presentacion).docx`.

- **Hasta el 16 de noviembre, en el Aula:** enlace a un **video de respaldo de máximo 3 minutos** (funcionalidad corazón y segunda funcionalidad) y el **archivo de la presentación** (PDF o PowerPoint).
- **Presentación en vivo:** en clases, entre el 16 y el 30 de noviembre, en el orden que informe el profesor.
- **Basta con localhost:** no es obligatorio publicar la app en internet.

## Qué exige la pauta y cómo lo cumplimos

| La pauta pide | Cómo lo mostramos |
|---|---|
| Funcionalidad corazón | Ruta de evacuación segura |
| Segunda funcionalidad integrada | Reporte colaborativo, que modifica las rutas |
| Flujo completo de usuario | Marcar origen y destino → ruta → reportar → ruta recalculada |
| Persistencia observable | Los reportes aparecen en el admin y **siguen ahí después de reiniciar el servidor** |
| Participación de todos | Cada integrante interviene (ver la tabla siguiente) |
| Explicar lo hecho con IA | Archivos de `explicaciones/` y tabla "Uso de IA" |

## Los 13 minutos

Reparto propuesto; el equipo lo confirma en T23.

| Bloque | Tiempo | Contenido | Quién |
|---|---|---|---|
| Pitch (máx. 5 diapositivas) | 2:00 | Problema y afectados, evidencia, solución y funcionalidad corazón, aporte frente a Waze y SENAPRED | Cristóbal |
| Demo: funcionalidad corazón | 1:50 | Ruta segura y caso sin ruta | Gonzalo |
| Demo: reporte y persistencia | 2:10 | Reporte, confirmación, recálculo, admin y reinicio | Yusu |
| Diagrama ER | 1:30 | ER actualizado, relación con la app y un cambio justificado | Vicente |
| Caso de prueba | 1:00 | Esperado, observado, conclusión o mejora | Juan |
| Dificultad significativa | 1:30 | Qué pasó, qué decidió el equipo y qué aprendió | Juan |
| Preguntas y defensa | 3:00 | Todos deben poder responder | Todos |

## Guion de la demo (4 minutos)

**Antes de empezar:** `python manage.py preparar_demo`, servidor corriendo, una ventana normal y una **ventana de incógnito** abiertas, y el admin con sesión iniciada en otra pestaña.

| Tiempo | Acción | Qué debe verse |
|---|---|---|
| 0:00 | Presentar el mapa y la leyenda | Círculo rojo en Departamental / Gran Avenida |
| 0:20 | Marcar origen y destino a ambos lados del paso; **Calcular ruta** | Ruta que lo rodea y "Evita 1 punto anegado" |
| 1:20 | **Nueva ruta** con destino dentro del círculo rojo | "No hay ruta segura" y ruta al punto de evacuación |
| 1:50 | Calcular una ruta y, en la ventana normal, reportar una calle anegada sobre ella | Marcador ámbar "1 de 2". **La ruta no cambia** |
| 2:20 | En la ventana de incógnito (otra persona), reportar el mismo lugar | Queda confirmado. La primera ventana avisa "Ruta recalculada" |
| 3:00 | Abrir el admin; luego `Ctrl + C`, `runserver` y recargar | Los 2 reportes guardados y el punto sigue en el mapa |
| 3:40 | Cierre: qué recibe la persona usuaria | Ruta segura y aviso "referencial" |

**Si falla algo en vivo:** mostrar el video de respaldo y explicar qué ocurrió. Probar internet antes, porque el mapa y la búsqueda de direcciones lo necesitan.

## Relato técnico (propuesta)

**Diagrama ER actualizado (T21).** Cambios respecto del E2:

- Se agrega `PuntoEvacuacion`, necesario para el caso sin ruta.
- `Reporte` actualiza a `PuntoAnegado`, como en el E2, y ahora **dos reportes de personas distintas lo activan**.
- `Vía` son las aristas de `grafo.json`, y `Consulta` y `Ruta` se calculan en cada petición. **No se guardan** porque la app se usa sin registro y lo que debe persistir son los reportes (DECISIONES D12).
- `Alerta` no se implementó (F3 diferida).

**Caso de prueba.** Caso 1 del Entregable III:

- *Esperado:* ningún tramo de la ruta pasa a menos de 100 m del paso anegado.
- *Observado la primera vez:* la prueba falló y la ruta cruzaba el túnel.
- *Conclusión y mejora:* el túnel mide unos 300 m y sus esquinas quedan lejos del punto, así que se pasó de bloquear esquinas a bloquear **tramos de calle**.

**Dificultad significativa.** No existía una fuente de datos en tiempo real sobre calles anegadas: CONDOR no tiene descarga y no tenemos sensores. El equipo decidió usar los pasos bajo nivel de OpenStreetMap como puntos de riesgo y sumar reportes ciudadanos confirmados por dos personas. *Aprendizaje:* verificar temprano que los datos existen.

## Video de respaldo (máximo 3 minutos)

Mismo recorrido de la demo, sin pausas: ruta segura (45 s), caso sin ruta (30 s), reporte y confirmación con recálculo (1:15), persistencia en el admin (30 s).

## Banco de preguntas (punto de partida para T23)

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué no usar Google Maps? | Su API de rutas no permite evitar puntos arbitrarios |
| ¿Qué algoritmo calcula la ruta? | Dijkstra con NetworkX, sobre el grafo de calles de OpenStreetMap, sin los tramos bloqueados |
| ¿Por qué 100 metros? | Margen alrededor del punto anegado (D5); es un parámetro ajustable y no un valor medido |
| ¿De dónde salen los puntos anegados? | Pasos bajo nivel de OSM, activados en el admin (simulación) o por dos reportes ciudadanos |
| ¿Por qué se piden dos reportes? | Para reducir reportes falsos sin obligar a crear una cuenta |
| ¿Se puede engañar al sistema? | Sí: abriendo otra sesión. Por eso se muestra "ruta referencial", los reportes vencen a las 6 horas y un admin puede descartarlos |
| ¿Qué datos se guardan? | Reportes (tipo, lugar, fecha) y puntos. No se guardan cuentas ni consultas |
| ¿Qué pasa si estoy dentro de la zona anegada? | Se ignora el destino y se guía al punto de evacuación seguro más cercano, con la salida que pasa por menos agua |
| ¿Cómo verificaron que funciona? | Pruebas automáticas, pruebas con 5 usuarios y escenarios simulados |
| ¿Cómo usaron la IA y cómo validaron lo que entregó? | Con Claude Code, trabajando por tareas; cada integrante revisa, prueba y documenta su parte en `explicaciones/` |

## Resultados de las pruebas con usuarios (T19)

| Persona | Calculó una ruta | Reportó un problema | Dónde se confundió | Sugerencia |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

## Uso de IA (para la defensa)

Cada integrante anota una situación concreta, en 2 líneas. Sale de la sección "Uso de IA" de su archivo de explicación.

| Integrante | Qué le pedimos a la IA | Qué aceptamos, cambiamos o rechazamos, y cómo lo verificamos |
|---|---|---|
| Juan | | |
| Vicente | | |
| Gonzalo | | |
| Cristóbal | | |
| Yusu | | |

## Checklist final

- [ ] Las dos funcionalidades funcionan de punta a punta en localhost.
- [ ] `python manage.py test rutas` pasa completo.
- [ ] El README permite ejecutar la app desde cero.
- [ ] Pitch de máximo 5 diapositivas.
- [ ] Video de 3 minutos o menos, con el enlace probado en incógnito.
- [ ] Video y presentación subidos al Aula.
- [ ] Ensayo cronometrado en 13 minutos o menos.
- [ ] Cada integrante puede explicar la app completa en términos generales.
