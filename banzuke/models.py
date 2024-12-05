from django.db import models
from django.utils.text import slugify

from banzuke.constants import BASHO_NAMES
from rikishi.models import Division, Rank, Rikishi


class Basho(models.Model):
    slug = models.CharField(max_length=6, primary_key=True, editable=False)
    year = models.PositiveSmallIntegerField(editable=False)
    month = models.PositiveSmallIntegerField(editable=False)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def name(self):
        return BASHO_NAMES[self.month]

    def __str__(self):
        return f"{self.name()} {self.year}"

    class Meta:
        verbose_name_plural = "Basho"


class Torikumi(models.Model):
    slug = models.CharField(primary_key=True, max_length=32, editable=False)
    basho = models.ForeignKey(
        Basho,
        on_delete=models.CASCADE,
        related_name="torikumi",
        editable=False,
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        related_name="torikumi",
        editable=False,
    )
    day = models.PositiveSmallIntegerField(editable=False)
    east = models.ForeignKey(
        Rikishi, on_delete=models.CASCADE, related_name="east", editable=False
    )
    east_rank = models.ForeignKey(
        Rank,
        on_delete=models.CASCADE,
        editable=False,
        related_name="east_rank",
        blank=True,
        null=True,
        default=None,
    )
    west = models.ForeignKey(
        Rikishi, on_delete=models.CASCADE, related_name="west", editable=False
    )
    west_rank = models.ForeignKey(
        Rank,
        on_delete=models.CASCADE,
        editable=False,
        related_name="west_rank",
        blank=True,
        null=True,
        default=None,
    )
    winner = models.ForeignKey(
        Rikishi, on_delete=models.CASCADE, related_name="win", editable=False
    )

    def save(self, *args, **kwargs):
        self.slug = self.gen_slug()
        super(Torikumi, self).save(*args, **kwargs)

    def gen_slug(self):
        return slugify(
            f"{self.basho.slug}-{self.division.level}-{self.day}-{self.east.api_id}-{self.west.api_id}"
        )

    class Meta:
        verbose_name_plural = "Torikumi"
