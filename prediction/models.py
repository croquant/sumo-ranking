from django.db import models
from ulid import ULID

from banzuke.models import Basho
from rikishi.models import Rikishi


class Prediction(models.Model):
    id = models.CharField(
        primary_key=True, max_length=26, default=ULID, editable=False
    )
    rikishi = models.ForeignKey(
        Rikishi,
        on_delete=models.CASCADE,
        related_name="prediction",
        editable=False,
        db_index=True,
    )
    basho = models.ForeignKey(
        Basho,
        on_delete=models.CASCADE,
        related_name="prediction",
        editable=False,
        db_index=True,
    )
    n_wins = models.FloatField(default=0.0, editable=False)
