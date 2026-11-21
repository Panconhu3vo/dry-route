import json
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from .alertas import actualizar_puntos
from .models import Alerta, PuntoAnegado, Reporte
from .reportes import HORAS_VIGENCIA_REPORTE
from .ruteo import RADIO_BLOQUEO_M, ZONA, distancia_a_tramo_m, distancia_m

# Los dos casos de prueba del Entregable III (docs/ENTREGABLE-3.md)
PASO_DEPARTAMENTAL = "way/451437804"  # Paso bajo nivel Avenida Departamental / Gran Avenida
PASO_CERRO_NEGRO = "way/39259025"     # Paso bajo nivel Cerro Negro / Avenida Américo Vespucio
# 0,1 grados (~11 km) al norte del borde de la zona: queda afuera aunque la zona cambie (T28)
FUERA_DE_LA_ZONA = f"{ZONA['norte'] + 0.1},{ZONA['oeste']}"


class CasosDePrueba(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos", verbosity=0)

    def activar(self, osm_id):
        punto = PuntoAnegado.objects.get(osm_id=osm_id)
        punto.activo = True
        punto.save()
        return punto

    def pedir_ruta(self, origen, destino):
        return self.client.get("/api/ruta/", {"origen": origen, "destino": destino})

    def test_caso_1_ruta_segura_esquiva_el_paso_anegado(self):
        paso = self.activar(PASO_DEPARTAMENTAL)
        # Por Avenida Departamental, de oeste a este: el camino directo pasa por el paso bajo nivel
        respuesta = self.pedir_ruta("-33.502460,-70.658334", "-33.505348,-70.647249").json()

        self.assertEqual(respuesta["estado"], "segura")
        self.assertEqual([p["nombre"] for p in respuesta["puntos_evitados"]], [paso.nombre])
        # Ningún tramo de la ruta pasa a menos de 100 m del paso (se revisan tramos, no solo esquinas)
        ruta = respuesta["ruta"]
        for (lat_a, lon_a), (lat_b, lon_b) in zip(ruta, ruta[1:]):
            tramo = distancia_a_tramo_m(paso, {"lat": lat_a, "lon": lon_a}, {"lat": lat_b, "lon": lon_b})
            self.assertGreaterEqual(tramo, RADIO_BLOQUEO_M)

    def test_caso_2_sin_ruta_segura_guia_al_punto_de_evacuacion(self):
        paso = self.activar(PASO_CERRO_NEGRO)
        # El destino está justo en el paso anegado: no se puede llegar de forma segura
        respuesta = self.pedir_ruta("-33.525000,-70.650000", f"{paso.lat},{paso.lon}").json()

        self.assertEqual(respuesta["estado"], "sin_ruta")
        self.assertIsNotNone(respuesta["punto_evacuacion"])
        self.assertGreater(len(respuesta["ruta"]), 1)

    def test_origen_en_zona_anegada_guia_al_punto_de_evacuacion_seguro(self):
        paso = self.activar(PASO_DEPARTAMENTAL)
        # El usuario está parado en el paso anegado: aunque pida ir lejos, primero hay que salir
        respuesta = self.pedir_ruta(f"{paso.lat},{paso.lon}", "-33.505348,-70.647249").json()

        self.assertEqual(respuesta["estado"], "en_peligro")
        self.assertGreater(len(respuesta["ruta"]), 1)
        evacuacion = respuesta["punto_evacuacion"]
        # El punto elegido nunca está dentro de la zona anegada
        self.assertGreaterEqual(distancia_m(evacuacion["lat"], evacuacion["lon"], paso.lat, paso.lon), RADIO_BLOQUEO_M)

    def test_sin_anegados_la_ruta_es_segura_y_no_evita_nada(self):
        respuesta = self.pedir_ruta("-33.502460,-70.658334", "-33.505348,-70.647249").json()
        self.assertEqual(respuesta["estado"], "segura")
        self.assertEqual(respuesta["puntos_evitados"], [])

    def test_error_si_falta_un_parametro(self):
        respuesta = self.client.get("/api/ruta/", {"origen": "-33.5,-70.65"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "parametros_invalidos")

    def test_error_si_el_punto_esta_fuera_de_la_zona(self):
        respuesta = self.pedir_ruta(FUERA_DE_LA_ZONA, "-33.505348,-70.647249")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "fuera_de_zona")

    def test_la_pagina_trae_la_zona_para_encuadrar_el_mapa(self):
        # mapa.js lee la zona de aquí (json_script), sin datos de ejemplo
        respuesta = self.client.get("/")
        self.assertContains(respuesta, 'id="zona-datos"')
        self.assertContains(respuesta, f'"norte": {ZONA["norte"]}')

    def test_api_puntos_entrega_zona_y_puntos(self):
        datos = self.client.get("/api/puntos/").json()
        self.assertEqual(len(datos["anegados"]), PuntoAnegado.objects.count())
        self.assertGreater(len(datos["evacuacion"]), 0)
        self.assertIn("norte", datos["zona"])
        self.assertEqual(datos["anegados"][0]["fuente"], "OpenStreetMap")
        self.assertEqual(datos["anegados"][0]["confirmaciones"], 0)
        self.assertEqual(datos["reportes_pendientes"], [])


# Ruta de prueba por Avenida Departamental, y un lugar en medio de ella, lejos de los pasos bajo nivel
ORIGEN = "-33.502460,-70.658334"
DESTINO = "-33.505348,-70.647249"
LUGAR_EN_LA_RUTA = (-33.504476, -70.651095)
LUGAR_A_25_M = (-33.504700, -70.651095)  # otra persona reporta casi en el mismo lugar


class ReporteColaborativo(TestCase):
    """Regla de los 2 reportes de personas distintas (DECISIONES D11)."""

    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos", verbosity=0)

    def reportar(self, cliente, lugar, tipo="anegamiento"):
        # Cada Client es un navegador distinto, con su propia sesión: es decir, otra persona
        return cliente.post("/api/reportes/", {"tipo": tipo, "lat": lugar[0], "lon": lugar[1]},
                            content_type="application/json")

    def pedir_ruta(self):
        return self.client.get("/api/ruta/", {"origen": ORIGEN, "destino": DESTINO}).json()

    def test_un_reporte_no_bloquea_rutas(self):
        respuesta = self.reportar(self.client, LUGAR_EN_LA_RUTA)

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["estado"], "pendiente")
        self.assertIsNone(respuesta.json()["punto_id"])
        self.assertFalse(PuntoAnegado.objects.filter(activo=True).exists())
        self.assertEqual(self.pedir_ruta()["puntos_evitados"], [])
        # Aparece en el mapa como pendiente, esperando a otra persona
        pendientes = self.client.get("/api/puntos/").json()["reportes_pendientes"]
        self.assertEqual([(p["confirmaciones"], p["requeridas"]) for p in pendientes], [(1, 2)])

    def test_dos_personas_activan_un_punto_y_la_ruta_lo_evita(self):
        self.reportar(Client(), LUGAR_EN_LA_RUTA)
        respuesta = self.reportar(Client(), LUGAR_A_25_M).json()

        self.assertEqual(respuesta["estado"], "confirmado")
        self.assertEqual(respuesta["confirmaciones"], 2)
        punto = PuntoAnegado.objects.get(id=respuesta["punto_id"])
        self.assertTrue(punto.activo)
        self.assertEqual(punto.fuente, "Reportes ciudadanos")
        # Los dos reportes quedan confirmados y unidos al mismo punto
        self.assertEqual(punto.reportes.filter(estado_verificacion="confirmado").count(), 2)

        ruta = self.pedir_ruta()
        self.assertEqual(ruta["estado"], "segura")
        self.assertEqual([p["id"] for p in ruta["puntos_evitados"]], [punto.id])

    def test_dos_reportes_de_la_misma_persona_no_cuentan(self):
        self.reportar(self.client, LUGAR_EN_LA_RUTA)
        respuesta = self.reportar(self.client, LUGAR_A_25_M)

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "ya_reportado")
        self.assertFalse(PuntoAnegado.objects.filter(activo=True).exists())
        self.assertEqual(Reporte.objects.count(), 1)

    def test_reporte_cerca_de_un_paso_bajo_nivel_activa_ese_paso(self):
        paso = PuntoAnegado.objects.get(osm_id=PASO_DEPARTAMENTAL)
        puntos_antes = PuntoAnegado.objects.count()
        self.reportar(Client(), (paso.lat + 0.0003, paso.lon))  # unos 30 m al norte del paso
        respuesta = self.reportar(Client(), (paso.lat, paso.lon + 0.0003)).json()

        self.assertEqual(respuesta["punto_id"], paso.id)
        paso.refresh_from_db()
        self.assertTrue(paso.activo)
        self.assertEqual(PuntoAnegado.objects.count(), puntos_antes)  # no se creó un punto repetido

    def test_tipo_invalido_devuelve_400(self):
        respuesta = self.reportar(self.client, LUGAR_EN_LA_RUTA, tipo="incendio")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "tipo_invalido")

    def test_punto_fuera_de_la_zona_devuelve_400(self):
        respuesta = self.reportar(self.client, [float(x) for x in FUERA_DE_LA_ZONA.split(",")])
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "fuera_de_zona")

    def test_faltan_datos_devuelve_400(self):
        respuesta = self.client.post("/api/reportes/", {"tipo": "anegamiento"}, content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "parametros_invalidos")


