from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("ranking/", views.GlickoRankingView.as_view(), name="ranking"),
    path("predictions/", views.PredictionView.as_view(), name="predictions"),
    path("chart/", views.chart_view, name="chart"),
]
