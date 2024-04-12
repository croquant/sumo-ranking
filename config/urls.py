from django.contrib import admin
from django.urls import path

from .api import ninja_api

urlpatterns = [
    path("api/", ninja_api.urls),
    path("admin/", admin.site.urls),
]
