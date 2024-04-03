from datetime import datetime

from django.core.management.base import BaseCommand

from banzuke.constants import DIVISIONS
from banzuke.models import Basho, Torikumi
from rikishi.models import Division, Rikishi
from sumoapi.client import SumoApiClient

sumoapi = SumoApiClient()


def save_bouts(bouts, basho):
    for bout in bouts:
        division = Division.objects.get(name=bout["division"])
        east = Rikishi.objects.get(api_id=bout["eastId"])
        west = Rikishi.objects.get(api_id=bout["westId"])
        try:
            winner = Rikishi.objects.get(api_id=bout["winnerId"])
        except Exception:
            continue
        Torikumi.objects.get_or_create(
            basho=basho,
            division=division,
            day=bout["day"],
            east=east,
            west=west,
            winner=winner,
        )


class Command(BaseCommand):
    args = "<start end>"
    help = "Update Torikumi results"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            help="start year",
            type=int,
        )
        parser.add_argument("--end", help="end year", type=int)

    def handle(
        self,
        *args,
        **options,
    ):
        start_year = 1958
        end_year = 2025
        if options["start"]:
            start_year = options["start"]
        if options["end"]:
            end_year = options["end"]

        for year in range(start_year, end_year):
            for month in range(1, 13, 2):
                basho_response = sumoapi.get_basho(year, month)
                if basho_response:
                    start_date = datetime.strptime(
                        basho_response["startDate"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    end_date = datetime.strptime(
                        basho_response["endDate"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    basho = Basho.objects.get_or_create(
                        slug=basho_response["date"],
                        year=year,
                        month=month,
                        start_date=start_date,
                        end_date=end_date,
                    )[0]

                    for day in range(1, 17):
                        for div in DIVISIONS:
                            bouts = sumoapi.get_bouts(year, month, day, div)
                            if bouts:
                                print(
                                    f"saving day {year}-{month:02d}-{day:02d}"
                                )
                                save_bouts(bouts, basho)
