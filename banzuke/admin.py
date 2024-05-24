from django.contrib import admin

from .models import Basho, Torikumi


@admin.register(Basho)
class BashoAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "slug",
        "year",
        "month",
        "start_date",
        "end_date",
    )
    readonly_fields = ("slug", "year", "month", "start_date", "end_date")


@admin.register(Torikumi)
class TorikumiAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "basho",
        "division",
        "day",
        "east",
        "west",
        "winner",
    )
    readonly_fields = (
        "slug",
        "basho",
        "division",
        "day",
        "east",
        "west",
        "winner",
    )
