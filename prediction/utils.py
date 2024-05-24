import itertools
import math
from collections import defaultdict
from typing import List, Tuple

from django.db.models import Q

from banzuke.models import Torikumi
from glicko.constants import DEFAULT_RATING, GLICKO2_SCALER
from rikishi.models import Rikishi


def get_precomputed_rikishi(rikishi: Rikishi) -> Tuple[float, float]:
    if rikishi is None or rikishi.glicko is None:
        raise ValueError("Invalid Rikishi or Glicko data")

    transformed_rating = (
        rikishi.glicko.rating - DEFAULT_RATING
    ) / GLICKO2_SCALER
    transformed_rd = rikishi.glicko.rd / GLICKO2_SCALER
    return transformed_rating, transformed_rd


def glicko_win_prob(
    precomputed_r1: Tuple[float, float], precomputed_r2: Tuple[float, float]
) -> float:
    rating_1, rd_1 = precomputed_r1
    rating_2, rd_2 = precomputed_r2

    return 1 / (
        1 + math.exp(-1 * math.sqrt(rd_1**2 + rd_2**2) * (rating_1 - rating_2))
    )


def head_to_head_prob(
    rikishi1: Rikishi, rikishi2: Rikishi
) -> Tuple[float, float]:
    torikumi_query = Q(east=rikishi1, west=rikishi2) | Q(
        east=rikishi2, west=rikishi1
    )

    matches = Torikumi.objects.filter(torikumi_query)
    wins = matches.filter(winner=rikishi1).count()
    total = matches.count()

    win_rate = (wins / total) if total != 0 else 0

    head_to_head_weight = math.tanh(total / 15) * 0.5

    return (win_rate, head_to_head_weight)


def get_weighted_prob(
    glicko_win_prob: float,
    head_to_head_prob: float,
    head_to_head_weight: float,
) -> float:
    if (
        not (0 <= glicko_win_prob <= 1)
        or not (0 <= head_to_head_prob <= 1)
        or not (0 <= head_to_head_weight <= 1)
    ):
        raise ValueError("probabilities/weights must be between 0 and 1")

    glicko_weight = 1 - head_to_head_weight

    return (
        glicko_weight * glicko_win_prob
        + head_to_head_weight * head_to_head_prob
    )


def get_precomputed_probs(rikishi_list: List[Rikishi]):
    precomputed_r = dict()
    for r in rikishi_list:
        precomputed_r[r.name] = get_precomputed_rikishi(r)

    matchups = list(itertools.combinations(rikishi_list, 2))
    precomputed_probs = defaultdict(lambda: defaultdict(dict))
    for matchup in matchups:
        if (
            matchup[1].name not in precomputed_probs[matchup[0].name]
            or matchup[0].name not in precomputed_probs[matchup[1].name]
        ):
            glicko_p1 = glicko_win_prob(
                precomputed_r[matchup[0].name],
                precomputed_r[matchup[1].name],
            )
            (h2h_p1, h2h_w) = head_to_head_prob(matchup[0], matchup[1])
            w_p1 = get_weighted_prob(glicko_p1, h2h_p1, h2h_w)
            precomputed_probs[matchup[0].name][matchup[1].name] = w_p1
            precomputed_probs[matchup[1].name][matchup[0].name] = 1 - w_p1

    return precomputed_probs
