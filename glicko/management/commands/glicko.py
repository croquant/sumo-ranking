import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models import Q

from banzuke.models import Basho, Torikumi
from glicko.constants import DEFAULT_RATING, DEFAULT_RD, DEFAULT_VOLATILITY
from glicko.glicko2 import Player
from glicko.models import Glicko, GlickoHistory
from prediction.utils import get_precomputed_rikishi, glicko_win_prob
from rikishi.models import Rikishi


def get_contestants(basho: Basho) -> set[Rikishi]:
    return set(
        [
            t.east
            for t in Torikumi.objects.filter(basho=basho)
            .select_related("east", "east__glicko")
            .distinct()
        ]
        + [
            t.west
            for t in Torikumi.objects.filter(basho=basho)
            .select_related("west", "west__glicko")
            .distinct()
        ]
    )


def get_basho_record(
    rikishi: Rikishi, bouts: list[Torikumi]
) -> tuple[list[float], list[float], list[int]]:
    records = []
    for bout in bouts:
        score = 1 if bout.winner == rikishi else 0
        opponent = bout.west if bout.east == rikishi else bout.east
        records.append((opponent.glicko.rating, opponent.glicko.rd, score))
    return tuple(map(list, zip(*records, strict=False)))


def reset_glicko_data():
    Glicko.objects.all().update(
        rating=DEFAULT_RATING,
        rd=DEFAULT_RD,
        vol=DEFAULT_VOLATILITY,
    )
    GlickoHistory.objects.all().delete()


def process_basho(basho_id, basho_cache):
    basho = basho_cache[basho_id]
    basho_date = datetime.strptime(basho_id, "%Y%m")
    print(f"==========BASHO-{basho_date}==========")

    bouts_cache = list(
        Torikumi.objects.select_related(
            "east",
            "east__glicko",
            "west",
            "west__glicko",
            "winner",
            "winner__glicko",
        ).filter(basho=basho_id)
    )

    contestants = set()
    rikishi_bouts = {}
    for bout in bouts_cache:
        contestants.add(bout.east)
        contestants.add(bout.west)
        rikishi_bouts.setdefault(bout.east, []).append(bout)
        rikishi_bouts.setdefault(bout.west, []).append(bout)

    print(f"Contestants: {len(contestants)}")

    glickos = []
    for rikishi in contestants:
        bouts = rikishi_bouts.get(rikishi, [])

        glicko_player = Player(
            rating=rikishi.glicko.rating,
            rd=rikishi.glicko.rd,
            vol=rikishi.glicko.vol,
        )
        if not bouts:
            glicko_player.did_not_compete()
        else:
            rating_list, rd_list, score_list = get_basho_record(rikishi, bouts)
            glicko_player.update_player(
                rating_list=rating_list,
                rd_list=rd_list,
                outcome_list=score_list,
            )

        glickos.append(
            GlickoHistory(
                glicko=rikishi.glicko,
                basho=basho,
                rating=max(glicko_player.get_rating(), 1),
                rd=glicko_player.get_rd(),
                vol=glicko_player.vol,
            )
        )
    GlickoHistory.objects.bulk_create(glickos)

    # Calculate prediction accuracy for the basho
    basho_prediction_accuracy = calculate_prediction_accuracy(bouts_cache)
    print(
        f"Prediction accuracy for basho {basho.slug}: {basho_prediction_accuracy:.4%}"  # noqa
    )

    update_active_rikishi(basho_date, glickos)

    return basho_prediction_accuracy


def calculate_prediction_accuracy(bouts):
    correct_predictions = 0
    total_bouts = len(bouts)

    for bout in bouts:
        east_rikishi = bout.east
        west_rikishi = bout.west
        winner = bout.winner

        # Get precomputed Glicko ratings
        east_precomputed = get_precomputed_rikishi(east_rikishi)
        west_precomputed = get_precomputed_rikishi(west_rikishi)

        # Calculate win probability for east rikishi
        east_win_prob = glicko_win_prob(east_precomputed, west_precomputed)

        # Predict winner based on higher win probability
        predicted_winner = (
            east_rikishi if east_win_prob > 0.5 else west_rikishi
        )

        # Check if prediction is correct
        if predicted_winner == winner:
            correct_predictions += 1

    # Calculate accuracy percentage
    accuracy = correct_predictions / total_bouts if total_bouts > 0 else 0

    return accuracy


def update_active_rikishi(basho_date, glickos):
    active_rikishi = Rikishi.objects.select_related("glicko").filter(
        Q(intai__isnull=True) | Q(intai__gte=basho_date), debut__lte=basho_date
    )
    print(f"Active: {len(active_rikishi)}")

    glicko_history_dict = {gh.glicko_id: gh for gh in glickos}
    glickos_to_update = []

    for rikishi in active_rikishi:
        glicko = rikishi.glicko
        if glicko_history := glicko_history_dict.get(glicko.rikishi_id):
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
            glicko.rating = max(glicko_player.get_rating(), 1)
            glicko.rd = glicko_player.get_rd()
            glicko.vol = glicko_player.vol
        glickos_to_update.append(glicko)

    Glicko.objects.bulk_update(
        glickos_to_update,
        ["rating", "rd", "vol"],
    )


class Command(BaseCommand):
    def handle(self, *args, **options):
        t0 = time.perf_counter()

        reset_glicko_data()

        basho_list = Torikumi.objects.values_list(
            "basho", flat=True
        ).distinct()

        basho_cache = {
            basho.pk: basho
            for basho in Basho.objects.filter(pk__in=basho_list)
        }

        total_accuracy = 0
        for basho_id in basho_list:
            accuracy = process_basho(basho_id, basho_cache)
            total_accuracy += accuracy

        percentage_accuracy = total_accuracy / len(basho_list)
        print(f"Total accuracy: {percentage_accuracy:.4%}")

        t1 = time.perf_counter()
        print(f"Total Time: {t1 - t0}s")