class VencimientoYDemo(TestCase):
    """T16: los puntos que encendieron los reportes se apagan solos; lo encendido a mano no (DECISIONES D11)."""

    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos", verbosity=0)

    def confirmar_lugar(self, lugar=LUGAR_EN_LA_RUTA, lugar_2=LUGAR_A_25_M):
        """Dos personas distintas reportan el mismo lugar. Devuelve el punto que se encendió."""
        for sitio in (lugar, lugar_2):
            respuesta = Client().post("/api/reportes/", {"tipo": "anegamiento", "lat": sitio[0], "lon": sitio[1]},
                                      content_type="application/json")
        return PuntoAnegado.objects.get(id=respuesta.json()["punto_id"])

    def activo_segun_api(self, punto):
        anegados = self.client.get("/api/puntos/").json()["anegados"]
        return next(p["activo"] for p in anegados if p["id"] == punto.id)

    def envejecer(self, reportes):
        reportes.update(fecha_hora=timezone.now() - timedelta(hours=HORAS_VIGENCIA_REPORTE + 1))

    def entrar_al_admin(self):
        self.client.force_login(get_user_model().objects.create_superuser("admin", "admin@example.com", "x"))

    def test_el_punto_se_apaga_cuando_vencen_sus_reportes(self):
        punto = self.confirmar_lugar()
        self.assertTrue(self.activo_segun_api(punto))

        self.envejecer(punto.reportes.all())

        self.assertFalse(self.activo_segun_api(punto))
        ruta = self.client.get("/api/ruta/", {"origen": ORIGEN, "destino": DESTINO}).json()
        self.assertEqual(ruta["puntos_evitados"], [])

    def test_descartar_los_dos_reportes_en_el_admin_apaga_el_punto_altiro(self):
        punto = self.confirmar_lugar()
        self.entrar_al_admin()

        ids = list(punto.reportes.values_list("id", flat=True))
        self.client.post("/admin/rutas/reporte/", {"action": "descartar", "_selected_action": ids})

        punto.refresh_from_db()
        self.assertFalse(punto.activo)

    def test_con_un_reporte_vigente_el_punto_sigue_encendido(self):
        punto = self.confirmar_lugar()
        Reporte.objects.filter(id=punto.reportes.first().id).update(estado_verificacion="descartado")

        self.assertTrue(self.activo_segun_api(punto))

    def test_un_punto_encendido_a_mano_no_vence(self):
        paso = PuntoAnegado.objects.get(osm_id=PASO_DEPARTAMENTAL)
        paso.activo = True
        paso.save()
        # Dos personas lo reportan y sus reportes quedan unidos al paso...
        self.confirmar_lugar((paso.lat + 0.0003, paso.lon), (paso.lat, paso.lon + 0.0003))
        self.envejecer(paso.reportes.all())

        # ...pero al vencer no lo apagan, porque lo encendió una persona en el admin
        self.assertTrue(self.activo_segun_api(paso))

    def test_cambiar_anegado_ahora_a_mano_quita_la_marca_de_reportes(self):
        punto = self.confirmar_lugar()
        self.assertTrue(punto.activado_por_reportes)
        self.entrar_al_admin()

        # Formulario del admin sin la casilla "anegado ahora": la persona lo apaga a mano
        self.client.post(f"/admin/rutas/puntoanegado/{punto.id}/change/", {
            "osm_id": punto.osm_id, "nombre": punto.nombre, "tipo": punto.tipo,
            "lat": punto.lat, "lon": punto.lon, "fuente": punto.fuente,
        })

        punto.refresh_from_db()
        self.assertFalse(punto.activo)
        self.assertFalse(punto.activado_por_reportes)

    def test_preparar_demo_deja_solo_el_paso_departamental_anegado(self):
        self.confirmar_lugar()  # crea un punto a partir de reportes
        PuntoAnegado.objects.filter(osm_id=PASO_CERRO_NEGRO).update(activo=True)

        call_command("preparar_demo", stdout=StringIO())

        self.assertEqual(Reporte.objects.count(), 0)
        self.assertFalse(PuntoAnegado.objects.filter(fuente="Reportes ciudadanos").exists())
        activos = list(PuntoAnegado.objects.filter(activo=True).values_list("osm_id", flat=True))
        self.assertEqual(activos, [PASO_DEPARTAMENTAL])
        # Los anegamientos simulados de la universidad quedan creados, pero apagados
        simulados = PuntoAnegado.objects.filter(osm_id__startswith="simulacion/usm-")
        self.assertEqual(simulados.count(), 2)
        self.assertFalse(simulados.filter(activo=True).exists())

    def test_anegar_la_universidad_convierte_la_ruta_en_una_ruta_de_escape(self):
        call_command("preparar_demo", stdout=StringIO())
        campus = "-33.491080,-70.619010"  # campus San Joaquín
        destino = "-33.475000,-70.622000"
        antes = self.client.get("/api/ruta/", {"origen": campus, "destino": destino}).json()

        # En la demo esto se hace en el admin: marcar "anegado ahora" y guardar
        PuntoAnegado.objects.filter(osm_id="simulacion/usm-san-joaquin").update(activo=True)
        despues = self.client.get("/api/ruta/", {"origen": campus, "destino": destino}).json()

        self.assertEqual(antes["estado"], "segura")
        self.assertEqual(despues["estado"], "en_peligro")
        self.assertIsNotNone(despues["punto_evacuacion"])

    def test_preparar_demo_se_puede_correr_varias_veces(self):
        call_command("preparar_demo", stdout=StringIO())
        call_command("preparar_demo", stdout=StringIO())
        self.assertEqual(PuntoAnegado.objects.filter(osm_id__startswith="simulacion/usm-").count(), 2)


