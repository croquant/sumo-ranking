import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from banzuke.models import Basho, Torikumi
from rikishi.models import Division, Rikishi
from sumoapi.client import SumoApiClient

sumoapi = SumoApiClient()


class Command(BaseCommand):
    args = "<start end>"
    help = "Update Torikumi results"

    def handle(
        self,
        *args,
        **options,
    ):
        t0 = time.perf_counter()

        all_rikishi = Rikishi.objects.all().only("id", "api_id")
        total = len(all_rikishi)

        divisions = Division.objects.in_bulk(field_name="slug")
        rikishi_in_bulk = all_rikishi.in_bulk(field_name="api_id")
        existing_basho = Basho.objects.in_bulk(field_name="slug")

        for i, rikishi in enumerate(all_rikishi):
            print(f"Saving bouts for Rikishi {rikishi} ({i+1}/{total})")

            bouts = sumoapi.get_bouts_for_rikishi(rikishi.api_id)
            if bouts is None:
                continue

            for bout in bouts:
                basho = self.get_or_create_basho(bout, existing_basho)
                if basho is None:
                    continue

                division = divisions[slugify(bout["division"])]

                try:
                    east = rikishi_in_bulk[bout["eastId"]]
                    west = rikishi_in_bulk[bout["westId"]]
                    winner = rikishi_in_bulk[bout["winnerId"]]
                except Exception:
                    print("! === Failed to process bout", bout)
                    continue

                Torikumi.objects.get_or_create(
                    basho=basho,
                    division=division,
                    day=bout["day"],
                    east=east,
                    west=west,
                    winner=winner,
                )

        t1 = time.perf_counter()
        print(f"Total Time: {t1 - t0}s")

    def get_or_create_basho(self, bout, existing_basho):
        try:
            return existing_basho[bout["bashoId"]]
        except Exception:
            basho_response = sumoapi.get_basho_by_id(bout["bashoId"])
            if basho_response is None:
                return None

            start_date = datetime.strptime(
                basho_response["startDate"], "%Y-%m-%dT%H:%M:%SZ"
            )
            end_date = datetime.strptime(
                basho_response["endDate"], "%Y-%m-%dT%H:%M:%SZ"
            )
            basho = Basho.objects.create(
                slug=basho_response["date"],
                year=int(basho_response["date"][0:4]),
                month=int(basho_response["date"][-2:]),
                start_date=start_date,
                end_date=end_date,
            )
            existing_basho[bout["bashoId"]] = basho
            return basho
