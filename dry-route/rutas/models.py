from django.db import models


class PuntoAnegado(models.Model):
    """Paso bajo nivel u otro punto que se puede anegar. Si está activo, la ruta lo evita."""

    # Texto y no número: en OpenStreetMap un "way" y un "node" pueden tener el mismo número (DECISIONES D4)
    osm_id = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, default="paso_bajo_nivel")  # o uno de Reporte.TIPOS, si lo crearon reportes
    lat = models.FloatField()
    lon = models.FloatField()
    # Sin sensores, el anegamiento se simula marcando esta casilla en el admin (DECISIONES D4)
    activo = models.BooleanField("anegado ahora", default=False)
    fuente = models.CharField(max_length=50, default="OpenStreetMap")
    # True si lo encendieron dos reportes: se apaga solo cuando vencen. Lo encendido a mano nunca vence (D11)
    activado_por_reportes = models.BooleanField("activado por reportes", default=False)

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


class Reporte(models.Model):
    """Aviso de una persona sobre un problema en la calle. Solo no bloquea rutas: hacen falta dos (DECISIONES D11)."""

    TIPOS = [
        ("anegamiento", "Calle anegada"),
        ("calle_cortada", "Calle cortada"),
        ("arbol_caido", "Árbol caído"),
        ("puente_cortado", "Puente cortado"),
    ]
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("confirmado", "Confirmado"),
        ("descartado", "Descartado"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.CharField("descripción", max_length=200, blank=True)
    lat = models.FloatField()
    lon = models.FloatField()
    fecha_hora = models.DateTimeField("fecha y hora", auto_now_add=True)
    estado_verificacion = models.CharField("estado", max_length=20, choices=ESTADOS, default="pendiente")
    # Clave de sesión del navegador: como no hay login, es lo que distingue a dos personas
    sesion = models.CharField("sesión", max_length=40)
    # Vacío mientras esté pendiente. SET_NULL: si se borra el punto, el reporte queda como registro
    punto = models.ForeignKey(PuntoAnegado, on_delete=models.SET_NULL, null=True, blank=True, related_name="reportes")

    class Meta:
        verbose_name = "reporte"
        verbose_name_plural = "reportes"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.get_estado_verificacion_display()})"
