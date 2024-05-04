import itertools
import math
import random
import time

from django.core.management.base import BaseCommand

from rikishi.models import Rikishi
from sumoapi.client import SumoApiClient

sumoapi = SumoApiClient()


def win_prob(r1, r2):
    rating_1 = (r1.glicko.rating - 1500) / 173.7178
    rd_1 = r1.glicko.rd / 173.7178
    rating_2 = (r2.glicko.rating - 1500) / 173.7178
    rd_2 = r2.glicko.rd / 173.7178

    return 1 / (
        1 + math.exp(-1 * math.sqrt(rd_1**2 + rd_2**2) * (rating_1 - rating_2))
    )


class Command(BaseCommand):
    def handle(self, *args, **options):
        t0 = time.perf_counter()

        rik_list = sumoapi.get_next_basho()
        id_list = [r["rikishiID"] for r in rik_list]
        rikishis = (
            Rikishi.objects.prefetch_related("glicko")
            .filter(api_id__in=id_list)
            .order_by("-glicko__rating")
        )

        records = dict()
        for r in rikishis:
            records[r.name] = {"wins": 0, "obj": r}

        matchups = list(itertools.combinations(rikishis, 2))

        monte_carlo = 10000
        for i in range(monte_carlo):
            for match in matchups:
                p1 = win_prob(match[0], match[1])
                winner = random.choices(match, [p1, 1 - p1])
                records[winner[0].name]["wins"] += 1

        ranking = dict(
            sorted(records.items(), key=lambda item: -item[1]["wins"])
        )
        ranking = [
            {
                "r": v["obj"],
                "wins": v["wins"] / monte_carlo / 41 * 15,
            }
            for k, v in ranking.items()
        ]

        for r in ranking:
            print(
                f"{r['r'].rank.__str__()  : <15} \t{r['r'].name : <12} \t{r['wins']:.1f}"
            )

        t1 = time.perf_counter()
        print(f"Total Time: {t1 - t0}s")
