import math
import random
from typing import Optional

PENDING = "pending"
IN_PROGRESS = "in_progress"
SUCCESS = "success"
FAILED = "failed"
UNRESPONSIVE = "unresponsive"
ROLLBACK = "rollback"

ROLLOUT_PENDING = "pending"
ROLLOUT_IN_PROGRESS = "in_progress"
ROLLOUT_HALTED = "halted"
ROLLOUT_ROLLED_BACK = "rolled_back"
ROLLOUT_COMPLETED = "completed"

TERMINAL_ROLLOUT_STATUSES = {ROLLOUT_HALTED, ROLLOUT_ROLLED_BACK, ROLLOUT_COMPLETED}


def target_batch_size(total_vehicle_count: int, stage_percent: int) -> int:
    return math.ceil(total_vehicle_count * stage_percent / 100)


def select_new_batch_vehicle_ids(
    all_vehicle_ids: list[str],
    already_assigned_ids: set[str],
    stage_percent: int,
) -> list[str]:
    total = len(all_vehicle_ids)
    target_count = target_batch_size(total, stage_percent)
    remaining_target = max(0, target_count - len(already_assigned_ids))
    candidates = [v for v in all_vehicle_ids if v not in already_assigned_ids]
    return candidates[:remaining_target]


def simulate_outcomes(
    vehicle_ids: list[str],
    success_probability: float,
    failure_probability: float,
    unresponsive_probability: float,
    rng: Optional[random.Random] = None,
) -> dict[str, str]:
    rng = rng or random.Random()
    outcomes: dict[str, str] = {}
    for vehicle_id in vehicle_ids:
        roll = rng.random()
        if roll < success_probability:
            outcomes[vehicle_id] = SUCCESS
        elif roll < success_probability + failure_probability:
            outcomes[vehicle_id] = FAILED
        else:
            outcomes[vehicle_id] = UNRESPONSIVE
    return outcomes


def compute_failure_rate(outcomes: dict[str, str]) -> float:
    if not outcomes:
        return 0.0
    failed = sum(1 for status in outcomes.values() if status == FAILED)
    return failed / len(outcomes)


def should_trigger_rollback(failure_rate: float, failure_threshold_percent: float) -> bool:
    return failure_rate > (failure_threshold_percent / 100)


def is_final_stage(stage_index: int, stages: list[int]) -> bool:
    return stage_index == len(stages) - 1
