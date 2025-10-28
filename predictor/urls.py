from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("actualizar_liga/", views.actualizar_liga, name="actualizar_liga"),
]
