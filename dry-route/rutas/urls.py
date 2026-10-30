from django.urls import path

from . import views

urlpatterns = [
    path("", views.mapa, name="mapa"),
    path("api/puntos/", views.api_puntos, name="api_puntos"),
    path("api/ruta/", views.api_ruta, name="api_ruta"),
]
