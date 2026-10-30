from django.core.management import call_command
from django.test import TestCase

from .models import PuntoAnegado
from .ruteo import RADIO_BLOQUEO_M, distancia_a_tramo_m

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
