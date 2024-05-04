import concurrent.futures
import itertools
import math
import random
import time
from datetime import datetime

from django.core.management.base import BaseCommand

from banzuke.models import Basho
from prediction.models import Prediction
from rikishi.models import Rikishi
from sumoapi.client import SumoApiClient

sumoapi = SumoApiClient()


def get_precomputed_rikishi(rikishi):
    transformed_rating = (rikishi.glicko.rating - 1500) / 173.7178
    transformed_rd = rikishi.glicko.rd / 173.7178
    return transformed_rating, transformed_rd


def win_prob(precomputed_r1, precomputed_r2):
    rating_1, rd_1 = precomputed_r1
    rating_2, rd_2 = precomputed_r2

    return 1 / (
        1 + math.exp(-1 * math.sqrt(rd_1**2 + rd_2**2) * (rating_1 - rating_2))
    )


class Command(BaseCommand):
    def handle(self, *args, **options):
        t0 = time.perf_counter()

        basho_date, rik_list = sumoapi.get_next_basho()
        basho = Basho.objects.get_or_create(
            slug=basho_date,
            year=basho_date[0:4],
            month=basho_date[-2:],
            start_date=datetime.now(),
            end_date=datetime.now(),
        )[0]
        id_list = [r["rikishiID"] for r in rik_list]
        rikishis = (
            Rikishi.objects.prefetch_related("glicko")
            .filter(api_id__in=id_list)
            .order_by("-glicko__rating")
        )

        records = dict()
        precomputed_r = dict()
        for r in rikishis:
            records[r.name] = {"wins": 0, "obj": r}
            precomputed_r[r.name] = get_precomputed_rikishi(r)

        matchups = list(itertools.combinations(rikishis, 2))

        def simulate_matchups():
            local_records = {r.name: {"wins": 0, "obj": r} for r in rikishis}
            for match in matchups:
                p1 = win_prob(
                    precomputed_r[match[0].name], precomputed_r[match[1].name]
                )
                winner = random.choices(match, [p1, 1 - p1])
                local_records[winner[0].name]["wins"] += 1
            return local_records

        monte_carlo = 10000
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(simulate_matchups) for _ in range(monte_carlo)
            ]
            for future in concurrent.futures.as_completed(futures):
                results = future.result()
                for name, data in results.items():
                    records[name]["wins"] += data["wins"]

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
            pred = Prediction.objects.get_or_create(
                rikishi=r["r"], basho=basho
            )[0]
            pred.n_wins = r["wins"]
            pred.save()
            print(
                f"""{r['r'].rank.__str__()  : <15} \t
                    {r['r'].name : <12} \t
                    {r['wins']:.1f}"""
            )

        t1 = time.perf_counter()
        print(f"Total Time: {t1 - t0}s")
