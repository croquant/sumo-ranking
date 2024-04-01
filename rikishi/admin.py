from django.contrib import admin

from .models import Division, Heya, Rank, Shusshin


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ("name", "level")
    readonly_fields = ("slug",)


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ("name", "division", "order", "direction")
    readonly_fields = ("slug", "name", "division", "order", "direction")
    list_filter = ("division", "direction")


@admin.register(Heya)
class HeyaAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    readonly_fields = ("name", "slug")


@admin.register(Shusshin)
class ShusshinAdmin(admin.ModelAdmin):
    list_display = ("__str__", "international")
    readonly_fields = ("slug", "name", "flag", "international")
    list_filter = ("international",)
