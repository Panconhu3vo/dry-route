from django.contrib import admin

from .models import Alerta, PuntoAnegado, PuntoEvacuacion, Reporte
from .reportes import desactivar_puntos_vencidos


@admin.register(PuntoAnegado)
class PuntoAnegadoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo", "activado_por_reportes", "activado_por_lluvia", "lluvia_mm", "lat", "lon"]
    # Permite marcar "anegado ahora" directo en la lista, para armar el escenario de la demo con un clic
    list_editable = ["activo"]
    list_filter = ["activo", "activado_por_reportes", "activado_por_lluvia"]
    search_fields = ["nombre"]
    # Los escribe solo la app (reportes y lluvia): se ven pero no se editan
    readonly_fields = ["activado_por_reportes", "activado_por_lluvia", "lluvia_mm", "actualizado"]

    def save_model(self, request, obj, form, change):
        # Si una persona cambia "anegado ahora" a mano, manda su decisión: ni el vencimiento de reportes
        # ni la lluvia que baja lo apagan después
        if "activo" in form.changed_data:
            obj.activado_por_reportes = False
            obj.activado_por_lluvia = False
        super().save_model(request, obj, form, change)


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
        apagados = desactivar_puntos_vencidos()  # el efecto se ve altiro en el mapa, sin esperar otra consulta
        self.message_user(request, f"Reportes descartados: {cantidad}. Puntos que se apagaron: {apagados}.")


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "nivel", "fuente", "activa", "creada", "vigente_hasta"]
    list_filter = ["nivel", "activa", "fuente"]
    readonly_fields = ["creada"]
