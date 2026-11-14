from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from .models import PuntoAnegado, Reporte
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
