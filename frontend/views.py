from django.db.models import F, Q, Window
from django.db.models.functions import RowNumber
from django.shortcuts import render
from django.views.generic.list import ListView

from rikishi.models import Rikishi


def home_view(request):
    return render(request, "home.html")


class ranking_view(ListView):
    model = Rikishi
    paginate_by = 12
    template_name = "ranking.html"

    def get_queryset(self, *args, **kwargs):
        qs = (
            Rikishi.objects.exclude(Q(rank=None) | Q(intai__isnull=False))
            .filter(
                Q(rank__division__in=["makuuchi", "juryo"])
            )  # Use Q objects
            .select_related("rank")
            .order_by("-glicko__rating")
            .annotate(
                position=Window(
                    expression=RowNumber(), order_by=F("glicko__rating").desc()
                )
            )
        )
        return qs
