from django.db import models
from ulid import ULID

from banzuke.constants import BASHO_NAMES
from rikishi.models import Division, Rikishi


class Basho(models.Model):
    slug = models.CharField(max_length=6, primary_key=True, editable=False)
    year = models.PositiveSmallIntegerField(editable=False)
    month = models.PositiveSmallIntegerField(editable=False)
    start_date = models.DateField(editable=False)
    end_date = models.DateField(editable=False)

    def name(self):
        return BASHO_NAMES[self.month]

    def __str__(self):
        return f"{self.name()} {self.year}"

    class Meta:
        verbose_name_plural = "Basho"


class Torikumi(models.Model):
    id = models.CharField(
        primary_key=True, max_length=26, default=ULID, editable=False
    )
    basho = models.ForeignKey(
        Basho,
        on_delete=models.CASCADE,
        related_name="torikumi",
        editable=False,
        db_index=True,
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        related_name="torikumi",
        editable=False,
        db_index=True,
    )
    day = models.PositiveSmallIntegerField(editable=False)
    east = models.ForeignKey(
        Rikishi, on_delete=models.CASCADE, related_name="east", editable=False
    )
    west = models.ForeignKey(
        Rikishi, on_delete=models.CASCADE, related_name="west", editable=False
    )
    winner = models.ForeignKey(
        Rikishi, on_delete=models.CASCADE, related_name="win", editable=False
    )

    class Meta:
        verbose_name_plural = "Torikumi"
