import itertools
import math
from typing import List

from django.db.models import Q

from banzuke.models import Torikumi
from rikishi.models import Rikishi


def get_precomputed_rikishi(rikishi):
    transformed_rating = (rikishi.glicko.rating - 1500) / 173.7178
    transformed_rd = rikishi.glicko.rd / 173.7178
    return transformed_rating, transformed_rd


def glicko_win_prob(precomputed_r1, precomputed_r2):
    rating_1, rd_1 = precomputed_r1
    rating_2, rd_2 = precomputed_r2

    return 1 / (
        1 + math.exp(-1 * math.sqrt(rd_1**2 + rd_2**2) * (rating_1 - rating_2))
    )


def head_to_head_prob(rikishi1: Rikishi, rikishi2: Rikishi) -> float:
    torikumi_query = Q(east=rikishi1, west=rikishi2) | Q(
        east=rikishi2, west=rikishi1
    )

    wins = Torikumi.objects.filter(torikumi_query, winner=rikishi1).count()
    total = Torikumi.objects.filter(torikumi_query).count()

    if total == 0:
        return 0.5

    return wins / total


def get_weighted_prob(
    glicko_win_prob: float, head_to_head_prob: float
) -> float:
    return 0.8 * glicko_win_prob + 0.2 * head_to_head_prob


def get_precomputed_probs(rikishi_list: List[Rikishi]):
    precomputed_r = dict()
    for r in rikishi_list:
        precomputed_r[r.name] = get_precomputed_rikishi(r)

    matchups = list(itertools.combinations(rikishi_list, 2))
    precomputed_probs = dict()
    for matchup in matchups:
        if matchup[0].name not in precomputed_probs:
            precomputed_probs[matchup[0].name] = dict()
        if matchup[1].name not in precomputed_probs:
            precomputed_probs[matchup[1].name] = dict()

        if (
            matchup[1].name not in precomputed_probs[matchup[0].name]
            or matchup[0].name not in precomputed_probs[matchup[1].name]
        ):
            glicko_p1 = glicko_win_prob(
                precomputed_r[matchup[0].name],
                precomputed_r[matchup[1].name],
            )
            h2h_p1 = head_to_head_prob(matchup[0], matchup[1])
            w_p1 = get_weighted_prob(glicko_p1, h2h_p1)
            precomputed_probs[matchup[0].name][matchup[1].name] = w_p1
            precomputed_probs[matchup[1].name][matchup[0].name] = 1 - w_p1

    return precomputed_probs
