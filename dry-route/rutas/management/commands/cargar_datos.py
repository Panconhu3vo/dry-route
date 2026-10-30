import json

from django.conf import settings
from django.core.management.base import BaseCommand

from rutas.models import PuntoAnegado, PuntoEvacuacion


class Command(BaseCommand):
    help = "Carga a la base de datos los puntos de dry-route/data/ (generados por scripts/generar_datos.py)."

    def handle(self, *args, **options):
        carpeta = settings.BASE_DIR / "data"

        with open(carpeta / "puntos_anegados.json", encoding="utf-8") as archivo:
            for punto in json.load(archivo):
                # update_or_create por osm_id: se puede correr varias veces sin duplicar.
                # "activo" no se toca, para no borrar el escenario que alguien armó en el admin.
                PuntoAnegado.objects.update_or_create(
                    osm_id=punto["osm_id"],
                    defaults={"nombre": punto["nombre"], "tipo": punto["tipo"], "lat": punto["lat"], "lon": punto["lon"]},
                )

        with open(carpeta / "puntos_evacuacion.json", encoding="utf-8") as archivo:
            for punto in json.load(archivo):
                PuntoEvacuacion.objects.update_or_create(
                    osm_id=punto["osm_id"],
                    defaults={"nombre": punto["nombre"], "tipo": punto["tipo"], "lat": punto["lat"], "lon": punto["lon"]},
                )

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {PuntoAnegado.objects.count()} puntos anegados y "
            f"{PuntoEvacuacion.objects.count()} puntos de evacuación."
        ))
