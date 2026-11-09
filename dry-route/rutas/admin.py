from django.contrib import admin

from .models import PuntoAnegado, PuntoEvacuacion, Reporte


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


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ["tipo", "estado_verificacion", "fecha_hora", "punto"]
    list_filter = ["estado_verificacion"]
    # Se ven pero no se editan: son el registro de cuándo se reportó y desde qué sesión
    readonly_fields = ["fecha_hora", "sesion"]
    actions = ["descartar"]

    @admin.action(description="Descartar los reportes seleccionados")
    def descartar(self, request, queryset):
        cantidad = queryset.update(estado_verificacion="descartado")
        self.message_user(request, f"Reportes descartados: {cantidad}.")
