from django.db.models import F, Q, Window
from django.db.models.functions import RowNumber
from django.shortcuts import render
from django.views.generic.list import ListView

from glicko.models import GlickoHistory
from rikishi.models import Rikishi


def home_view(request):
    return render(request, "home.html")


class RankingView(ListView):
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
    data_2 = []

    rikishi = (
        Rikishi.objects.prefetch_related("glicko")
        .exclude(Q(rank=None) | Q(intai__isnull=False))
        .order_by("?")
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

    all_dates = set()
    for basho_glicko in history_1:
        all_dates.add(basho_glicko.basho.end_date.isoformat())
    for basho_glicko in history_2:
        all_dates.add(basho_glicko.basho.end_date.isoformat())

    vd1 = 0
    vd2 = 0
    for date in sorted(all_dates):
        vd1 = next(
            (
                bg.rating
                for bg in history_1
                if bg.basho.end_date.isoformat() == date
            ),
            vd1,
        )
        data_1.append(vd1)

        vd2 = next(
            (
                bg.rating
                for bg in history_2
                if bg.basho.end_date.isoformat() == date
            ),
            vd2,
        )
        data_2.append(vd2)

    return render(
        request,
        "charts/base.html",
        {
            "title": f"{rikishi_1.name} vs {rikishi_2.name}",
            "name_1": rikishi_1.name,
            "data_1": data_1,
            "name_2": rikishi_2.name,
            "data_2": data_2,
            "labels": sorted(all_dates),
        },
    )
