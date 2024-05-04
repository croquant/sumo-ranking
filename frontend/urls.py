from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("ranking/", views.RankingView.as_view(), name="ranking"),
    path("chart/", views.chart_view, name="chart"),
]
