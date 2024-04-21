from django.contrib import admin
from django.urls import include, path

from .api import ninja_api

urlpatterns = [
    path("", include("frontend.urls")),
    path("api/", ninja_api.urls),
    path("admin/", admin.site.urls),
]
