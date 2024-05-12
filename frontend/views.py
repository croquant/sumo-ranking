from django.db.models import F, Q, Window
from django.db.models.functions import RowNumber
from django.shortcuts import render
from django.views.generic.list import ListView

from glicko.models import GlickoHistory
from prediction.models import Prediction
from rikishi.models import Rikishi


def home_view(request):
    return render(request, "home.html")


class GlickoRankingView(ListView):
    model = Rikishi
    paginate_by = 42
    template_name = "tables/glicko_ranking.html"

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


class PredictionView(ListView):
    model = Prediction
    template_name = "tables/predictions.html"

    def get_queryset(self, *args, **kwargs):
        last_pred = Prediction.objects.select_related("basho").latest(
            "basho__year", "basho__month"
        )
        qs = (
            Prediction.objects.select_related(
                "rikishi", "rikishi__rank", "rikishi__shusshin"
            )
            .filter(basho=last_pred.basho)
            .order_by("-n_wins")
            .annotate(
                position=Window(
                    expression=RowNumber(), order_by=F("n_wins").desc()
                )
            )
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_pred = Prediction.objects.select_related("basho").latest(
            "basho__year", "basho__month"
        )
        context["basho"] = last_pred.basho
        return context


def chart_view(request):
    data_1 = []
    data_2 = []
    data_3 = []
    data_4 = []

    rikishi = (
        Rikishi.objects.prefetch_related("glicko")
        .exclude(Q(rank=None) | Q(intai__isnull=False))
        .order_by("-glicko__rating")
    )
    rikishi_1 = rikishi[0]
    rikishi_2 = rikishi[1]
    rikishi_3 = rikishi[2]
    rikishi_4 = rikishi[3]

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
    history_3 = (
        GlickoHistory.objects.select_related("basho")
        .filter(glicko=rikishi_3.glicko)
        .order_by("basho")
    )
    history_4 = (
        GlickoHistory.objects.select_related("basho")
        .filter(glicko=rikishi_4.glicko)
        .order_by("basho")
    )

    all_dates = set()
    for basho_glicko in history_1:
        all_dates.add(basho_glicko.basho.end_date.isoformat())
    for basho_glicko in history_2:
        all_dates.add(basho_glicko.basho.end_date.isoformat())
    for basho_glicko in history_3:
        all_dates.add(basho_glicko.basho.end_date.isoformat())
    for basho_glicko in history_4:
        all_dates.add(basho_glicko.basho.end_date.isoformat())

    vd1 = "NaN"
    vd2 = "NaN"
    vd3 = "NaN"
    vd4 = "NaN"
    for date in sorted(all_dates):
        vd1 = next(
            (
                round(bg.rating)
                for bg in history_1
                if bg.basho.end_date.isoformat() == date
            ),
            vd1,
        )
        data_1.append(vd1)

        vd2 = next(
            (
                round(bg.rating)
                for bg in history_2
                if bg.basho.end_date.isoformat() == date
            ),
            vd2,
        )
        data_2.append(vd2)

        vd3 = next(
            (
                round(bg.rating)
                for bg in history_3
                if bg.basho.end_date.isoformat() == date
            ),
            vd3,
        )
        data_3.append(vd3)

        vd4 = next(
            (
                round(bg.rating)
                for bg in history_4
                if bg.basho.end_date.isoformat() == date
            ),
            vd4,
        )
        data_4.append(vd4)

    return render(
        request,
        "charts/base.html",
        {
            "name_1": rikishi_1.name,
            "data_1": data_1,
            "name_2": rikishi_2.name,
            "data_2": data_2,
            "name_3": rikishi_3.name,
            "data_3": data_3,
            "name_4": rikishi_4.name,
            "data_4": data_4,
            "labels": sorted(all_dates),
        },
    )
