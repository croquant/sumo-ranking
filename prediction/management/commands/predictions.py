import concurrent.futures
import itertools
import random
import time

from django.core.management.base import BaseCommand

from banzuke.models import Basho
from prediction.models import Prediction
from prediction.utils import get_precomputed_probs
from rikishi.models import Rikishi
from sumoapi.client import SumoApiClient

sumoapi = SumoApiClient()


class Command(BaseCommand):
    def handle(self, *args, **options):
        t0 = time.perf_counter()

        basho_date, rik_list = sumoapi.get_next_basho()
        basho = Basho.objects.get_or_create(
            slug=basho_date,
            year=basho_date[0:4],
            month=basho_date[-2:],
        )[0]
        id_list = [r["rikishiID"] for r in rik_list]
        rikishis = (
            Rikishi.objects.select_related("heya")
            .prefetch_related("glicko")
            .filter(api_id__in=id_list)
        )

        records = dict()
        for r in rikishis:
            records[r.name] = {"wins": 0, "total": 0, "obj": r}

        precomputed_probs = get_precomputed_probs(rikishis)

        matchups = list(itertools.combinations(rikishis, 2))

        def simulate_matchups():
            local_records = {
                r.name: {"wins": 0, "total": 0, "obj": r} for r in rikishis
            }
            for match in matchups:
                if match[0].heya == match[1].heya:
                    continue

                p1 = precomputed_probs[match[0].name][match[1].name]
                winner = random.choices(match, [p1, 1 - p1])
                local_records[winner[0].name]["wins"] += 1
                local_records[match[0].name]["total"] += 1
                local_records[match[1].name]["total"] += 1
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
                    records[name]["total"] += data["total"]

        for _, record in records.items():
            record["win_percent"] = record["wins"] / record["total"]
            record["predicted_wins"] = record["win_percent"] * 15

        records = sorted(
            records.items(), key=lambda x: x[1]["win_percent"], reverse=True
        )

        for _, record in records:
            print(
                f"{record['obj'].rank.__str__()  : <12} \t{record['obj'].name : <12} \t{record['predicted_wins']:.2f} ({record['win_percent'] * 100:.2f}%) {record['wins']}/{record['total']}"  # noqa: E501
            )
            pred = Prediction.objects.get_or_create(
                rikishi=record["obj"], basho=basho
            )[0]
            pred.n_wins = record["predicted_wins"]
            pred.save()

        t1 = time.perf_counter()
        print(f"Total Time: {t1 - t0}s")
