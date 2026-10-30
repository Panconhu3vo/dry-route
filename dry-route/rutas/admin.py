from django.contrib import admin

from .models import PuntoAnegado, PuntoEvacuacion


@admin.register(PuntoAnegado)
class PuntoAnegadoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo", "lat", "lon"]
    # Permite marcar "anegado ahora" directo en la lista, para armar el escenario de la demo con un clic
    list_editable = ["activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


@admin.register(PuntoEvacuacion)
class PuntoEvacuacionAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tipo", "lat", "lon"]
    list_filter = ["tipo"]
    search_fields = ["nombre"]
