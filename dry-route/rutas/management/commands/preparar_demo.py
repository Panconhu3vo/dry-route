from django.core.management.base import BaseCommand, CommandError

from rutas.models import PuntoAnegado, Reporte
from rutas.reportes import FUENTE_REPORTES

# El paso del guion de la demo: Avenida Departamental / Gran Avenida (docs/ENTREGA-FINAL.md)
PASO_DE_LA_DEMO = "way/451437804"

# Anegamientos simulados en la universidad: quedan creados pero APAGADOS. En la demo se encienden desde
# el admin ("anegado ahora") y la ruta que sale del campus pasa a ser una ruta de escape (docs/ENTREGA-FINAL.md).
# Empiezan con "Anegamiento" para que aparezcan primeros en la lista del admin, que se ordena por nombre.
SIMULACIONES_UNIVERSIDAD = [
    {"osm_id": "simulacion/usm-san-joaquin", "nombre": "Anegamiento simulado: USM campus San Joaquín",
     "lat": -33.491080, "lon": -70.619010},
    {"osm_id": "simulacion/usm-vitacura", "nombre": "Anegamiento simulado: USM campus Vitacura",
     "lat": -33.377500, "lon": -70.576900},
]
FUENTE_SIMULACION = "Simulación para la demo"


class Command(BaseCommand):
    help = ("Deja el escenario de la demo: sin reportes, solo el paso Departamental / Gran Avenida anegado "
            "y los anegamientos simulados de la universidad listos pero apagados.")

    def handle(self, *args, **options):
        if not PuntoAnegado.objects.filter(osm_id=PASO_DE_LA_DEMO).exists():
            raise CommandError("No está el paso de la demo en la base de datos. Corre primero: python manage.py cargar_datos")

        reportes_borrados, _ = Reporte.objects.all().delete()
        # Los puntos que crearon los reportes desaparecen; los de OpenStreetMap solo se apagan
        puntos_borrados, _ = PuntoAnegado.objects.filter(fuente=FUENTE_REPORTES).delete()
        PuntoAnegado.objects.update(activo=False, activado_por_reportes=False)
        PuntoAnegado.objects.filter(osm_id=PASO_DE_LA_DEMO).update(activo=True)

        for simulacion in SIMULACIONES_UNIVERSIDAD:
            PuntoAnegado.objects.update_or_create(
                osm_id=simulacion["osm_id"],
                defaults={"nombre": simulacion["nombre"], "tipo": "anegamiento", "lat": simulacion["lat"],
                          "lon": simulacion["lon"], "activo": False, "fuente": FUENTE_SIMULACION},
            )

        self.stdout.write(self.style.SUCCESS(
            f"Escenario de la demo listo: {reportes_borrados} reportes y {puntos_borrados} puntos de reportes borrados. "
            "Solo queda anegado el paso Departamental / Gran Avenida. "
            "Los anegamientos simulados de la USM están listos en el admin, apagados."
        ))
