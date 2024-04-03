from django.contrib import admin

from .models import Glicko


@admin.register(Glicko)
class GlickoAdmin(admin.ModelAdmin):
    list_display = (
        "rikishi",
        "rating",
        "rd",
        "vol",
    )
    search_fields = ("rikishi__name",)
