from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("ranking/", views.ranking_view.as_view(), name="ranking"),
]
