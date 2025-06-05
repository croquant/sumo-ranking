# Create your views here.
import math
from typing import Any, List

from django.db.models import F, Q, Window
from django.db.models.functions import RowNumber
from ninja import Router, Schema
from ninja.pagination import PaginationBase, paginate

from rikishi.schemas import RikishiSchema

from .models import Rikishi

rikishi_router = Router()


class PaginationSchema(Schema):
    current_page: int
    next_page: int
    previous_page: int
    total_page: int


class CustomPagination(PaginationBase):
    class Input(Schema):
        page: int = 0
        max_per_page: int = 20

    class Output(Schema):
        items: List[Any]
        total_items: int
        pagination: PaginationSchema

    def paginate_queryset(self, queryset, pagination: Input, **params):
        page = pagination.page
        max_per_page = pagination.max_per_page
        total_items = queryset.count()
        total_page = max(math.ceil(total_items / max_per_page) - 1, 0)
        next_page = min(page + 1, total_page)
        previous_page = max(page - 1, 0)
        return {
            "items": queryset[
                page * max_per_page : page * max_per_page + max_per_page
            ],
            "total_items": total_items,
            "pagination": {
                "current_page": page,
                "total_page": total_page,
                "next_page": next_page,
                "previous_page": previous_page,
            },
        }


@rikishi_router.get("/ranking", response=List[RikishiSchema])
@paginate(CustomPagination, page_size=21)
def get_glicko_ranking(request):
    qs = (
        Rikishi.objects.select_related("heya", "shusshin", "rank")
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