def open_meteo_falso(mm_por_hora):
    """Reemplaza a urlopen en las pruebas: responde como Open-Meteo, con la misma lluvia en todas las
    coordenadas pedidas. Así las pruebas no dependen de internet ni de si hoy llueve en Santiago."""
    def urlopen_falso(url, timeout):
        cantidad = len(parse_qs(urlsplit(url).query)["latitude"][0].split(","))
        respuestas = [{"location_id": i, "current": {"precipitation": mm_por_hora / 4},  # 15 minutos
                       "hourly": {"precipitation": [mm_por_hora] * 3}} for i in range(cantidad)]
        # Con una sola coordenada, Open-Meteo devuelve un objeto y no una lista
        return BytesIO(json.dumps(respuestas if cantidad > 1 else respuestas[0]).encode())
    return urlopen_falso


class AlertasDeLluvia(TestCase):
    """La lluvia enciende y apaga sola los pasos bajo nivel (DECISIONES D14). Umbral por defecto: 4 mm/h."""

    def setUp(self):
        # Dos pasos en celdas distintas de la zona y uno que una persona encendió a mano en el admin
        self.paso_sur = PuntoAnegado.objects.create(osm_id="prueba/sur", nombre="Paso sur", lat=-33.55, lon=-70.65)
        self.paso_norte = PuntoAnegado.objects.create(osm_id="prueba/norte", nombre="Paso norte", lat=-33.40, lon=-70.55)
        self.paso_a_mano = PuntoAnegado.objects.create(osm_id="prueba/mano", nombre="Paso a mano",
                                                       lat=-33.45, lon=-70.70, activo=True)

    def llover(self, mm_por_hora):
        with patch("rutas.alertas.urlopen", side_effect=open_meteo_falso(mm_por_hora)) as urlopen:
            resumen = actualizar_puntos()
        for punto in (self.paso_sur, self.paso_norte, self.paso_a_mano):
            punto.refresh_from_db()
        return resumen, urlopen

    def test_lluvia_sobre_el_umbral_enciende_los_pasos_con_una_sola_consulta(self):
        _, urlopen = self.llover(6)

        self.assertTrue(self.paso_sur.activo)
        self.assertTrue(self.paso_sur.activado_por_lluvia)
        self.assertEqual(self.paso_sur.lluvia_mm, 6)
        self.assertTrue(self.paso_norte.activo)
        self.assertEqual(urlopen.call_count, 1)  # una petición para toda la zona, no una por paso
        alerta = Alerta.objects.get(activa=True)
        self.assertEqual(alerta.nivel, "alerta")
        self.assertIn("3 pasos bajo nivel", alerta.titulo)

    def test_lluvia_bajo_el_umbral_apaga_lo_que_encendio_la_lluvia_y_cierra_la_alerta(self):
        self.llover(6)
        self.llover(1)

        self.assertFalse(self.paso_sur.activo)
        self.assertFalse(self.paso_sur.activado_por_lluvia)
        self.assertEqual(self.paso_sur.lluvia_mm, 1)
        self.assertFalse(Alerta.objects.filter(activa=True).exists())

    def test_la_lluvia_no_apaga_un_paso_encendido_a_mano(self):
        self.llover(6)
        self.llover(0)

        self.assertTrue(self.paso_a_mano.activo)
        self.assertFalse(self.paso_a_mano.activado_por_lluvia)

    def test_la_lluvia_no_apaga_un_lugar_que_confirmaron_dos_vecinos(self):
        self.llover(6)
        for sesion in ("persona-1", "persona-2"):
            Reporte.objects.create(tipo="anegamiento", lat=self.paso_sur.lat, lon=self.paso_sur.lon, sesion=sesion,
                                   estado_verificacion="confirmado", punto=self.paso_sur)
        self.llover(0)

        self.assertTrue(self.paso_sur.activo)
        self.assertFalse(self.paso_norte.activo)

    def test_si_open_meteo_falla_queda_el_ultimo_estado(self):
        self.llover(6)
        with patch("rutas.alertas.urlopen", side_effect=URLError("sin internet")):
            with self.assertLogs("rutas.alertas", level="WARNING"):
                resumen = actualizar_puntos()

        self.assertIsNone(resumen)
        self.paso_sur.refresh_from_db()
        self.assertTrue(self.paso_sur.activo)
        self.assertEqual(self.paso_sur.lluvia_mm, 6)

    def test_mucha_lluvia_es_alarma(self):
        self.llover(8)  # el doble del umbral
        self.assertEqual(Alerta.objects.get(activa=True).nivel, "alarma")

    def test_simular_no_usa_internet(self):
        with patch("rutas.alertas.urlopen") as urlopen:
            call_command("actualizar_alertas", "--simular", "10", stdout=StringIO())

        urlopen.assert_not_called()
        self.paso_sur.refresh_from_db()
        self.assertTrue(self.paso_sur.activo)

    def test_simular_cerca_moja_solo_ese_sector(self):
        call_command("actualizar_alertas", "--simular", "10", "--cerca", f"{self.paso_sur.lat},{self.paso_sur.lon}",
                     stdout=StringIO())

        self.paso_sur.refresh_from_db()
        self.paso_norte.refresh_from_db()
        self.assertTrue(self.paso_sur.activo)
        self.assertFalse(self.paso_norte.activo)
        self.assertEqual(self.paso_norte.lluvia_mm, 0)

    def test_api_alertas_tiene_la_forma_de_docs_api(self):
        self.llover(6)
        datos = self.client.get("/api/alertas/").json()

        self.assertEqual(set(datos), {"vigentes", "actualizado", "al_dia", "fuente", "lluvia_max_mm", "puntos"})
        self.assertTrue(datos["al_dia"])
        self.assertEqual(datos["fuente"], "Open-Meteo")
        self.assertEqual(datos["lluvia_max_mm"], 6)
        self.assertEqual(set(datos["vigentes"][0]),
                         {"id", "titulo", "nivel", "descripcion", "fuente", "creada", "vigente_hasta"})
        # Solo los que encendió la lluvia: el paso encendido a mano no aparece
        self.assertEqual({p["nombre"] for p in datos["puntos"]}, {"Paso sur", "Paso norte"})
        self.assertEqual(set(datos["puntos"][0]), {"id", "nombre", "lat", "lon", "lluvia_mm"})

    def test_api_alertas_avisa_si_los_datos_no_estan_al_dia(self):
        self.llover(6)
        PuntoAnegado.objects.update(actualizado=timezone.now() - timedelta(hours=1))
        Alerta.objects.update(vigente_hasta=timezone.now() - timedelta(minutes=30))

        datos = self.client.get("/api/alertas/").json()

        self.assertFalse(datos["al_dia"])
        self.assertEqual(datos["vigentes"], [])

    def test_preparar_demo_borra_la_lluvia_y_las_alertas(self):
        call_command("cargar_datos", stdout=StringIO())
        self.llover(6)

        call_command("preparar_demo", stdout=StringIO())

        self.assertFalse(Alerta.objects.exists())
        self.assertFalse(PuntoAnegado.objects.filter(activado_por_lluvia=True).exists())
        self.assertFalse(PuntoAnegado.objects.filter(lluvia_mm__isnull=False).exists())
