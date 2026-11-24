# Levantar Dry Routes en otro PC (día de la presentación)

Guía para instalar y dejar lista la demo en un computador que no es el de siempre. Se probó el 23-11 desde cero: se clonó el repo en una carpeta vacía y se siguieron estos pasos tal cual. Funcionaron todos y pasaron las 34 pruebas.

**Tiempo:** unos 10 minutos de instalación. Háganlo **al menos 30 minutos antes** de presentar.

## 0. Antes de partir

- [ ] **Internet.** El mapa, la búsqueda de direcciones, la lluvia, las fuentes y Leaflet vienen de internet. Lleven el **celular con datos para compartir (hotspot)** por si la red de la sala bloquea algo.
- [ ] **Python 3.12 o más nuevo** (probado con 3.14). Para ver la versión: `py --version` o `python --version`. Si no está, o es más antiguo, instálenlo desde [python.org](https://www.python.org/downloads/) y **marquen "Add python.exe to PATH"** en la primera pantalla del instalador.
- [ ] **Git**, para clonar. Si no está, sirve el ZIP (ver el paso 1).
- [ ] **Edge o Chrome.**
- [ ] **El video de respaldo** a mano (enlace o pendrive), por si algo falla en vivo.

## 1. Instalar (una sola vez en ese PC)

Abran **PowerShell** (tecla Windows → escribir "PowerShell") y copien de a un bloque:

```powershell
cd $HOME\Desktop
git clone https://github.com/Panconhu3vo/dry-route.git
cd dry-route
```

> **Sin Git:** en GitHub, botón verde **Code → Download ZIP**. Descomprímanlo en el Escritorio y entren a la carpeta con `cd $HOME\Desktop\dry-route-main`. Desde aquí, todo es igual.

```powershell
py -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Si `py` no se reconoce, usen `python -m venv venv`.
- Sabrán que el entorno quedó activo porque la línea de PowerShell empieza con **`(venv)`**.
- `Set-ExecutionPolicy -Scope Process` solo vale para esa ventana y no pide permisos de administrador.

```powershell
cd dry-route
python manage.py migrate
python manage.py cargar_datos
python manage.py createsuperuser
```

- `cargar_datos` debe decir: **"Listo: 185 puntos anegados y 3534 puntos de evacuación."**
- `createsuperuser` pide un usuario y una contraseña para entrar al admin (el correo se puede dejar vacío). **Anótenlos:** los necesitan en la demo.

## 2. Dejar la demo lista (cada vez, justo antes de presentar)

En la misma ventana, dentro de `dry-route\dry-route` y con `(venv)` activo:

```powershell
python manage.py preparar_demo
python manage.py actualizar_alertas
python manage.py check
```

- `preparar_demo` borra los reportes de prueba y deja anegado solo el paso Departamental / Gran Avenida. También deja **apagados** los anegamientos simulados de la USM.
- `actualizar_alertas` trae la lluvia real de Open-Meteo, así la franja del panel dice *"Sin alertas de lluvia en la zona · actualizado HH:MM"*. (En el paso 3 se deja repitiéndose sola hasta que empiece la demo.)
- `check` debe decir **"System check identified no issues"**.
- *(Opcional, 20 segundos)* `python manage.py test rutas` debe terminar en **"OK"**.

## 3. Levantar la app

**Terminal 1, el servidor:**

```powershell
python manage.py runserver
```

Déjenla abierta mientras dure la presentación. Se cierra con `Ctrl + C`.

**Terminal 2, la lluvia.** Abran otra ventana de PowerShell, activen el entorno y dejen la lluvia real actualizándose mientras esperan su turno:

```powershell
cd $HOME\Desktop\dry-route\dry-route
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
..\venv\Scripts\Activate.ps1
python manage.py actualizar_alertas --cada 10
```

> **Cuando empiece la presentación, detengan esa terminal con `Ctrl + C`.** Si sigue corriendo, cada 10 minutos trae la lluvia real (0 mm/h) y **apagaría la lluvia simulada** en medio de la demo. Los datos de lluvia valen 30 minutos, así que la franja sigue al día durante los 13 minutos de la presentación. Usen esa misma terminal para el paso de lluvia del guion (sección 5).

## 4. Abrir el navegador

| Qué | Dónde |
|---|---|
| La app (persona 1) | http://127.0.0.1:8000 |
| La app (persona 2, para confirmar el reporte) | una **ventana de incógnito** (`Ctrl + Shift + N`) con la misma dirección |
| El admin | http://127.0.0.1:8000/admin/, con el usuario del paso 1 |

**Calienten la app:** calculen **una ruta cualquiera** antes de empezar. La primera tarda 2 segundos porque carga el mapa de calles en memoria; las siguientes son instantáneas. Después presionen **Nueva ruta**.

## 5. Durante la demo

El guion completo, minuto a minuto, está en [ENTREGA-FINAL.md](ENTREGA-FINAL.md#guion-de-la-demo-4-minutos). Comandos que se usan en vivo:

| Momento | Dónde | Qué hacer |
|---|---|---|
| Anegar la universidad | admin → **Puntos anegados** | Marcar "anegado ahora" en *Anegamiento simulado: USM campus San Joaquín* y **Guardar** |
| Lluvia simulada (paso opcional) | Terminal 2 | `python manage.py actualizar_alertas --simular 10 --cerca -33.4911,-70.6190` |
| Terminar la lluvia | Terminal 2 | `python manage.py actualizar_alertas --simular 0` |
| Persistencia | Terminal 1 | `Ctrl + C`, después `python manage.py runserver` y recargar el navegador |

- **Anegar la universidad:** en hasta 15 segundos, el mapa avisa "Ruta recalculada".
- **Lluvia simulada:** en hasta 15 segundos se encienden los 2 pasos de Vicuña Mackenna y se recalcula la ruta. En hasta 1 minuto, la franja se pone roja.

**Para volver a empezar la demo** (por ejemplo, en un ensayo): `Ctrl + C` en la terminal 1, `python manage.py preparar_demo`, `python manage.py actualizar_alertas` y `python manage.py runserver`.

## 6. Si algo falla

| Lo que pasa | Qué hacer |
|---|---|
| `py` o `python` "no se reconoce" | Instalar Python desde python.org marcando **"Add python.exe to PATH"**, cerrar PowerShell y abrirlo de nuevo |
| "...la ejecución de scripts está deshabilitada" al activar | Correr `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` en esa ventana. **O** no activar y usar `..\venv\Scripts\python.exe manage.py ...` en vez de `python manage.py ...` |
| `pip install` falla porque Django pide otra versión de Python | El Python es muy antiguo: instalar 3.14 y repetir desde `py -m venv venv` |
| "That port is already in use" | `python manage.py runserver 8001` y abrir http://127.0.0.1:8001 |
| "no such table" u "OperationalError" | Faltó `python manage.py migrate` |
| "No pudimos cargar los puntos anegados" | El servidor no está corriendo (terminal 1), o faltó `python manage.py cargar_datos` |
| El mapa sale gris, sin calles, o la página sin estilos | No hay internet o la red bloquea OpenStreetMap: conectarse al **hotspot** del celular |
| La franja dice "Datos de lluvia no disponibles" | Pasaron más de 30 minutos sin actualizar: correr `python manage.py actualizar_alertas` (en hasta 1 minuto se corrige sola). Sin internet: `python manage.py actualizar_alertas --simular 0` |
| El segundo reporte no confirma el lugar | Tiene que hacerlo **otra sesión**: la ventana de incógnito, no la misma ventana |
| Olvidaron la contraseña del admin | `python manage.py changepassword <usuario>` |
| Quedaron reportes o puntos de un ensayo | `python manage.py preparar_demo` (con el servidor detenido o no, da igual) |
| Algo no responde y no hay tiempo | Mostrar el **video de respaldo** y explicar qué pasó |

## 7. Al terminar

`Ctrl + C` en las dos terminales. Si el PC es prestado, pueden borrar la carpeta `dry-route` del Escritorio.
