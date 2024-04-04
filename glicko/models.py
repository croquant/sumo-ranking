from django.db import models
from ulid import ULID

from banzuke.models import Basho
from glicko.constants import DEFAULT_RATING, DEFAULT_RD, DEFAULT_VOLATILITY
from rikishi.models import Rikishi


class Glicko(models.Model):
    rikishi = models.OneToOneField(
        Rikishi,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="glicko",
        db_index=True,
    )
    rating = models.FloatField(default=DEFAULT_RATING, editable=False)
    rd = models.FloatField(default=DEFAULT_RD, editable=False)
    vol = models.FloatField(
        default=DEFAULT_VOLATILITY,
        editable=False,
    )


class GlickoHistory(models.Model):
    id = models.CharField(
        primary_key=True, max_length=26, default=ULID, editable=False
    )
    glicko = models.ForeignKey(
        Glicko,
        on_delete=models.CASCADE,
        related_name="history",
        db_index=True,
    )
    basho = models.ForeignKey(
        Basho,
        on_delete=models.CASCADE,
        related_name="glicko_history",
        editable=False,
        db_index=True,
    )
    rating = models.FloatField(default=DEFAULT_RATING, editable=False)
    rd = models.FloatField(default=DEFAULT_RD, editable=False)
    vol = models.FloatField(
        default=DEFAULT_VOLATILITY,
        editable=False,
    )
