from django.core.management.base import BaseCommand

from banzuke.models import Torikumi


class Command(BaseCommand):
    args = "<start end>"
    help = "Update Torikumi results"

    def handle(
        self,
        *args,
        **options,
    ):
        last_torikumi = Torikumi.objects.select_related("basho").latest(
            "basho__year", "basho__month"
        )
        all_torikumi = Torikumi.objects.filter(
            basho=last_torikumi.basho
        ).select_related(
            "winner",
            "winner__heya",
            "division",
            "east",
            "east__heya",
            "west",
            "west__heya",
        )

        heya_records = dict()

        for torikumi in all_torikumi:
            multiplier = 1 / torikumi.division.level**2

            winner_heya = torikumi.winner.heya
            heya_records.setdefault(winner_heya, {"wins": 0, "total": 0})
            heya_records[winner_heya]["wins"] += 1 * multiplier

            east_heya = torikumi.east.heya
            heya_records.setdefault(east_heya, {"wins": 0, "total": 0})
            heya_records[east_heya]["total"] += 1 * multiplier

            west_heya = torikumi.west.heya
            heya_records.setdefault(west_heya, {"wins": 0, "total": 0})
            heya_records[west_heya]["total"] += 1 * multiplier

        heya_win_percent = [
            (heya, record["wins"] / record["total"])
            for heya, record in heya_records.items()
        ]

        ranking = sorted(heya_win_percent, key=lambda x: x[1], reverse=True)

        print(f"{"HEYA":<12}:\tWIN_PERCENT")
        for r in ranking:
            print(f"{str(r[0]):<12}:\t{r[1]:.2%}")
