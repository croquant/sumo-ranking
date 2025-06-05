from django.db.models.signals import post_save
from django.dispatch import receiver

from glicko.models import Glicko

from .models import Rikishi


@receiver(post_save, sender=Rikishi)
def create_glicko_for_rikishi(sender, instance, created, **kwargs):
    """Create a Glicko rating for each new Rikishi."""
    if created:
        Glicko.objects.create(rikishi=instance)
