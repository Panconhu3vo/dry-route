from django.db import models


class PuntoAnegado(models.Model):
    """Paso bajo nivel u otro punto que se puede anegar. Si está activo, la ruta lo evita."""

    # Texto y no número: en OpenStreetMap un "way" y un "node" pueden tener el mismo número (DECISIONES D4)
    osm_id = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, default="paso_bajo_nivel")
    lat = models.FloatField()
    lon = models.FloatField()
    # Sin sensores, el anegamiento se simula marcando esta casilla en el admin (DECISIONES D4)
    activo = models.BooleanField("anegado ahora", default=False)
    fuente = models.CharField(max_length=50, default="OpenStreetMap")

    class Meta:
        verbose_name = "punto anegado"
        verbose_name_plural = "puntos anegados"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class PuntoEvacuacion(models.Model):
    """Lugar seguro al que se guía al usuario cuando no hay ruta segura a su destino."""

    osm_id = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50)  # hospital, clinica, bomberos, carabineros, colegio, punto_encuentro
    lat = models.FloatField()
    lon = models.FloatField()

    class Meta:
        verbose_name = "punto de evacuación"
        verbose_name_plural = "puntos de evacuación"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
