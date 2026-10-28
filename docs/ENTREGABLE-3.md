# Entregable III — Implementación (10%)

**Entrega: viernes 30 de octubre de 2026, 23:55.** Régimen: equipo.
Pauta original: `.claude/context-docs/Entregable III Implementacion.docx`.

## Qué exige la pauta

Desde el navegador, una persona usuaria debe poder:

1. **Ingresar o seleccionar** la información → origen y destino (búsqueda, GPS o clic).
2. **Ejecutar el procesamiento** en la aplicación → `/api/ruta/` calcula la ruta con NetworkX evitando los anegados activos.
3. **Observar el resultado** en la interfaz → ruta dibujada y tarjeta con distancia, tiempo y puntos evitados (o el punto de evacuación).

- Debe ejecutarse en **localhost**. Se permiten **datos precargados** y una interfaz sencilla.
- **No se exige:** persistencia, API pública, autenticación, despliegue ni una interfaz terminada.
- **No sirve:** código Python suelto, pantallas estáticas o componentes que no estén integrados en la web.
- El repo debe tener un **README** con dependencias, pasos para iniciar Django y datos para probar.

## Checklist de entrega

- [ ] La funcionalidad corazón funciona de punta a punta en localhost.
- [ ] Los 2 casos de prueba se ejecutaron y su resultado observado quedó anotado.
- [ ] El video dura 5 minutos o menos, y su enlace se probó en una ventana de incógnito.
- [ ] El documento está completo, **sin las instrucciones de la pauta** y con los títulos intactos.
- [ ] El README permite que alguien externo ejecute la app desde cero.
- [ ] Están los enlaces del repositorio y del video.

## Componentes (tabla del documento)

| Componente | Estado | Qué funciona y qué falta |
|---|---|---|
| Entrada de información | *completar en T7* | Búsqueda de direcciones (Nominatim), GPS y clic en el mapa. |
| Procesamiento | *completar en T7* | Grafo OSM y NetworkX con bloqueo de 100 m alrededor de los anegados activos. |
| Presentación del resultado | *completar en T7* | Ruta dibujada y tarjeta; caso sin ruta con punto de evacuación. |

## Casos de prueba

Las coordenadas exactas se fijan cuando T1 genera los datos (Vicente y Juan las anotan aquí). Ambos casos quedan también como pruebas automáticas en `rutas/tests.py`.

| Elemento | Caso 1 · Escenario principal: ruta segura | Caso 2 · Alternativo: sin ruta segura |
|---|---|---|
| Condición previa (admin) | Activo: paso bajo nivel **Gran Avenida / Departamental** | Activo: paso bajo nivel en la zona de **Lo Espejo** |
| Datos de entrada | Origen: Gran Avenida al norte de Departamental (`__, __`). Destino: Gran Avenida al sur (`__, __`). | Origen: `__, __`. Destino: a menos de 100 m del paso activo (`__, __`). |
| Resultado esperado | `estado = "segura"`; la ruta **no pasa** a menos de 100 m del paso activo (toma una calle paralela); "Evita 1 punto anegado". | `estado = "sin_ruta"`; mensaje "No hay ruta segura a tu destino"; ruta al punto de evacuación más cercano, resaltado. |
| Resultado observado | *completar en T7* | *completar en T7* |
| ¿Coinciden? | | |

Ambos casos salen del diagrama de flujo del E2: la rama "Sí" y la rama "No" de *¿Existe una ruta de evacuación segura al destino?*

## Guion del video (5 min)

| Tiempo | Qué se muestra | Quién habla |
|---|---|---|
| 0:00 – 0:30 | Problema en una frase y qué hace Dry Routes. | *definir* |
| 0:30 – 1:00 | Terminal con `runserver`; en el admin se marca el anegado activo (escenario simulado). | |
| 1:00 – 2:15 | **Caso 1** en el navegador: entrada → clic en Calcular → ruta que esquiva el paso. | |
| 2:15 – 3:15 | **Caso 2**: destino junto a un paso anegado → sin ruta → punto de evacuación. | |
| 3:15 – 4:30 | **Código:** `calcular_ruta` en `rutas/ruteo.py` (15 a 30 líneas). Qué hace, la decisión técnica (bloquear nodos a menos de 100 m y Dijkstra con NetworkX, en vez de Google, que no permite evitar puntos; ver DECISIONES D2 y D5) y cómo se usó la IA para entenderlo y verificarlo. | Juan o Vicente |
| 4:30 – 5:00 | Qué falta y los próximos pasos (F2 o F3). | |

Si algo falla durante la grabación, la pauta pide **mostrar el comportamiento y explicarlo**, no ocultarlo.

## Uso de IA (para el video y el documento)

La pauta pide explicar cómo usaron Copilot u otra IA para **comprender, verificar o mejorar** el código, y qué hicieron si la IA agregó algo que no habían pedido.
Que cada integrante anote aquí **una** situación concreta mientras trabaja (con 2 líneas basta):

| Integrante | Qué le pedimos a la IA | Qué aceptamos, cambiamos o rechazamos y por qué |
|---|---|---|
| Juan | | |
| Vicente | | |
| Gonzalo | | |
| Cristóbal | | |
| Yusu | | |

## Cambios respecto del Entregable II (para el documento)

- Los roles cambiaron: el ruteo pasa de Gonzalo a Juan y Vicente; Gonzalo pasa al frontend.
- Los puntos anegados se extraen de OSM (pasos bajo nivel) en vez del catastro CONDOR, porque CONDOR no está disponible para descarga (R6).
- Se agrega la entidad `PuntoEvacuacion`, necesaria para el caso sin ruta.
- `Consulta`, `Ruta` y `Vía` no se guardan en la base de datos en la v1 (se calculan en cada petición).
- F2 y F3 se postergan (R1). El recálculo durante el trayecto (pantalla 5) también.

## Riesgos para la sección "Plan de trabajo y riesgos"

Candidatos para los "dos que requieren mayor atención": **R1** (plazo; sigue siendo crítico) y **R2** (conocimiento de Django). Como alternativa a R2 se puede usar **R5** (validez de la ruta), si para entonces el ruteo ya funciona.
