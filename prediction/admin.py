from django.contrib import admin

from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "rikishi", "basho", "n_wins")
    search_fields = (
        "rikishi__name",
        "basho__slug",
    )
    list_filter = ("basho",)
    ordering = ("id",)
    verbose_name = "Prediction"
