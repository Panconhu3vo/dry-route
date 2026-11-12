from django.core.management.base import BaseCommand, CommandError

from rutas.models import PuntoAnegado, Reporte
from rutas.reportes import FUENTE_REPORTES

# El paso del guion de la demo: Avenida Departamental / Gran Avenida (docs/ENTREGA-FINAL.md)
PASO_DE_LA_DEMO = "way/451437804"


class Command(BaseCommand):
    help = "Deja el escenario de la demo: sin reportes y solo con el paso Departamental / Gran Avenida anegado."

    def handle(self, *args, **options):
        if not PuntoAnegado.objects.filter(osm_id=PASO_DE_LA_DEMO).exists():
            raise CommandError("No está el paso de la demo en la base de datos. Corre primero: python manage.py cargar_datos")

        reportes_borrados, _ = Reporte.objects.all().delete()
        # Los puntos que crearon los reportes desaparecen; los de OpenStreetMap solo se apagan
        puntos_borrados, _ = PuntoAnegado.objects.filter(fuente=FUENTE_REPORTES).delete()
        PuntoAnegado.objects.update(activo=False, activado_por_reportes=False)
        PuntoAnegado.objects.filter(osm_id=PASO_DE_LA_DEMO).update(activo=True)

        self.stdout.write(self.style.SUCCESS(
            f"Escenario de la demo listo: {reportes_borrados} reportes y {puntos_borrados} puntos de reportes borrados. "
            "Solo queda anegado el paso Departamental / Gran Avenida."
        ))
