"""Score calculation and constants module"""

from enum import Enum


class Judgement(str, Enum):
    PERFECT = "perfect"
    PERFECT_EARLY = "perfect early"
    PERFECT_LATE = "perfect late"
    GOOD_EARLY = "good early"
    GOOD_LATE = "good late"
    MEH_EARLY = "meh early"
    MEH_LATE = "meh late"
    BAD_EARLY = "bad early"
    BAD_LATE = "bad late"
    MISS = "MISS"
    OOPS = "OOPS"


JUDGEMENT_SCORES = {
    Judgement.PERFECT: 1000,
    Judgement.PERFECT_EARLY: 900,
    Judgement.PERFECT_LATE: 900,
    Judgement.GOOD_EARLY: 500,
    Judgement.GOOD_LATE: 500,
    Judgement.MEH_EARLY: 200,
    Judgement.MEH_LATE: 200,
    Judgement.BAD_EARLY: 50,
    Judgement.BAD_LATE: 50,
    Judgement.MISS: -100,
    Judgement.OOPS: -50,
}


def calculate_score(judgement: str) -> int:
    """
    Calculate the score for a given judgement.
    Returns the score value based on the JUDGEMENT_SCORES mapping.
    """
    try:
        return JUDGEMENT_SCORES[Judgement(judgement)]
    except ValueError:
        return 0  # Return 0 for unknown judgement types

