import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models import Q

from banzuke.models import Basho, Torikumi
from glicko.constants import DEFAULT_RATING, DEFAULT_RD, DEFAULT_VOLATILITY
from glicko.glicko2 import Player
from glicko.models import Glicko, GlickoHistory
from rikishi.models import Rikishi


def get_contestants(basho: Basho) -> set[str]:
    return set(
        Torikumi.objects.filter(basho=basho)
        .values_list("east", flat=True)
        .distinct()
        .union(
            Torikumi.objects.filter(basho=basho)
            .values_list("west", flat=True)
            .distinct()
        )
    )


def get_basho_record(
    rikishi: Rikishi, bouts: list[Torikumi]
) -> tuple[list[float], list[float], list[int]]:
    records = []
    for bout in bouts:
        score = 1 if bout.winner == rikishi else 0
        opponent = bout.west if bout.east == rikishi else bout.east
        records.append((opponent.glicko.rating, opponent.glicko.rd, score))
    return tuple(map(list, zip(*records)))


class Command(BaseCommand):
    def handle(self, *args, **options):
        t0 = time.perf_counter()

        Glicko.objects.all().update(
            rating=DEFAULT_RATING,
            rd=DEFAULT_RD,
            vol=DEFAULT_VOLATILITY,
        )
        GlickoHistory.objects.all().delete()

        basho_list = Torikumi.objects.values_list(
            "basho", flat=True
        ).distinct()

        for basho_id in basho_list:
            basho = Basho.objects.get(pk=basho_id)
            basho_date = datetime.strptime(basho_id, "%Y%m")
            print(f"==========BASHO-{basho_date}==========")

            contestants = get_contestants(basho_id)
            print(f"Constestants: {len(contestants)}")

            glickos = []
            for contestant in contestants:
                bouts = Torikumi.objects.filter(basho=basho_id).filter(
                    Q(east=contestant) | Q(west=contestant)
                )

                rikishi = Rikishi.objects.get(pk=contestant)
                glicko_player = Player(
                    rating=rikishi.glicko.rating,
                    rd=rikishi.glicko.rd,
                    vol=rikishi.glicko.vol,
                )
                if len(bouts) < 1:
                    glicko_player.did_not_compete()
                else:
                    rating_list, rd_list, score_list = get_basho_record(
                        rikishi, bouts
                    )
                    glicko_player.update_player(
                        rating_list=rating_list,
                        RD_list=rd_list,
                        outcome_list=score_list,
                    )

                glickos.append(
                    GlickoHistory(
                        glicko=rikishi.glicko,
                        basho=basho,
                        rating=max(glicko_player.getRating(), 1),
                        rd=glicko_player.getRd(),
                        vol=glicko_player.vol,
                    )
                )
            GlickoHistory.objects.bulk_create(glickos)

            active_rikishi = Rikishi.objects.filter(
                Q(intai__isnull=True) | Q(intai__gte=basho_date)
            ).filter(debut__lte=basho_date)
            print(f"Active: {len(active_rikishi)}")

            glickos_to_update = []
            for rikishi in active_rikishi:
                glicko = rikishi.glicko
                glicko_history = GlickoHistory.objects.filter(
                    basho=basho, glicko=rikishi.glicko
                ).first()
                if glicko_history:
                    glicko.rating = glicko_history.rating
                    glicko.rd = glicko_history.rd
                    glicko.vol = glicko_history.vol
                else:
                    glicko_player = Player(
                        rating=glicko.rating,
                        rd=glicko.rd,
                        vol=glicko.vol,
                    )
                    glicko_player.did_not_compete()
                    glicko.rating = glicko_player.getRating()
                    glicko.rd = glicko_player.getRd()
                    glicko.vol = glicko_player.vol
                glickos_to_update.append(glicko)

            Glicko.objects.bulk_update(
                glickos_to_update,
                ["rating", "rd", "vol"],
            )

        t1 = time.perf_counter()
        print(f"Total Time: {t1 - t0}s")
