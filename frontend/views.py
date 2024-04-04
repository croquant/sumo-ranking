from django.db.models import Q
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
            .filter(Q(rank__division="makuuchi") | Q(rank__division="juryo"))
            .order_by("-glicko__rating")
        )
        return qs
