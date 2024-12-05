import pycountry
from django.db import models
from django.utils.text import slugify
from ulid import ULID

from .constants import (
    DIRECTION_NAMES,
    DIRECTION_NAMES_SHORT,
    DIVISION_NAMES,
    DIVISION_NAMES_SHORT,
    RANK_NAMES,
    RANK_NAMES_SHORT,
    RANKING_LEVELS,
)


class Division(models.Model):
    slug = models.SlugField(primary_key=True, editable=False)
    name = models.CharField(
        max_length=12, choices=DIVISION_NAMES, editable=False
    )
    level = models.PositiveSmallIntegerField(editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Division, self).save(*args, **kwargs)

    def short_name(self):
        return DIVISION_NAMES_SHORT[self.name]

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["level"]


class Rank(models.Model):
    slug = models.SlugField(primary_key=True, editable=False)
    division = models.ForeignKey(
        Division,
        on_delete=models.CASCADE,
        related_name="ranks",
        editable=False,
    )
    title = models.CharField(max_length=12, choices=RANK_NAMES, editable=False)
    level = models.PositiveSmallIntegerField(editable=False)
    order = models.PositiveSmallIntegerField(
        blank=True, default=0, editable=False
    )
    direction = models.CharField(
        max_length=4,
        choices=DIRECTION_NAMES,
        blank=True,
        null=True,
        editable=False,
    )

    def name(self):
        if self.order and self.direction:
            dir_shorthand = DIRECTION_NAMES_SHORT[self.direction]
            return f"{self.title} {self.order}{dir_shorthand}"
        else:
            return self.title

    def long_name(self):
        if self.order and self.direction:
            return f"{self.title} {self.order} {self.direction}"
        else:
            return self.title

    def short_name(self):
        shorthand = RANK_NAMES_SHORT[self.title]
        if self.order and self.direction:
            dir_shorthand = DIRECTION_NAMES_SHORT[self.direction]
            return f"{shorthand}{self.order}{dir_shorthand}"
        else:
            return shorthand

    def save(self, *args, **kwargs):
        self.slug = slugify(self.short_name())
        if Division.objects.filter(name=self.title).exists():
            self.division = Division.objects.get(name=self.title)
        else:
            self.division = Division.objects.get(name="Makuuchi")
        self.level = RANKING_LEVELS[self.title]
        super(Rank, self).save(*args, **kwargs)

    def __str__(self):
        return self.name()

    class Meta:
        ordering = ["level", "order", "direction"]


class Heya(models.Model):
    slug = models.SlugField(primary_key=True, editable=False)
    name = models.CharField(max_length=32, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Heya, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Heya"


class Shusshin(models.Model):
    slug = models.SlugField(primary_key=True, editable=False)
    name = models.CharField(max_length=32, editable=False)
    international = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Shusshin, self).save(*args, **kwargs)

    def flag(self):
        if self.international:
            return pycountry.countries.lookup(self.name).flag
        else:
            return "🇯🇵"

    def __str__(self):
        return f"{self.flag()}{self.name}"

    class Meta:
        ordering = ["international", "name"]
        verbose_name_plural = "Shusshin"


class Rikishi(models.Model):
    id = models.CharField(
        primary_key=True, max_length=26, default=ULID, editable=False
    )
    api_id = models.PositiveSmallIntegerField(
        unique=True, editable=False, db_index=True
    )
    name = models.CharField(max_length=64)
    name_jp = models.CharField(max_length=64)
    rank = models.ForeignKey(
        Rank,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rikishi",
    )
    heya = models.ForeignKey(
        Heya,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rikishi",
    )
    shusshin = models.ForeignKey(
        Shusshin,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rikishi",
    )
    height = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    weight = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    birth_date = models.DateField(blank=True, null=True)
    debut = models.DateField(blank=True, null=True)
    intai = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Rikishi"
