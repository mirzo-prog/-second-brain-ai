import datetime
from typing import Tuple

def calculate_sm2(
    grade: int,
    repetitions: int,
    ease_factor: float,
    current_interval: int
) -> Tuple[int, int, float, datetime.datetime]:
    """
    Computes the SuperMemo SM-2 spaced repetition schedule.
    grade: 0-5 (0=blackout, 3=passed with effort, 5=perfect recall)
    Returns: (interval_days, repetitions, ease_factor, next_scheduled_date)
    """
    grade = max(0, min(5, grade))
    
    if grade >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(round(current_interval * ease_factor))
        repetitions += 1
    else:
        repetitions = 0
        interval = 1

    # Update ease factor
    new_ef = ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if new_ef < 1.3:
        new_ef = 1.3

    now = datetime.datetime.now(datetime.timezone.utc)
    next_date = now + datetime.timedelta(days=interval)

    return interval, repetitions, round(new_ef, 2), next_date
