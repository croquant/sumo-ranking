from django.db.models import F, Q, Window
from django.db.models.functions import RowNumber
from django.shortcuts import render
from django.views.generic.list import ListView

from glicko.models import GlickoHistory
from rikishi.models import Rikishi


def home_view(request):
    return render(request, "home.html")


class ranking_view(ListView):
    model = Rikishi
    paginate_by = 20
    template_name = "ranking.html"

    def get_queryset(self, *args, **kwargs):
        qs = (
            Rikishi.objects.select_related("rank", "shusshin")
            .prefetch_related("glicko")
            .exclude(Q(rank=None) | Q(intai__isnull=False))
            .order_by("-glicko__rating")
            .annotate(
                position=Window(
                    expression=RowNumber(), order_by=F("glicko__rating").desc()
                )
            )
        )
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        page = context["page_obj"]
        paginator_range = page.paginator.get_elided_page_range(
            page.number, on_each_side=1, on_ends=2
        )
        context["paginator_range"] = paginator_range
        return context


def chart_view(request):
    data_1 = []
    labels_1 = []
    data_2 = []
    labels_2 = []

    rikishi = (
        Rikishi.objects.prefetch_related("glicko")
        .exclude(Q(rank=None) | Q(intai__isnull=False))
        .order_by("-glicko__rating")
    )
    rikishi_1 = rikishi[0]
    rikishi_2 = rikishi[1]

    history_1 = (
        GlickoHistory.objects.select_related("basho")
        .filter(glicko=rikishi_1.glicko)
        .order_by("basho")
    )
    history_2 = (
        GlickoHistory.objects.select_related("basho")
        .filter(glicko=rikishi_2.glicko)
        .order_by("basho")
    )

    for basho_glicko in history_1:
        data_1.append(basho_glicko.rating)
        labels_1.append(basho_glicko.basho.end_date.isoformat())

    for basho_glicko in history_2:
        data_2.append(basho_glicko.rating)
        labels_2.append(basho_glicko.basho.end_date.isoformat())

    return render(
        request,
        "charts/base.html",
        {
            "title": f"{rikishi_1.name} vs {rikishi_2.name}",
            "data_1": data_1,
            "data_2": data_2,
            "labels": sorted(set(labels_1 + labels_2)),
        },
    )
