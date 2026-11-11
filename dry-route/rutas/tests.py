from django.core.management import call_command
from django.test import Client, TestCase

from .models import PuntoAnegado, Reporte
from .ruteo import RADIO_BLOQUEO_M, distancia_a_tramo_m, distancia_m

# Los dos casos de prueba del Entregable III (docs/ENTREGABLE-3.md)
PASO_DEPARTAMENTAL = "way/451437804"  # Paso bajo nivel Avenida Departamental / Gran Avenida
PASO_CERRO_NEGRO = "way/39259025"     # Paso bajo nivel Cerro Negro / Avenida Américo Vespucio


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
        respuesta = self.pedir_ruta("-33.44,-70.65", "-33.505348,-70.647249")  # Santiago Centro
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "fuera_de_zona")

    def test_api_puntos_entrega_zona_y_puntos(self):
        datos = self.client.get("/api/puntos/").json()
        self.assertEqual(len(datos["anegados"]), 4)
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
        self.reportar(Client(), (paso.lat + 0.0003, paso.lon))  # unos 30 m al norte del paso
        respuesta = self.reportar(Client(), (paso.lat, paso.lon + 0.0003)).json()

        self.assertEqual(respuesta["punto_id"], paso.id)
        paso.refresh_from_db()
        self.assertTrue(paso.activo)
        self.assertEqual(PuntoAnegado.objects.count(), 4)  # no se creó un punto repetido

    def test_tipo_invalido_devuelve_400(self):
        respuesta = self.reportar(self.client, LUGAR_EN_LA_RUTA, tipo="incendio")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "tipo_invalido")

    def test_punto_fuera_de_la_zona_devuelve_400(self):
        respuesta = self.reportar(self.client, (-33.44, -70.65))  # Santiago Centro
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "fuera_de_zona")

    def test_faltan_datos_devuelve_400(self):
        respuesta = self.client.post("/api/reportes/", {"tipo": "anegamiento"}, content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"], "parametros_invalidos")
